from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    CaseInformationReport,
    ResponsePlan,
    ResponseType,
)
from src.rag.schemas import QueryAnalysis


class ResponsePlanner:
    """
    Enrutador determinista que retorna el ResponsePlan final.
    Avalua la urgència, la puntuació d'informació mínima i la intenció de la consulta.
    """

    def plan(
        self,
        intake: BresolIntakeAnalysis,
        report: CaseInformationReport,
        query_analysis: QueryAnalysis,
        is_out_of_scope: bool = False,
    ) -> ResponsePlan:

        # 1. CONTROL DE CONTEXT (FORA DE DOMINI - PRIORITAT 1)
        out_of_scope = is_out_of_scope or getattr(query_analysis, "is_out_of_scope", False)
        if out_of_scope:
            return ResponsePlan(
                response_type="out_of_scope",
                should_run_documental_rag=False,
                rag_instructions="Consulta fora de domini. Rebutjar amb fermesa."
            )

        # 2. RISC VITAL URGENT (PRIORITAT 2)
        if intake.requires_urgent_review:
            return ResponsePlan(
                response_type="urgent_protection",
                should_run_documental_rag=True, # RAG s'executa per obtenir mesures de protecció immediates
                urgent_actions=[
                    "1. Garantir la seguretat física i emocional immediata de l'alumne/a.",
                    "2. Comunicar immediatament a la direcció del centre.",
                    "3. No deixar l'alumne/a sol en cap moment (especialment en risc de suïcidi o autolesions)."
                ],
                rag_instructions="Prioritzar extremadament les mesures d'urgència i protecció física immediata sobre qualsevol altra qüestió."
            )

        # 3. ALERTA ANÒNIMA (PRIORITAT 3)
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

        # 4. ALERTA NO ANÒNIMA (PRIORITAT 4)
        score = report.minimum_information_score

        # A) Capa Legal
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

        # C) Capa de Protocol
        else:
            if score <= 4:
                return ResponsePlan(
                    response_type="collect_minimum_information",
                    should_run_documental_rag=True,
                    rag_instructions="La informació és insuficient (score <= 4). Executar RAG per a orientació preliminar preventiva."
                )
            elif 4 < score < 8:
                return ResponsePlan(
                    response_type="protocol_with_missing_info",
                    should_run_documental_rag=True,
                    rag_instructions="Ambigüitat parcial (4 < score < 8). Executar RAG i incloure guia d'informació restant a confirmar."
                )
            else: # score >= 8
                return ResponsePlan(
                    response_type="protocol_response",
                    should_run_documental_rag=True,
                    rag_instructions="Cas complet (score >= 8). Executar RAG i retornar el protocol de manera directa, neta i executiva."
                )
