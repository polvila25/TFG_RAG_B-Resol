import os
import time
from typing import Optional, List, Dict, Any

from src.rag.query_analizer import QueryAnalyzer, QueryAnalysis
from src.rag.query_enricher import enrich_query, EnrichedQuery
from src.rag.retriever import QdrantRetriever, RetrievedChunk
from src.rag.reranker import CrossEncoderReranker, RerankedChunk
from src.rag.context_builder import ContextBuilder
from src.rag.prompt_builder import get_prompt
from src.rag.generator import LLMGenerator

class AdvancedRAGPipeline:
    """
    Pipeline RAG avanzado que implementa la orquestación completa:
    Query -> Analyzer -> Enricher -> Retriever -> Reranker -> Context Builder -> LLM
    """
    def __init__(self, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"):
        print("[INIT] Inicializando Query Analyzer...")
        self.analyzer = QueryAnalyzer(gemini_api_key=gemini_api_key)
        
        print("[INIT] Inicializando Retriever (Qdrant)...")
        self.retriever = QdrantRetriever()
        
        print("[INIT] Inicializando Reranker (CrossEncoder)...")
        self.reranker = CrossEncoderReranker()
        
        print("[INIT] Inicializando LLM Generator...")
        self.prompt_template = get_prompt()
        self.generator = LLMGenerator(gemini_api_key, gemini_model, self.prompt_template)
        print("[INIT] Pipeline listo.\n")

    def _retrieve_and_rerank(
        self, 
        enriched_query: str, 
        original_query: str,
        retrieval_layer: str, 
        risk_category: str, 
        top_k: int, 
        top_n: int
    ) -> List[RerankedChunk]:
        """Helper para hacer retrieve y rerank de un layer específico."""
        
        t0 = time.time()
        # 1. Recuperar candidatos amplios de la base de datos
        retrieved_chunks = self.retriever.retrieve(
            query=enriched_query,
            retrieval_layer=retrieval_layer if retrieval_layer != "unknown" else None,
            risk_category=risk_category if risk_category != "unknown" else None,
            top_k=top_k
        )
        t_retrieve = time.time() - t0
        
        t1 = time.time()
        # 2. Reordenar los candidatos usando un modelo más potente (CrossEncoder)
        reranked_chunks = self.reranker.rerank(
            query=original_query, # El reranker funciona mejor comparando con la consulta natural
            chunks=retrieved_chunks,
            top_n=top_n
        )
        t_rerank = time.time() - t1
        
        print(f"      [Time] Retrieve: {t_retrieve:.3f}s | Rerank: {t_rerank:.3f}s")
        
        return reranked_chunks

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo.
        Devuelve un diccionario con el resultado y metadatos del proceso.
        """
        print("="*60)
        print("INICIANDO PIPELINE RAG")
        print("="*60)
        print(f"Pregunta original: '{user_query}'\n")
        
        t_total_start = time.time()
        
        # 1. Query Analyzer
        print("[1/6] Analizando consulta...")
        t0 = time.time()
        analysis: QueryAnalysis = self.analyzer.analyze(user_query)
        t_analyzer = time.time() - t0
        print(f"      - Tipo detectado: {analysis.query_type}")
        print(f"      - Categoría de riesgo: {analysis.risk_category}")
        print(f"      - Nivel de seguridad: {analysis.safety_level}")
        print(f"      [Time] {t_analyzer:.3f}s")

        # 2. Query Enricher
        print("\n[2/6] Enriqueciendo consulta...")
        t0 = time.time()
        enriched: EnrichedQuery = enrich_query(user_query, analysis)
        t_enricher = time.time() - t0
        print(f"      - Query de búsqueda: {enriched.search_query}")
        print(f"      - Términos de expansión: {', '.join(enriched.expansion_terms[:5])}...")
        print(f"      [Time] {t_enricher:.3f}s")

        # 3 & 4. Retriever & Reranker (Lógica de negocio por tipo de consulta)
        print("\n[3-4/6] Recuperación y Reranking...")
        t0 = time.time()
        final_chunks: List[RerankedChunk] = []
        
        q_type = analysis.query_type
        
        if q_type == "application":
            print("      - Flujo: Application (Protocolos prácticos)")
            final_chunks = self._retrieve_and_rerank(
                enriched_query=enriched.search_query,
                original_query=user_query,
                retrieval_layer="application",
                risk_category=analysis.risk_category,
                top_k=15,
                top_n=5
            )
            
        elif q_type == "legal_support":
            print("      - Flujo: Legal Support (Normativa)")
            final_chunks = self._retrieve_and_rerank(
                enriched_query=enriched.search_query,
                original_query=user_query,
                retrieval_layer="legal_support",
                risk_category=analysis.risk_category,
                top_k=10,
                top_n=4
            )
            
        elif q_type == "mixed":
            print("      - Flujo: Mixto (Application + Legal Support)")
            print("         - Buscando parte práctica...")
            app_chunks = self._retrieve_and_rerank(
                enriched_query=enriched.search_query,
                original_query=user_query,
                retrieval_layer="application",
                risk_category=analysis.risk_category,
                top_k=12,
                top_n=4
            )
            print("         - Buscando parte legal...")
            legal_chunks = self._retrieve_and_rerank(
                enriched_query=enriched.search_query,
                original_query=user_query,
                retrieval_layer="legal_support",
                risk_category=analysis.risk_category,
                top_k=8,
                top_n=2
            )
            # Combinar manteniendo un orden lógico (primero protocolos, luego leyes)
            final_chunks = app_chunks + legal_chunks
            
        else:
            print("      - Flujo: General (Unknown)")
            final_chunks = self._retrieve_and_rerank(
                enriched_query=enriched.search_query,
                original_query=user_query,
                retrieval_layer="unknown",
                risk_category=analysis.risk_category,
                top_k=12,
                top_n=5
            )
        t_retrieval_rerank = time.time() - t0

        print(f"      - Total chunks finales retenidos: {len(final_chunks)}")
        print(f"      [Time] {t_retrieval_rerank:.3f}s")

        # 5. Context Builder
        print("\n[5/6] Construyendo contexto estructurado...")
        t0 = time.time()
        context = ContextBuilder.build(final_chunks)
        t_context = time.time() - t0
        print(f"      [Time] {t_context:.3f}s")

        # 6. LLM Generation
        print("[6/6] Generando respuesta con IA...")
        t0 = time.time()
        answer = self.generator.generate(user_query, context)
        t_gen = time.time() - t0
        print(f"      [Time] {t_gen:.3f}s")

        t_total = time.time() - t_total_start
        print("="*60)
        print(f"PIPELINE FINALIZADO en {t_total:.3f}s")
        print("="*60)
        
        return {
            "answer": answer,
            "analysis": analysis,
            "enriched_query": enriched,
            "chunks": final_chunks,
            "context": context,
            "timings": {
                "analyzer": t_analyzer,
                "enricher": t_enricher,
                "retrieval_rerank": t_retrieval_rerank,
                "context_builder": t_context,
                "generator": t_gen,
                "total": t_total
            }
        }
