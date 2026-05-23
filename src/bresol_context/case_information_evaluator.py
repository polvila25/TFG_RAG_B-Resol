from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    CaseInformationReport,
    MissingParameter,
)
from src.bresol_context.risk_type import get_risk_config


class CaseInformationEvaluator:
    """
    Deterministically evaluates if the required information for a given risk category
    is present. Computes a minimum information score (0-10) and tracks missing elements.
    """

    def evaluate(self, intake: BresolIntakeAnalysis) -> CaseInformationReport:
        risk_category = intake.risk_category
        taxonomy_info = get_risk_config(risk_category)

        minimum_elements = taxonomy_info.get("minimum_elements", [])
        
        # Determine missing vs completed
        completed_parameters = []
        missing_parameters = []

        llm_missing = [m.lower() for m in intake.missing_information]
        
        # Pull question lists from the single source of truth in risk_type.py
        missing_info_qs = taxonomy_info.get("missing_info_questions", [])
        safe_id_qs = taxonomy_info.get("safe_identification_questions", [])

        for idx, element in enumerate(minimum_elements):
            is_missing = False
            
            # 1. Direct check from LLM-identified missing keys
            if element in intake.missing_minimum_elements:
                is_missing = True
            # 2. Strict check for victim
            elif "victima" in element or "afectat" in element:
                is_missing = not intake.victim_identified
            else:
                # 3. Check against general free-text missing information list
                element_clean = element.replace("_", " ")
                for missing_str in llm_missing:
                    if element_clean in missing_str or missing_str in element_clean:
                        is_missing = True
                        break
                
                # 4. Strict length fallback: queries under 12 words with generic statements
                # lack sufficient detail to prove intent, repetition, or power imbalance.
                # This strict validation only applies if the alert is explicitly anonymous.
                if intake.reporting_mode == "anonymous" and len(intake.original_query.split()) < 12:
                    query_lower = intake.original_query.lower()
                    if element == "repeticio_temporal" and not any(w in query_lower for w in ["sempre", "repetit", "cada dia", "fa temps", "mesos", "setmanes", "diari", "habitual"]):
                        is_missing = True
                    elif element == "desequilibri_poder" and not any(w in query_lower for w in ["grup", "més fort", "més gran", "popular", "superior", "abús", "abus", "amenaça", "intimid"]):
                        is_missing = True
                    elif element == "intencionalitat" and not any(w in query_lower for w in ["volen", "vol", "adrede", "a propòsit", "intencionat", "per fer mal"]):
                        is_missing = True

            if is_missing:
                # Dynamically retrieve matching questions from the config
                q_context = "Ens podries orientar amb més detalls sobre aquesta situació?"
                if "victima" in element or "afectat" in element:
                    if safe_id_qs:
                        q_context = safe_id_qs[0]
                else:
                    # Distribute general missing questions matching index or fallback
                    q_idx = idx % len(missing_info_qs) if missing_info_qs else 0
                    if missing_info_qs:
                        q_context = missing_info_qs[q_idx]

                missing_parameters.append(
                    MissingParameter(
                        parameter_name=element,
                        parameter_label=element.replace("_", " ").capitalize(),
                        importance="high" if ("victima" in element or "risc" in element) else "medium",
                        question_context=q_context
                    )
                )
            else:
                completed_parameters.append(element)

        # Force safe_identification if victim is not identified
        has_safe_id = any(mp.parameter_name == "safe_identification" or "victima" in mp.parameter_name for mp in missing_parameters)
        if not intake.victim_identified and not has_safe_id:
            q_context = safe_id_qs[0] if safe_id_qs else "Ens podries orientar sobre quin curs o edat aproximada té l'alumne/a?"
            missing_parameters.append(
                MissingParameter(
                    parameter_name="safe_identification",
                    parameter_label="Identificació segura",
                    importance="high",
                    question_context=q_context
                )
            )

        # Calculate Minimum Information Score (0 - 10)
        score = self._calculate_score(
            intake, 
            completed_elements_count=len(completed_parameters), 
            total_elements_count=len(minimum_elements)
        )

        all_met = len(missing_parameters) == 0

        return CaseInformationReport(
            completed_parameters=completed_parameters,
            missing_parameters=missing_parameters,
            minimum_information_score=score,
            all_minimum_elements_met=all_met,
        )

    def _calculate_score(
        self, 
        intake: BresolIntakeAnalysis, 
        completed_elements_count: int, 
        total_elements_count: int
    ) -> float:
        score = 0.0
        
        # 1. Base score from completing minimum elements (up to 5 points)
        if total_elements_count > 0:
            ratio = completed_elements_count / total_elements_count
            score += ratio * 5.0
            
        # 2. Base score from detected indicators (up to 2 points)
        score += min(len(intake.detected_indicators), 2) * 1.0
        
        # 3. Victim identified adds solid actionable context (up to 2 points)
        if intake.victim_identified:
            score += 2.0
            
        # 4. Valid risk category identified (not unknown/general) adds clarity (up to 1 point)
        if intake.risk_category not in ["unknown", "general"]:
            score += 1.0
            
        # Ensure it doesn't exceed 10
        final_score = round(min(score, 10.0), 1)
        return final_score
