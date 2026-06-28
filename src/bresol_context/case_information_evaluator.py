from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    CaseInformationReport,
    MissingParameter,
)
from src.bresol_context.risk_type import get_risk_config


class CaseInformationEvaluator:
    """
    Avalua de forma determinista si la informació requerida per a una categoria
    de risc està present. Calcula una puntuació (0-10) i els elements faltants.
    """

    def evaluate(self, intake: BresolIntakeAnalysis) -> CaseInformationReport:
        risk_category = intake.risk_category
        taxonomy_info = get_risk_config(risk_category)

        minimum_elements = taxonomy_info.get("minimum_elements", [])
        
        # Determinar elements completats i faltants
        completed_parameters = []
        missing_parameters = []

        llm_missing = [m.lower() for m in intake.missing_information]
        
        # Obtenir llistes de preguntes des de risk_type.py
        missing_info_qs = taxonomy_info.get("missing_info_questions", [])
        safe_id_qs = taxonomy_info.get("safe_identification_questions", [])

        query_lower = intake.original_query.lower()
        word_count = len(intake.original_query.split())

        for idx, element in enumerate(minimum_elements):
            is_missing = False
            
            # 1. Comprovació directa de les claus identificades per l'LLM
            if element in intake.missing_minimum_elements:
                is_missing = True
            # 2. Comprovació estricta de la víctima
            elif "victima" in element or "afectat" in element:
                is_missing = not intake.victim_identified
            else:
                # 3. Comprovació contra la llista general d'informació faltant
                element_clean = element.replace("_", " ")
                for missing_str in llm_missing:
                    if element_clean in missing_str or missing_str in element_clean:
                        is_missing = True
                        break
                
                # 4. Comprovació estricta d'evidència textual. Les consultes 
                # curtes manquen de detall suficient per provar intencionalitat.
                if word_count < 20:
                    if element == "repeticio_temporal" and not any(w in query_lower for w in ["sempre", "repetit", "cada dia", "fa temps", "mesos", "setmanes", "diari", "habitual", "continuament", "sovint", "constantment"]):
                        is_missing = True
                    elif element == "desequilibri_poder" and not any(w in query_lower for w in ["grup", "més fort", "més gran", "popular", "superior", "abús", "abus", "amenaça", "intimid", "banda", "sol contra", "tots contra"]):
                        is_missing = True
                    elif element == "intencionalitat" and not any(w in query_lower for w in ["volen", "vol", "adrede", "a propòsit", "intencionat", "per fer mal", "expressament", "deliberat"]):
                        is_missing = True
                    elif element == "repeticio_o_persistencia" and not any(w in query_lower for w in ["sempre", "repetit", "cada dia", "persistent", "continua", "no para", "constantment", "sovint"]):
                        is_missing = True

            if is_missing:
                # Recuperar dinàmicament les preguntes coincidents de la configuració
                q_context = "Ens podries orientar amb més detalls sobre aquesta situació?"
                if "victima" in element or "afectat" in element:
                    if safe_id_qs:
                        q_context = safe_id_qs[0]
                else:
                    # Distribuir preguntes generals coincidents o per defecte
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

        # Forçar identificació segura si la víctima no està identificada
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

        # Calcular Puntuació Mínima d'Informació (0 - 10)
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
        
        # 1. Puntuació ponderada per elements mínims (Fins a 6.0 punts)
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
            score += ratio * 6.0
            
        # 2. Indicadors detectats (Fins a 1.0 punt, reduït de 2.0)
        score += min(len(intake.detected_indicators), 2) * 0.5
        
        # 3. Víctima identificada (0.5 punts, reduït de 1.0)
        if intake.victim_identified:
            score += 0.5
            
        # 3b. Agressor identificat (0.5 punts)
        if intake.aggressor_identified:
            score += 0.5
            
        # 4. Bonus de context espai-temporal (Fins a 0.5 punts, reduït de 1.0)
        query_lower = intake.original_query.lower()
        
        # Bonus Temporal (0.25 punts)
        temporal_keywords = ["ahir", "avui", "demà", "dema", "dies", "setmanes", "mesos", "sempre", "repetit", "vegades", "curs", "dilluns", "dimarts", "dimecres", "dijous", "divendres", "hora", "mati", "tarda"]
        print(f'Elements temporals extrets: {intake.temporal_context_elements}')
        
        if intake.temporal_context_elements:
            score += 0.25
        elif any(kw in query_lower for kw in temporal_keywords):
            score += 0.25
            
        # Bonus Espacial (0.25 punts)
        spatial_keywords = ["pati", "classe", "aula", "passadis", "menjador", "gimnas", "escola", "institut", "xarxes", "whatsapp", "instagram", "tiktok", "carrer", "sortida", "lavabo"]
        print(f'Elements espacials extrets: {intake.spatial_context_elements}')
        if intake.spatial_context_elements:
            score += 0.25
        elif any(kw in query_lower for kw in spatial_keywords):
            score += 0.25

        # 5. Categoria de risc vàlida (0.5 punts, reduït de 1.0)
        if intake.risk_category not in ["unknown", "general"]:
            score += 0.5
            
        # 6. Penalització per consultes curtes (menys de 20 paraules)
        words = intake.original_query.split()
        if len(words) < 20:
            # Penalització més suau: a menys paraules, major penalització (màxim -1.5)
            # 5 paraules = -1.12, 10 paraules = -0.75, 19 paraules = -0.075
            penalty = 1.5 * (20 - len(words)) / 20
            score -= penalty
            
        # Assegurar que la puntuació final estigui entre 0.0 i 10.0
        final_score = round(max(0.0, min(score, 10.0)), 1)
        return final_score
