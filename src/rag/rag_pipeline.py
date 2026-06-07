import os
import time
from typing import Optional, List, Dict, Any

from src.bresol_context.bresol_intake_analyzer import BresolIntakeAnalyzer
from src.bresol_context.case_information_evaluator import CaseInformationEvaluator
from src.bresol_context.teacher_guidance_builder import TeacherGuidanceBuilder
from src.bresol_context.response_planner import ResponsePlanner

from src.rag.query_analizer import QueryAnalyzer, QueryAnalysis
from src.rag.query_enricher import enrich_query, EnrichedQuery
from src.rag.retriever import QdrantRetriever, RetrievedChunk
from src.rag.reranker import CrossEncoderReranker, RerankedChunk
from src.rag.context_builder import ContextBuilder
from src.rag.prompt_builder import get_prompt
from src.rag.generator import LLMGenerator


def _format_list(items: List[str]) -> str:
    if not items:
        return "Cap dada rellevant especificada."
    return "\n".join(f"- {item}" for item in items)


class AdvancedRAGPipeline:
    """
    Pipeline RAG Avançat amb Triage Intel·ligent B-Resol.
    """
    def __init__(self, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"):
        print("[INIT] Inicialitzant el Sistema Triage B-Resol...")
        self.intake_analyzer = BresolIntakeAnalyzer(gemini_api_key=gemini_api_key)
        self.evaluator = CaseInformationEvaluator()
        self.guidance_builder = TeacherGuidanceBuilder()
        self.planner = ResponsePlanner()

        print("[INIT] Inicialitzant Query Analyzer...")
        self.query_analyzer = QueryAnalyzer(gemini_api_key=gemini_api_key)
        
        # Lazy loading placeholders per evitar bloqueig de base de dades local i estalviar memòria
        self.retriever = None
        self.reranker = None
        self.context_builder = ContextBuilder()
        
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        print("[INIT] Pipeline apunt.\n")

    def _retrieve_and_rerank(
        self, 
        enriched_query: str, 
        original_query: str,
        retrieval_layer: str, 
        risk_category: str, 
        top_k: int, 
        top_n: int
    ) -> List[RerankedChunk]:
        # Lazy initialization
        if self.retriever is None:
            print("      [LAZY] Inicialitzant Qdrant Retriever...")
            self.retriever = QdrantRetriever()
        if self.reranker is None:
            print("      [LAZY] Inicialitzant CrossEncoder Reranker...")
            self.reranker = CrossEncoderReranker()

        t0 = time.time()
        retrieved_chunks = self.retriever.retrieve(
            query=enriched_query,
            retrieval_layer=retrieval_layer if retrieval_layer != "unknown" else None,
            risk_category=risk_category if risk_category != "unknown" else None,
            top_k=top_k
        )
        t_retrieve = time.time() - t0
        
        t1 = time.time()
        reranked_chunks = self.reranker.rerank(
            query=original_query,
            chunks=retrieved_chunks,
            top_n=top_n
        )
        t_rerank = time.time() - t1
        
        print(f"      [Time] Retrieve: {t_retrieve:.3f}s | Rerank: {t_rerank:.3f}s")
        return reranked_chunks

    def run(self, user_query: str, reporting_mode: str = "identified", student_metadata: dict = None) -> Dict[str, Any]:
        print("="*60)
        print("INICIANT PIPELINE RAG + TRIAJE")
        print("="*60)
        
        t_total_start = time.time()
        
        # 1. Bresol Intake & Evaluation
        print("[1/6] Analitzant consulta amb Bresol Intake...")
        bresol_analysis = self.intake_analyzer.analyze(user_query, reporting_mode)
        case_report = self.evaluator.evaluate(bresol_analysis)
        
        print(f"      - Risc: {bresol_analysis.risk_category} | Score Info: {case_report.minimum_information_score}/10")
        
        # 2. Query Intent Analysis
        print("[2/6] Analitzant intencionalitat (QueryAnalyzer)...")
        query_analysis = self.query_analyzer.analyze(user_query)
        
        # 3. Response Planning (Routing)
        print("[3/6] Planificant ruta de resposta...")
        response_plan = self.planner.plan(
            bresol_analysis,
            case_report,
            query_analysis,
            is_out_of_scope=query_analysis.is_out_of_scope
        )
        print(f"      - Tipus Resposta: {response_plan.response_type} | RAG Actiu: {response_plan.should_run_documental_rag}")
        
        # 4. Building Teacher Guidance (CNV, Empathy, Limits)
        teacher_guidance = self.guidance_builder.build(bresol_analysis, case_report)
        
        # 5. Conditional Document Retrieval (RAG)
        final_chunks = []
        context = "No s'ha realitzat cerca documental per falta d'informació mínima."
        enriched = None
        
        if response_plan.should_run_documental_rag:
            print("\n[4/6] Recuperació RAG Activa...")
            enriched = enrich_query(user_query, query_analysis, bresol_analysis)
            
            # Simple routing based on query_type
            if query_analysis.query_type == "legal_support":
                final_chunks = self._retrieve_and_rerank(
                    enriched.search_query, user_query, "legal_support", query_analysis.risk_category, 10, 4)
            elif query_analysis.query_type == "mixed":
                app_chunks = self._retrieve_and_rerank(
                    enriched.search_query, user_query, "application", query_analysis.risk_category, 12, 4)
                leg_chunks = self._retrieve_and_rerank(
                    enriched.search_query, user_query, "legal_support", query_analysis.risk_category, 8, 2)
                final_chunks = app_chunks + leg_chunks
            else:
                final_chunks = self._retrieve_and_rerank(
                    enriched.search_query, user_query, "application", query_analysis.risk_category, 15, 5)
            
            context = self.context_builder.build(final_chunks)
        else:
            print("\n[4/6] Recuperació RAG Omesa (Planificador).")
 
        # 6. LLM Generation
        print("[5/6] Generant resposta amb Prompt Dinàmic...")
        dynamic_prompt = get_prompt(
            response_type=response_plan.response_type,
            risk_category=bresol_analysis.risk_category,
            reporting_mode=bresol_analysis.reporting_mode,
            info_score=case_report.minimum_information_score,
            query_type=query_analysis.query_type,
            is_out_of_scope=query_analysis.is_out_of_scope,
            requires_urgent_review=bresol_analysis.requires_urgent_review,
            student_metadata=student_metadata,
        )
        generator = LLMGenerator(self.gemini_api_key, self.gemini_model, dynamic_prompt)
        
        variables = {
            "user_query": user_query,
            "answer_context": context,
            "query_type": query_analysis.query_type,
            "risk_category": bresol_analysis.risk_category,
            "bresol_detected_indicators": _format_list(bresol_analysis.detected_indicators),
            "empathy_statement": teacher_guidance.empathy_statement,
            "opening_phrases": teacher_guidance.empathy_statement,
            "tone_recommendation": teacher_guidance.empathy_statement,
            "recommended_questions": _format_list(teacher_guidance.recommended_questions),
            "avoid_questions": _format_list(teacher_guidance.avoid_questions),
            "urgent_actions": _format_list(response_plan.urgent_actions),
            "safety_notes": _format_list(response_plan.urgent_actions) if response_plan.urgent_actions else "No s'han especificat indicacions especials de seguretat.",
            "missing_information": _format_list(bresol_analysis.missing_information) if bresol_analysis.missing_information else _format_list([m.replace("_", " ").capitalize() for m in bresol_analysis.missing_minimum_elements]),
            "reporting_mode": bresol_analysis.reporting_mode,
            "victim_identified": "Sí" if bresol_analysis.victim_identified else "No",
            "identification_status": "Anònim" if bresol_analysis.reporting_mode == "anonymous" else ("Identificat" if bresol_analysis.reporting_mode == "identified" else "Desconegut"),
            "urgency_level": query_analysis.urgency_level,
            "has_implicated_parties": "Sí" if query_analysis.has_implicated_parties else "No",
            "detected_features": ", ".join(query_analysis.detected_features) if query_analysis.detected_features else "Cap característica específica detectada.",
        }
        
        # Filtrem les variables perquè només s'enviïn les que el prompt específic requereix
        filtered_variables = {
            k: v for k, v in variables.items() 
            if k in dynamic_prompt.input_variables
        }
        
        answer = generator.generate(filtered_variables)
        
        t_total = time.time() - t_total_start
        print(f"PIPELINE FINALITZAT en {t_total:.3f}s")
        print("="*60)
        
        return {
            "answer": answer,
            "analysis": query_analysis,
            "bresol_intake": bresol_analysis,
            "case_report": case_report,
            "teacher_guidance": teacher_guidance,
            "response_plan": response_plan,
            "enriched_query": enriched,
            "chunks": final_chunks,
            "context": context,
        }
