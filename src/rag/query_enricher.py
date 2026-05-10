from typing import Dict, List

from src.rag.schemas import EnrichedQuery, QueryAnalysis, RiskCategory


RISK_EXPANSIONS: Dict[RiskCategory, List[str]] = {
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
        "Instagram",
        "WhatsApp",
        "mitjans digitals",
        "insults digitals",
        "difusió d'imatges",
        "perfil fals",
        "ridiculització pública",
        "exclusió digital",
        "protocol de ciberassetjament",
        "circuit d'actuació",
    ],
    "consum_substancies": [
        "consum de substàncies",
        "drogues",
        "alcohol",
        "cànnabis",
        "vapeig",
        "centre educatiu",
        "prevenció",
        "detecció",
        "intervenció",
        "protocol de drogues",
        "mesures educatives",
    ],
    "maltractament_infantil": [
        "maltractament infantil",
        "negligència",
        "protecció del menor",
        "detecció de maltractament",
        "indicadors de risc",
        "àmbit educatiu",
        "activació de protocol",
        "derivació",
    ],
    "violencia_sexual": [
        "violència sexual",
        "abús sexual",
        "agressió sexual",
        "grooming",
        "imatges íntimes",
        "protecció del menor",
        "activació urgent",
        "protocol d'actuació",
    ],
    "conducta_suicida": [
        "conducta suïcida",
        "ideació suïcida",
        "risc immediat",
        "mesures d'urgència",
        "protecció de l'alumne",
        "activació de protocol",
        "seguiment",
    ],
    "autolesions": [
        "autolesions",
        "conductes autolesives",
        "risc emocional",
        "protecció de l'alumne",
        "mesures d'urgència",
        "seguiment educatiu",
    ],
    "tca": [
        "trastorns de la conducta alimentària",
        "TCA",
        "anorèxia",
        "bulímia",
        "detecció a l'aula",
        "prevenció",
        "acompanyament",
        "derivació",
    ],
    "falta_greument_perjudicial": [
        "faltes greument perjudicials",
        "convivència",
        "mesures correctores",
        "expedient",
        "protocol de convivència",
        "normes de centre",
    ],
    "menor_14_infraccio_penal": [
        "menor de catorze anys",
        "menor de 14 anys",
        "infracció penal",
        "conflicte",
        "comissió d'una infracció",
        "protocol aplicable",
        "mesures educatives",
    ],
    "conductes_odi_discriminacio": [
        "conductes d'odi",
        "discriminació",
        "racisme",
        "xenofòbia",
        "homofòbia",
        "violència discriminatòria",
        "protocol d'actuació",
    ],
    "acompanyament_alumnat_transgenere": [
        "alumnat transgènere",
        "identitat de gènere",
        "expressió de gènere",
        "acompanyament educatiu",
        "protocol d'acompanyament",
    ],
    "general": [
        "convivència",
        "centre educatiu",
        "protocol d'actuació",
        "mesures educatives",
        "seguiment",
    ],
    "unknown": [
        "centre educatiu",
        "convivència",
        "protocol d'actuació",
        "orientació educativa",
        "mesures de protecció",
    ],
}


QUERY_TYPE_EXPANSIONS = {
    "application": [
        "cal recuperar actuacions pràctiques",
        "protocol d'actuació",
        "circuit d'intervenció",
        "mesures inicials",
        "mesures de protecció",
        "orientacions per al centre educatiu",
    ],
    "legal_support": [
        "base legal",
        "normativa aplicable",
        "llei",
        "decret",
        "marc jurídic",
        "fonament normatiu",
    ],
    "mixed": [
        "actuació pràctica",
        "protocol aplicable",
        "circuit d'intervenció",
        "base legal",
        "normativa aplicable",
    ],
    "unknown": [
        "protocol d'actuació",
        "orientació educativa",
        "centre educatiu",
    ],
}


def _deduplicate_terms(terms: List[str]) -> List[str]:
    """
    Elimina duplicados manteniendo el orden.
    """
    seen = set()
    clean_terms = []

    for term in terms:
        normalized = term.lower().strip()

        if normalized and normalized not in seen:
            seen.add(normalized)
            clean_terms.append(term)

    return clean_terms


def enrich_query(
    original_query: str,
    analysis: QueryAnalysis,
) -> EnrichedQuery:
    """
    Genera una query enriquecida para búsqueda semántica.

    Importante:
    - Esta query se usa para generar el embedding y buscar en Qdrant.
    - La respuesta final debe seguir usando la pregunta original del usuario.
    """

    risk_terms = RISK_EXPANSIONS.get(
        analysis.risk_category,
        RISK_EXPANSIONS["unknown"],
    )

    query_type_terms = QUERY_TYPE_EXPANSIONS.get(
        analysis.query_type,
        QUERY_TYPE_EXPANSIONS["unknown"],
    )

    expansion_terms = _deduplicate_terms(
        risk_terms + query_type_terms + analysis.detected_keywords
    )

    risk_part = ""
    if analysis.risk_category != "unknown":
        risk_part = f"Categoria de risc probable: {analysis.risk_category}. "

    intent_part = f"Tipus de consulta: {analysis.query_type}. "

    support_part = ""
    if analysis.needs_legal_support:
        support_part = (
            "La consulta pot requerir actuació pràctica i suport legal. "
        )

    search_query = (
        f"{original_query.strip()} "
        f"{risk_part}"
        f"{intent_part}"
        f"{support_part}"
        f"Context semàntic per a la recuperació documental: "
        f"{', '.join(expansion_terms)}."
    )

    return EnrichedQuery(
        original_query=original_query,
        search_query=search_query,
        expansion_terms=expansion_terms,
    )