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
    ) -> ResponsePlan:

        # 1. Evaluate Legal / Mixed overrides
        if query_analysis.query_type == "legal_support":
            return ResponsePlan(
                response_type="legal_support",
                should_run_documental_rag=True,
                rag_instructions="Centrar-se exclusivament en l'exposició normativa i legal."
            )
            
        if query_analysis.query_type == "mixed":
            return ResponsePlan(
                response_type="mixed_response",
                should_run_documental_rag=True,
                rag_instructions="Combinar orientació pràctica d'aplicació amb fonament legal clar."
            )

        # 2. Evaluate Urgent Override
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

        # 3. Score-based routing (0 - 10)
        score = report.minimum_information_score

        if score <= 3:
            # Too little information to run RAG reliably
            return ResponsePlan(
                response_type="collect_minimum_information",
                should_run_documental_rag=False,
                rag_instructions="Recopilar la informació mínima essencial sense abrumar."
            )
            
        elif 4 <= score <= 6:
            # Partial information. We can conditionally run RAG.
            # If the victim is missing, guide for safe identification
            has_safe_id = any(mp.parameter_name == "safe_identification" for mp in report.missing_parameters)
            
            if has_safe_id:
                return ResponsePlan(
                    response_type="safe_identification_guidance",
                    should_run_documental_rag=True, # Partial minimums detected -> conditionally execute RAG
                    rag_instructions="Oferir orientació protocol·lària base, remarcant la necessitat d'identificar de forma segura l'afectat."
                )
            else:
                return ResponsePlan(
                    response_type="protocol_with_missing_info",
                    should_run_documental_rag=True,
                    rag_instructions="Orientar en el protocol assumint que hi ha elements a confirmar. Evitar asseveracions absolutes."
                )
                
        else:
            # Score 7 - 10: Robust context
            return ResponsePlan(
                response_type="protocol_response",
                should_run_documental_rag=True,
                rag_instructions="Exposar clarament el circuit o protocol d'actuació complet atès el bon context."
            )
