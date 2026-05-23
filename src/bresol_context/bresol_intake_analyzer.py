import json
import re
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    PhaseAssessment,
    ReportingMode,
    ReporterRole
)
from src.bresol_context.risk_type import (
    BRESOL_RISK_TAXONOMY,
    BRESOL_PHASE_2_CRITERIA,
)


BRESOL_INTAKE_PROMPT = """
Ets un analitzador inicial d'alertes educatives segons el marc intern b-resol.

IMPORTANT:
- No has de donar una resposta final al docent.
- No has de citar protocols oficials.
- No has d'inventar fets que no apareguin en la consulta.
- Retorna només JSON vàlid, sense markdown.

Objectiu:
Analitzar la consulta inicial per extreure els indicadors presents i la fase inicial de risc.

Marc de riscos b-resol:
{risk_taxonomy}

Criteris Fase 2 b-resol:
{phase_2_criteria}

Consulta inicial:
{user_query}

Retorna exactament aquest JSON:

{
  "bresol_case_type": "string (una de les claus del diccionari de riscos, ex: assetjament_escolar)",
  "risk_category": "string (igual que bresol_case_type)",
  "detected_indicators": ["string (indicadors concrets detectats)"],
  "missing_information": ["string (elements importants de la situació que falten)"],
  "missing_minimum_elements": ["string (claus exactes de la llista minimum_elements del risc detectat que no es descriuen amb detall a la consulta, ex: 'repeticio_temporal', 'desequilibri_poder', 'intencionalitat', 'possible_victima_o_alumne_afectat')"],
  "reporter_role": "victim | teacher | observer | parent | unknown",
  "victim_identified": true/false (true només si es diu o s'identifica clarament la víctima),
  "aggressor_identified": true/false (true només si s'identifica l'agressor),
  "phase_assessment": "sense_indicis_delictius | indicis_possibles | indicis_clars_activitat_delictiva | unknown",
  "possible_crime_indicators": ["string"],
  "requires_urgent_review": true/false (true si hi ha conducta_suicida, violencia_sexual o indicis clars de delicte greu o risc vital immediat),
  "enriched_context_hint": "string (pista de context molt breu per a cerca vectorial)",
  "notes": "string or null"
}
"""


class BresolIntakeAnalyzer:
    def __init__(
        self,
        gemini_api_key: str,
        gemini_model: str = "gemini-2.5-flash-lite",
        temperature: float = 0.0,
    ) -> None:
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=temperature,
        )
        self.prompt = PromptTemplate.from_template(BRESOL_INTAKE_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def analyze(self, user_query: str, reporting_mode: str) -> BresolIntakeAnalysis:
        try:
            raw_response = self.chain.invoke({
                "user_query": user_query,
                "risk_taxonomy": json.dumps(
                    {k: {"label": v["label"], "key_indicators": v["key_indicators"]} 
                     for k, v in BRESOL_RISK_TAXONOMY.items()},
                    ensure_ascii=False,
                    indent=2,
                ),
                "phase_2_criteria": json.dumps(
                    BRESOL_PHASE_2_CRITERIA,
                    ensure_ascii=False,
                    indent=2,
                ),
            })

            data = self._parse_json(raw_response)

            return BresolIntakeAnalysis(
                original_query=user_query,
                bresol_case_type=self._safe_str(data.get("bresol_case_type"), "unknown"),
                risk_category=self._safe_str(data.get("risk_category"), "unknown"),
                detected_indicators=self._safe_list(data.get("detected_indicators")),
                missing_information=self._safe_list(data.get("missing_information")),
                missing_minimum_elements=self._safe_list(data.get("missing_minimum_elements")),
                reporting_mode=self._safe_reporting_mode(reporting_mode),
                reporter_role=self._safe_reporter_role(data.get("reporter_role")),
                victim_identified=self._safe_bool(data.get("victim_identified"), False),
                aggressor_identified=self._safe_bool(data.get("aggressor_identified"), False),
                phase_assessment=self._safe_phase(data.get("phase_assessment")),
                possible_crime_indicators=self._safe_list(data.get("possible_crime_indicators")),
                requires_urgent_review=self._safe_bool(data.get("requires_urgent_review"), False),
                enriched_context_hint=self._safe_optional_str(data.get("enriched_context_hint")),
                notes=self._safe_optional_str(data.get("notes")),
            )
        
        except Exception as exc:
            return self._fallback(user_query, reporting_mode, str(exc))

    def _parse_json(self, raw_response: str) -> dict:
        if not isinstance(raw_response, str) or not raw_response.strip():
            raise ValueError("Empty response from Bresol Intake Analyzer.")

        text = raw_response.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {raw_response}")

        return json.loads(match.group(0))

    def _safe_str(self, value, default: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return default

    def _safe_optional_str(self, value) -> Optional[str]:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _safe_list(self, value) -> list:
        if not isinstance(value, list):
            return []
        clean = []
        for item in value:
            if isinstance(item, str) and item.strip():
                clean.append(item.strip())
        return clean

    def _safe_bool(self, value, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        return default

    def _safe_phase(self, value) -> PhaseAssessment:
        allowed = {"sense_indicis_delictius", "indicis_possibles", "indicis_clars_activitat_delictiva", "unknown"}
        if isinstance(value, str) and value in allowed:
            return value # type: ignore
        return "unknown"
        
    def _safe_reporting_mode(self, value) -> ReportingMode:
        allowed = {"anonymous", "identified", "unknown"}
        if isinstance(value, str) and value in allowed:
            return value # type: ignore
        return "unknown"
        
    def _safe_reporter_role(self, value) -> ReporterRole:
        allowed = {"victim", "teacher", "observer", "parent", "unknown"}
        if isinstance(value, str) and value in allowed:
            return value # type: ignore
        return "unknown"

    def _fallback(self, user_query: str, reporting_mode: str, error: str) -> BresolIntakeAnalysis:
        # Check simple urgency keywords to at least capture extreme risks
        lower_query = user_query.lower()
        is_urgent = any(word in lower_query for word in ["suïcidi", "matar", "violació", "abús sexual", "no vull viure"])
        
        return BresolIntakeAnalysis(
            original_query=user_query,
            bresol_case_type="unknown",
            risk_category="unknown",
            detected_indicators=[],
            missing_information=[],
            missing_minimum_elements=[],
            reporting_mode=self._safe_reporting_mode(reporting_mode),
            reporter_role="unknown",
            victim_identified=False,
            aggressor_identified=False,
            phase_assessment="unknown",
            possible_crime_indicators=[],
            requires_urgent_review=is_urgent,
            enriched_context_hint=None,
            notes=f"Fallback bresol intake. Error: {error}",
        )
