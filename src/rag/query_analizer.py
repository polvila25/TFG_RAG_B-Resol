import json
import re
from typing import Any, Dict, List, Optional
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from src.rag.schemas import QueryAnalysis


ALLOWED_QUERY_TYPES = {
    "application",
    "legal_support",
    "mixed",
    "unknown",
}

ALLOWED_RETRIEVAL_LAYERS = {
    "application",
    "legal_support",
    "unknown",
}

ALLOWED_RISK_CATEGORIES = {
    "assetjament_escolar",
    "ciberassetjament",
    "conductes_odi_discriminacio",
    "violencies_masclistes",
    "violencia_sexual",
    "maltractament_infantil",
    "violencia_familiar",
    "falta_greument_perjudicial",
    "menor_14_infraccio_penal",
    "presumpte_delicte",
    "extremisme_violent",
    "conducta_suicida",
    "autolesions",
    "tca",
    "consum_substancies",
    "conflicte_convivencia",
    "acompanyament_alumnat_transgenere",
    "general",
    "unknown",
}

ALLOWED_CONFIDENCE = {
    "low",
    "medium",
    "high",
}

ALLOWED_SAFETY_LEVELS = {
    "low",
    "medium",
    "high",
    "critical",
    "unknown",
}


QUERY_ANALYZER_PROMPT = """
Ets un analitzador estructurat de consultes per a un sistema RAG educatiu.

IMPORTANT:
- No has de respondre la consulta del docent.
- No has de donar instruccions d'actuació.
- No has de citar protocols.
- Només has d'analitzar la consulta i retornar JSON vàlid.
- No utilitzis markdown.
- No escriguis explicacions fora del JSON.

Objectiu:
Analitzar la consulta inicial d'un docent o responsable de convivència i extreure:
1. tipus de consulta
2. capa de recuperació documental
3. categoria de risc probable
4. categories secundàries
5. indicadors detectats
6. si cal suport legal
7. nivell de seguretat orientatiu
8. si requereix revisió humana
9. una pista breu per enriquir la query semàntica
10. si la consulta és fora de domini (no relacionada amb convivència escolar, assetjament, salut mental o normatives educatives)

Tipus de consulta permesos:
- application: pregunta què fer, com actuar, quin protocol activar, quines mesures aplicar.
- legal_support: pregunta per llei, decret, normativa, base legal o articles.
- mixed: pregunta actuació pràctica i també base legal.
- unknown: no es pot determinar.

Capes de recuperació permeses:
- application: protocols, circuits, guies i actuacions pràctiques.
- legal_support: lleis, decrets i normativa.
- unknown: no es pot determinar.

Categories de risc permeses:
- assetjament_escolar
- ciberassetjament
- conductes_odi_discriminacio
- violencies_masclistes
- violencia_sexual
- maltractament_infantil
- violencia_familiar
- falta_greument_perjudicial
- menor_14_infraccio_penal
- presumpte_delicte
- extremisme_violent
- conducta_suicida
- autolesions
- tca
- consum_substancies
- conflicte_convivencia
- acompanyament_alumnat_transgenere
- general
- unknown

Criteris orientatius:
- Si pregunta "què he de fer", "com actuar", "quin protocol", classifica com application.
- Si pregunta "quina llei", "base legal", "normativa", classifica com legal_support.
- Si demana actuació i llei, classifica com mixed.
- Si parla d'Instagram, WhatsApp, xarxes socials, perfils falsos, fotos o missatges digitals, pot ser ciberassetjament.
- Si parla de drogues, alcohol, cànnabis, vapeig o substàncies, pot ser consum_substancies.
- Si parla de cops, agressions, insults repetits, por, humiliacions o exclusió entre iguals, pot ser assetjament_escolar o conflicte_convivencia.
- Si parla de voler morir, suïcidi, pla per fer-se mal o desesperança greu, pot ser conducta_suicida.
- Si parla de talls, autolesions o fer-se mal, pot ser autolesions.
- Si parla de no menjar, vomitar, anorèxia, bulímia, pes o imatge corporal, pot ser tca.
- Si parla de maltractament a casa, negligència, lesions inexplicades o desatenció, pot ser maltractament_infantil.
- Si parla d'abús sexual, grooming, imatges íntimes o tocament sexual, pot ser violencia_sexual.
- Si parla de discriminació, racisme, odi, origen, religió, orientació sexual o identitat de gènere, pot ser conductes_odi_discriminacio.
- Si parla d'un menor de 13 anys, menor de 14 anys o infracció penal, pot ser menor_14_infraccio_penal.

Nivell de seguretat:
- critical: risc immediat, suïcidi, autolesió greu, abús sexual, violència greu, amenaça greu.
- high: possible risc seriós però sense immediatesa clara.
- medium: situació sensible que requereix seguiment.
- low: consulta general o normativa sense risc immediat.
- unknown: no es pot valorar.

Retorna exactament aquest JSON:

{{
  "query_type": "application | legal_support | mixed | unknown",
  "retrieval_layer": "application | legal_support | unknown",
  "risk_category": "categoria permesa",
  "secondary_risk_categories": ["categoria permesa"],
  "confidence": "low | medium | high",
  "needs_legal_support": true,
  "detected_indicators": ["indicador 1", "indicador 2"],
  "detected_keywords": ["keyword 1", "keyword 2"],
  "safety_level": "low | medium | high | critical | unknown",
  "requires_human_review": true,
  "is_out_of_scope": true | false,
  "enriched_query_hint": "frase breu en català per ajudar a recuperar documents",
  "notes": "comentari breu o null"
}}

Consulta del docent:
{user_query}
"""


class QueryAnalyzer:
    """
    Analitzador bàsic de consultes amb LLM.

    Aquesta versió:
    - NO utilitza encara el document intern de b-resol.
    - NO fa intake avançat.
    - NO decideix la resposta final.
    - Només classifica i estructura la consulta per preparar el retrieval.
    """

    def __init__(
        self,
        gemini_api_key: str,
        gemini_model: str = "gemini-2.5-flash-lite",
        temperature: float = 0.0,
    ) -> None:
        self.llm = ChatGoogleGenerativeAI(
            google_api_key= os.getenv("GEMINI_API_KEY"),
            model=gemini_model,
            temperature=temperature,
        )

        self.prompt = PromptTemplate.from_template(QUERY_ANALYZER_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def analyze(self, user_query: str) -> QueryAnalysis:
        """
        Analitza una consulta del docent i retorna QueryAnalysis.

        Si el LLM falla o retorna JSON invàlid, aplica fallback bàsic per regles.
        """

        try:
            raw_response = self.chain.invoke({
                "user_query": user_query,
            })

            parsed = self._parse_json_response(raw_response)
            normalized = self._normalize_analysis_dict(parsed, user_query)

            return QueryAnalysis(
                original_query=user_query,
                query_type=normalized["query_type"],
                retrieval_layer=normalized["retrieval_layer"],
                risk_category=normalized["risk_category"],
                secondary_risk_categories=normalized["secondary_risk_categories"],
                confidence=normalized["confidence"],
                needs_legal_support=normalized["needs_legal_support"],
                detected_indicators=normalized["detected_indicators"],
                missing_information=[],
                followup_questions=[],
                should_ask_followup=False,
                safety_level=normalized["safety_level"],
                requires_human_review=normalized["requires_human_review"],
                detected_keywords=normalized["detected_keywords"],
                enriched_query_hint=normalized["enriched_query_hint"],
                analyzer_used="llm",
                notes=normalized["notes"],
                is_out_of_scope=normalized["is_out_of_scope"],
            )

        except Exception as exc:
            return self._fallback_rules(user_query, error=str(exc))

    def _parse_json_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Extreu JSON d'una resposta del LLM.

        Encara que el prompt demani JSON pur, aquest mètode és tolerant
        si el model retorna ```json ... ```.
        """

        if not isinstance(raw_response, str) or not raw_response.strip():
            raise ValueError("Empty response from query analyzer LLM.")

        text = raw_response.strip()

        text = text.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response: {raw_response}")

        json_text = match.group(0)

        try:
            return json.loads(json_text)

        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from LLM: {json_text}") from exc

    def _normalize_analysis_dict(
        self,
        data: Dict[str, Any],
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Normalitza i valida els camps retornats pel LLM.
        """

        query_type = self._safe_choice(
            value=data.get("query_type"),
            allowed=ALLOWED_QUERY_TYPES,
            default="unknown",
        )

        retrieval_layer = self._safe_choice(
            value=data.get("retrieval_layer"),
            allowed=ALLOWED_RETRIEVAL_LAYERS,
            default="unknown",
        )

        risk_category = self._safe_choice(
            value=data.get("risk_category"),
            allowed=ALLOWED_RISK_CATEGORIES,
            default="unknown",
        )

        confidence = self._safe_choice(
            value=data.get("confidence"),
            allowed=ALLOWED_CONFIDENCE,
            default="low",
        )

        safety_level = self._safe_choice(
            value=data.get("safety_level"),
            allowed=ALLOWED_SAFETY_LEVELS,
            default="unknown",
        )

        secondary_risk_categories = self._safe_list_of_choices(
            values=data.get("secondary_risk_categories"),
            allowed=ALLOWED_RISK_CATEGORIES,
        )

        detected_indicators = self._safe_string_list(
            data.get("detected_indicators")
        )

        detected_keywords = self._safe_string_list(
            data.get("detected_keywords")
        )

        needs_legal_support = self._safe_bool(
            data.get("needs_legal_support"),
            default=(query_type == "mixed"),
        )

        requires_human_review = self._safe_bool(
            data.get("requires_human_review"),
            default=True,
        )

        is_out_of_scope = self._safe_bool(
            data.get("is_out_of_scope"),
            default=False,
        )

        enriched_query_hint = data.get("enriched_query_hint")
        if not isinstance(enriched_query_hint, str) or not enriched_query_hint.strip():
            enriched_query_hint = self._build_basic_enriched_hint(
                user_query=user_query,
                risk_category=risk_category,
                query_type=query_type,
            )

        notes = data.get("notes")
        if notes is not None and not isinstance(notes, str):
            notes = None

        # Ajustes defensivos
        if query_type == "legal_support":
            retrieval_layer = "legal_support"

        if query_type == "application":
            retrieval_layer = "application"

        if query_type == "mixed":
            retrieval_layer = "application"
            needs_legal_support = True

        if safety_level in {"high", "critical"}:
            requires_human_review = True

        return {
            "query_type": query_type,
            "retrieval_layer": retrieval_layer,
            "risk_category": risk_category,
            "secondary_risk_categories": secondary_risk_categories,
            "confidence": confidence,
            "needs_legal_support": needs_legal_support,
            "detected_indicators": detected_indicators,
            "detected_keywords": detected_keywords,
            "safety_level": safety_level,
            "requires_human_review": requires_human_review,
            "enriched_query_hint": enriched_query_hint,
            "notes": notes,
            "is_out_of_scope": is_out_of_scope,
        }

    def _safe_choice(
        self,
        value: Any,
        allowed: set[str],
        default: str,
    ) -> str:
        if isinstance(value, str):
            clean = value.strip()
            if clean in allowed:
                return clean

        return default

    def _safe_list_of_choices(
        self,
        values: Any,
        allowed: set[str],
    ) -> List[str]:
        if not isinstance(values, list):
            return []

        clean_values = []

        for value in values:
            if isinstance(value, str):
                clean = value.strip()
                if clean in allowed and clean not in clean_values:
                    clean_values.append(clean)

        return clean_values

    def _safe_string_list(self, values: Any) -> List[str]:
        if not isinstance(values, list):
            return []

        clean_values = []

        for value in values:
            if isinstance(value, str):
                clean = value.strip()
                if clean and clean not in clean_values:
                    clean_values.append(clean)

        return clean_values

    def _safe_bool(self, value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value

        return default

    def _build_basic_enriched_hint(
        self,
        user_query: str,
        risk_category: str,
        query_type: str,
    ) -> str:
        return (
            f"Consulta educativa relacionada amb {risk_category}. "
            f"Tipus de consulta: {query_type}. "
            f"Cal recuperar documents oficials, protocols, circuits o normativa aplicable segons correspongui."
        )

    def _fallback_rules(
        self,
        user_query: str,
        error: Optional[str] = None,
    ) -> QueryAnalysis:
        """
        Fallback simple si falla el LLM.

        Es deliberadament bàsic. Serveix perquè el pipeline no es trenqui.
        """

        query_lower = user_query.lower()

        query_type = "application"
        retrieval_layer = "application"
        needs_legal_support = False

        if any(term in query_lower for term in ["quina llei", "base legal", "normativa", "decret", "article"]):
            query_type = "legal_support"
            retrieval_layer = "legal_support"

        if any(term in query_lower for term in ["què he de fer", "que he de fer", "com actuar", "quin protocol"]):
            query_type = "application"
            retrieval_layer = "application"

        if any(term in query_lower for term in ["base legal", "quina llei"]) and any(
            term in query_lower for term in ["què he de fer", "que he de fer", "com actuar", "quin protocol"]
        ):
            query_type = "mixed"
            retrieval_layer = "application"
            needs_legal_support = True

        risk_category = "unknown"
        detected_keywords = []

        keyword_map = {
            "ciberassetjament": ["instagram", "whatsapp", "xarxes", "fotos", "missatges", "perfil fals"],
            "consum_substancies": ["droga", "drogues", "alcohol", "cànnabis", "cannabis", "vapeig", "substàncies"],
            "conducta_suicida": ["suïcidi", "suicidi", "vol morir", "no vol viure", "matar-se"],
            "autolesions": ["autolesions", "es talla", "talls", "fer-se mal"],
            "tca": ["tca", "anorèxia", "anorexia", "bulímia", "bulimia", "no menja", "vomita"],
            "violencia_sexual": ["abús sexual", "abus sexual", "grooming", "imatges íntimes", "tocaments"],
            "maltractament_infantil": ["maltractament", "negligència", "negligencia", "lesions inexplicades"],
            "menor_14_infraccio_penal": ["menor de 14", "menor de catorze", "13 anys", "infracció penal"],
            "assetjament_escolar": ["assetjament", "bullying", "insults", "burles", "humiliació", "exclusió"],
        }

        for category, keywords in keyword_map.items():
            matches = [keyword for keyword in keywords if keyword in query_lower]
            if matches:
                risk_category = category
                detected_keywords = matches
                break

        safety_level = "medium"
        requires_human_review = True

        if risk_category in {"conducta_suicida", "autolesions", "violencia_sexual"}:
            safety_level = "critical"

        enriched_query_hint = self._build_basic_enriched_hint(
            user_query=user_query,
            risk_category=risk_category,
            query_type=query_type,
        )

        # Heuristic check for out of scope:
        is_out_of_scope = False
        out_of_scope_keywords = ["barça", "temps fa", "guerra", "capità", "capita", "futbol", "temps", "història d", "historia d", "qui és el", "qui es el", "quin temps"]
        if risk_category == "unknown" and any(term in query_lower for term in out_of_scope_keywords):
            is_out_of_scope = True

        return QueryAnalysis(
            original_query=user_query,
            query_type=query_type,
            retrieval_layer=retrieval_layer,
            risk_category=risk_category,
            secondary_risk_categories=[],
            confidence="low",
            needs_legal_support=needs_legal_support,
            detected_indicators=[],
            missing_information=[],
            followup_questions=[],
            should_ask_followup=False,
            safety_level=safety_level,
            requires_human_review=requires_human_review,
            detected_keywords=detected_keywords,
            enriched_query_hint=enriched_query_hint,
            analyzer_used="fallback",
            notes=f"Fallback per regles. Error LLM: {error}",
            is_out_of_scope=is_out_of_scope,
        )


def analyze_query(
    user_query: str,
    gemini_api_key: str,
    gemini_model: str = "gemini-2.5-flash-lite",
) -> QueryAnalysis:
    """
    Funció helper per usar l'analitzador de manera simple.
    """

    analyzer = QueryAnalyzer(
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )

    return analyzer.analyze(user_query)