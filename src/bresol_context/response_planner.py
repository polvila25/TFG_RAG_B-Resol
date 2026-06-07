from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    CaseInformationReport,
    ResponsePlan,
    ResponseType,
)
from src.rag.schemas import QueryAnalysis


class ResponsePlanner:
    """
    Deterministic router that outputs the final ResponsePlan.
    Evaluates urgency, the minimum_information_score, and the query analysis intent.
    """

    def plan(
        self,
        intake: BresolIntakeAnalysis,
        report: CaseInformationReport,
        query_analysis: QueryAnalysis,
        is_out_of_scope: bool = False,
    ) -> ResponsePlan:

        # 1. CONTROL DE CONTEXTO (FUERA DE DOMINIO - PRIORIDAD 1)
        out_of_scope = is_out_of_scope or getattr(query_analysis, "is_out_of_scope", False)
        if out_of_scope:
            return ResponsePlan(
                response_type="out_of_scope",
                should_run_documental_rag=False,
                rag_instructions="Consulta fora de domini. Rebutjar amb fermesa."
            )

        # 2. RIESGO VITAL URGENTE (PRIORIDAD 2)
        if intake.requires_urgent_review:
            return ResponsePlan(
                response_type="urgent_protection",
                should_run_documental_rag=True, # RAG executes to get immediate protection measures
                urgent_actions=[
                    "1. Garantir la seguretat física i emocional immediata de l'alumne/a.",
                    "2. Comunicar immediatament a la direcció del centre.",
                    "3. No deixar l'alumne/a sol en cap moment (especialment en risc de suïcidi o autolesions)."
                ],
                rag_instructions="Prioritzar extremadament les mesures d'urgència i protecció física immediata sobre qualsevol altra qüestió."
            )

        # 3. ALERTA ANÓNIMA (PRIORIDAD 3)
        if intake.reporting_mode == "anonymous":
            score = report.minimum_information_score
            if score < 5:
                return ResponsePlan(
                    response_type="safe_identification_guidance",
                    should_run_documental_rag=True,
                    rag_instructions="Alerta explícitament anònima incompleta (score < 5). Orientació a la indagació psicopedagògica i identificació segura."
                )
            else: # score >= 5
                return ResponsePlan(
                    response_type="anonymous_protocol",
                    should_run_documental_rag=True,
                    rag_instructions="Alerta explícitament anònima completa (score >= 5). Protocol d'actuació protegint la identitat de l'emissor."
                )

        # 4. ALERTA NO ANÓNIMA (PRIORIDAD 4)
        score = report.minimum_information_score

        # A) Capa de Ley
        if query_analysis.query_type == "legal_support":
            return ResponsePlan(
                response_type="legal_support",
                should_run_documental_rag=True,
                rag_instructions="Centrar-se exclusivament en l'exposició normativa i legal."
            )

        # B) Capa Mixta
        elif query_analysis.query_type == "mixed":
            return ResponsePlan(
                response_type="mixed_response",
                should_run_documental_rag=True,
                rag_instructions="Combinar orientació pràctica d'aplicació amb fonament legal clar."
            )

        # C) Capa de Protocolo
        else:
            if score <= 3 or getattr(query_analysis, "urgency_level", "unknown") == "ambiguous":
                return ResponsePlan(
                    response_type="collect_minimum_information",
                    should_run_documental_rag=True,
                    rag_instructions="La informació és insuficient (score <= 3) o ambigua. Executar RAG per a orientació preliminar preventiva."
                )
            elif 3 < score < 6:
                return ResponsePlan(
                    response_type="protocol_with_missing_info",
                    should_run_documental_rag=True,
                    rag_instructions="Ambigüitat parcial (3 < score < 6). Executar RAG i incloure guia d'informació restant a confirmar."
                )
            else: # score >= 6
                return ResponsePlan(
                    response_type="protocol_response",
                    should_run_documental_rag=True,
                    rag_instructions="Cas complet (score >= 6). Executar RAG i retornar el protocol de manera directa, neta i executiva."
                )
