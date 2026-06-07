from dataclasses import dataclass, field
from typing import List, Optional

RiskCategory = str

@dataclass
class QueryAnalysis:
    original_query: str
    query_type: str
    retrieval_layer: str
    risk_category: str
    secondary_risk_categories: List[str]
    confidence: str
    needs_legal_support: bool
    detected_indicators: List[str]
    missing_information: List[str]
    followup_questions: List[str]
    should_ask_followup: bool
    safety_level: str
    requires_human_review: bool
    detected_keywords: List[str]
    enriched_query_hint: str
    analyzer_used: str
    urgency_level: str = "unknown"
    has_implicated_parties: bool = False
    detected_features: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    is_out_of_scope: bool = False

@dataclass
class EnrichedQuery:
    original_query: str
    search_query: str
    expansion_terms: List[str]
