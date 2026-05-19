from dataclasses import dataclass, field
from typing import List, Optional

from src.rag.schemas import QueryAnalysis
from src.bresol_context.schemas import BresolIntakeAnalysis


@dataclass
class EnrichedQuery:
    original_query: str
    search_query: str
    expansion_terms: List[str] = field(default_factory=list)
    bresol_indicators: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)


class QueryEnricher:
    def enrich(
        self,
        original_query: str,
        analysis: QueryAnalysis,
        bresol_intake: Optional[BresolIntakeAnalysis] = None,
    ) -> EnrichedQuery:
        expansion_terms = []

        expansion_terms.extend(
            self._terms_for_risk_category(analysis.risk_category)
        )

        expansion_terms.extend(
            self._terms_for_query_type(analysis.query_type)
        )

        bresol_indicators = []
        missing_information = []

        if bresol_intake is not None:
            bresol_indicators.extend(bresol_intake.detected_indicators)
            missing_information.extend(bresol_intake.missing_information)

            if bresol_intake.enriched_context_hint:
                expansion_terms.append(bresol_intake.enriched_context_hint)

            expansion_terms.extend(bresol_intake.detected_indicators)
            expansion_terms.extend(bresol_intake.possible_crime_indicators)

            if bresol_intake.phase_assessment != "unknown":
                expansion_terms.append(
                    f"fase o valoració inicial: {bresol_intake.phase_assessment}"
                )

        clean_terms = self._deduplicate(expansion_terms)

        search_query = (
            f"{original_query}\n"
            f"Categoria de risc probable: {analysis.risk_category}.\n"
            f"Tipus de consulta: {analysis.query_type}.\n"
            f"Capa documental prioritària: {analysis.retrieval_layer}.\n"
        )

        if bresol_intake is not None:
            search_query += (
                f"Classificació inicial b-resol: {bresol_intake.bresol_case_type}.\n"
                f"Indicadors detectats segons b-resol: {', '.join(bresol_intake.detected_indicators)}.\n"
                f"Valoració inicial de fase: {bresol_intake.phase_assessment}.\n"
            )

            if bresol_intake.enriched_context_hint:
                search_query += (
                    f"Pista semàntica b-resol: {bresol_intake.enriched_context_hint}.\n"
                )

        search_query += (
            "Context semàntic per a la recuperació documental: "
            + ", ".join(clean_terms)
            + "."
        )

        return EnrichedQuery(
            original_query=original_query,
            search_query=search_query,
            expansion_terms=clean_terms,
            bresol_indicators=bresol_indicators,
            missing_information=missing_information,
        )

    def _terms_for_risk_category(self, risk_category: str) -> List[str]:
        mapping = {
            "assetjament_escolar": [
                "assetjament escolar",
                "bullying",
                "violència entre iguals",
                "repetició de conductes",
                "intencionalitat de fer mal",
                "desequilibri de poder",
                "víctima",
                "agressor",
                "observadors",
                "protocol d'actuació",
                "mesures de protecció",
            ],
            "ciberassetjament": [
                "ciberassetjament",
                "cyberbullying",
                "xarxes socials",
                "missatgeria",
                "difusió digital",
                "perfils falsos",
                "insults digitals",
                "protocol de ciberassetjament",
                "evidències digitals",
            ],
            "consum_substancies": [
                "consum de substàncies",
                "alcohol",
                "drogues",
                "cànnabis",
                "vapeig",
                "conductes de risc",
                "actuació educativa",
            ],
            "conducta_suicida": [
                "conducta suïcida",
                "ideació suïcida",
                "risc vital",
                "urgència",
                "protecció immediata",
                "protocol d'actuació",
            ],
            "tca": [
                "trastorns de la conducta alimentària",
                "anorèxia",
                "bulímia",
                "afartament",
                "imatge corporal",
                "conductes compensatòries",
            ],
            "maltractament_infantil": [
                "maltractament infantil",
                "negligència",
                "lesions inexplicades",
                "protecció del menor",
                "situació de risc",
            ],
        }

        return mapping.get(risk_category, ["convivència escolar", "protocol educatiu"])

    def _terms_for_query_type(self, query_type: str) -> List[str]:
        if query_type == "application":
            return [
                "actuacions pràctiques",
                "circuit d'intervenció",
                "mesures inicials",
                "mesures de protecció",
                "orientacions per al centre educatiu",
            ]

        if query_type == "legal_support":
            return [
                "normativa aplicable",
                "base legal",
                "article",
                "llei",
                "decret",
            ]

        if query_type == "mixed":
            return [
                "actuació pràctica",
                "protocol",
                "circuit",
                "base legal",
                "normativa de suport",
            ]

        return ["orientació documental", "context educatiu"]

    def _deduplicate(self, terms: List[str]) -> List[str]:
        seen = set()
        clean = []

        for term in terms:
            if not term:
                continue

            normalized = term.strip().lower()

            if normalized not in seen:
                seen.add(normalized)
                clean.append(term.strip())

        return clean


def enrich_query(
    original_query: str,
    analysis: QueryAnalysis,
    bresol_intake: Optional[BresolIntakeAnalysis] = None,
) -> EnrichedQuery:
    return QueryEnricher().enrich(original_query, analysis, bresol_intake)