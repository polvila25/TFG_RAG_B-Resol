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
            completed_parameters=completed_parameters, 
            minimum_elements=minimum_elements
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
        completed_parameters: list[str], 
        minimum_elements: list[str]
    ) -> float:
        score = 0.0
        
        # 1. Puntuació ponderada per elements mínims (Fins a 5.0 punts)
        # Els elements crítics pesen més que els secundaris
        critical_keywords = ["victima", "afectat", "repeticio", "agressiva", "sexual", "suicida", "violencia", "assetjament", "maltractament", "risc"]
        
        total_weight = 0.0
        earned_weight = 0.0
        
        for element in minimum_elements:
            weight = 1.5 if any(kw in element.lower() for kw in critical_keywords) else 0.7
            total_weight += weight
            if element in completed_parameters:
                earned_weight += weight
                
        if total_weight > 0:
            ratio = earned_weight / total_weight
            score += ratio * 5.0
            
        # 2. Indicadors detectats (Fins a 2.0 punts)
        score += min(len(intake.detected_indicators), 2) * 1.0
        
        # 3. Víctima identificada (Reduït de 2.0 a 1.0 per evitar penalitzar en excés alertes anònimes)
        if intake.victim_identified:
            score += 1.0
            
        # 4. Bonus de context espai-temporal (Fins a 1.0 punt)
        query_lower = intake.original_query.lower()
        
        # Bonus Temporal
        temporal_keywords = ["ahir", "avui", "demà", "dema", "dies", "setmanes", "mesos", "sempre", "repetit", "vegades", "curs", "dilluns", "dimarts", "dimecres", "dijous", "divendres", "hora", "mati", "tarda", "pati"]
        print(f'Elements temporals extrets: {intake.temporal_context_elements}')
        
        if intake.temporal_context_elements:
            score += 0.5
        elif any(kw in query_lower for kw in temporal_keywords):
            score += 0.5
            
        # Bonus Espacial
        spatial_keywords = ["pati", "classe", "aula", "passadis", "menjador", "gimnas", "escola", "institut", "xarxes", "whatsapp", "instagram", "tiktok", "carrer", "sortida", "lavabo"]
        print(f'Elements espacials extrets: {intake.spatial_context_elements}')
        if intake.spatial_context_elements:
            score += 0.5
        elif any(kw in query_lower for kw in spatial_keywords):
            score += 0.5

        # 5. Categoria de risc vàlida (Fins a 1.0 punt)
        if intake.risk_category not in ["unknown", "general"]:
            score += 1.0
            
        # 6. Penalització per consultes extremadament curtes (menys de 10 paraules)
        words = intake.original_query.split()
        if len(words) < 10:
            # Penalització lineal: 1 paraula = -2.0, 9 paraules = -0.2
            penalty = 2.0 * (10 - len(words)) / 10
            score -= penalty
            
        # Assegurar que la puntuació final estigui entre 0.0 i 10.0
        final_score = round(max(0.0, min(score, 10.0)), 1)
        return final_score
