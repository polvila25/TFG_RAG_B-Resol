# src/bresol_context/bresol_intake_analyzer.py

import json
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.bresol_context.risk_type import (
    BRESOL_RISK_TAXONOMY,
    BRESOL_PHASE_2_CRITERIA,
)


PhaseAssessment = Literal[
    "sense_indicis_delictius",
    "indicis_possibles",
    "indicis_clars_activitat_delictiva",
    "unknown",
]


@dataclass
class BresolAnalisis:
    original_query: str

    bresol_case_type: str = "unknown"
    risk_category: str = "unknown"

    detected_indicators: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    followup_questions: List[str] = field(default_factory=list)

    phase_assessment: PhaseAssessment = "unknown"
    possible_crime_indicators: List[str] = field(default_factory=list)

    should_ask_followup: bool = False
    requires_human_review: bool = True
    requires_urgent_review: bool = False

    enriched_context_hint: Optional[str] = None
    notes: Optional[str] = None


BRESOL_INTAKE_PROMPT = """
Ets un analitzador inicial d'alertes educatives segons el marc intern b-resol.

IMPORTANT:
- No has de donar una resposta final al docent.
- No has de citar protocols oficials.
- No has de fer retrieval documental.
- No has d'inventar fets que no apareguin en la consulta.
- No presentis la classificació com un diagnòstic definitiu.
- Retorna només JSON vàlid, sense markdown.

Objectiu:
Analitzar la consulta inicial per:
1. classificar orientativament la situació
2. detectar indicadors presents
3. detectar informació faltant
4. valorar si caldria preguntar més informació
5. valorar fase o gravetat inicial
6. detectar possibles indicis d'activitat delictiva
7. generar una pista de context per enriquir la query de recuperació documental

Marc de riscos b-resol:
{risk_taxonomy}

Criteris Fase 2 b-resol:
{phase_2_criteria}

Consulta inicial:
{user_query}

Retorna exactament aquest JSON:

{{
  "bresol_case_type": "string",
  "risk_category": "string",
  "detected_indicators": ["string"],
  "missing_information": ["string"],
  "followup_questions": ["string"],
  "phase_assessment": "sense_indicis_delictius | indicis_possibles | indicis_clars_activitat_delictiva | unknown",
  "possible_crime_indicators": ["string"],
  "should_ask_followup": true,
  "requires_human_review": true,
  "requires_urgent_review": false,
  "enriched_context_hint": "string",
  "notes": "string or null"
}}

Criteris:
- Si la consulta és massa ambigua per orientar una primera actuació, should_ask_followup = true.
- Si la consulta ja permet orientar una primera actuació, should_ask_followup = false encara que hi hagi informació a confirmar.
- Si hi ha risc greu, violència sexual, conducta suïcida, autolesions amb risc vital, maltractament greu o indicis clars d'activitat delictiva, requires_urgent_review = true.
- Si només hi ha indicis possibles, requires_human_review = true però requires_urgent_review pot ser false.
"""


class BresolAnalizador:
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

    def analyze(self, user_query: str) -> BresolAnalisis:
        try:
            raw_response = self.chain.invoke({
                "user_query": user_query,
                "risk_taxonomy": json.dumps(
                    BRESOL_RISK_TAXONOMY,
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

            return BresolAnalisis(
                original_query=user_query,
                bresol_case_type=self._safe_str(data.get("bresol_case_type"), "unknown"),
                risk_category=self._safe_str(data.get("risk_category"), "unknown"),
                detected_indicators=self._safe_list(data.get("detected_indicators")),
                missing_information=self._safe_list(data.get("missing_information")),
                followup_questions=self._safe_list(data.get("followup_questions")),
                phase_assessment=self._safe_phase(data.get("phase_assessment")),
                possible_crime_indicators=self._safe_list(data.get("possible_crime_indicators")),
                should_ask_followup=self._safe_bool(data.get("should_ask_followup"), False),
                requires_human_review=self._safe_bool(data.get("requires_human_review"), True),
                requires_urgent_review=self._safe_bool(data.get("requires_urgent_review"), False),
                enriched_context_hint=self._safe_optional_str(data.get("enriched_context_hint")),
                notes=self._safe_optional_str(data.get("notes")),
            )

        except Exception as exc:
            return self._fallback(user_query, str(exc))

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

    def _safe_list(self, value) -> List[str]:
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
        allowed = {
            "sense_indicis_delictius",
            "indicis_possibles",
            "indicis_clars_activitat_delictiva",
            "unknown",
        }

        if isinstance(value, str) and value in allowed:
            return value

        return "unknown"

    def _fallback(self, user_query: str, error: str) -> BresolAnalisis:
        return BresolAnalisis(
            original_query=user_query,
            bresol_case_type="unknown",
            risk_category="unknown",
            detected_indicators=[],
            missing_information=[],
            followup_questions=[],
            phase_assessment="unknown",
            possible_crime_indicators=[],
            should_ask_followup=False,
            requires_human_review=True,
            requires_urgent_review=False,
            enriched_context_hint=None,
            notes=f"Fallback bresol intake. Error: {error}",
        )