from dataclasses import dataclass, field
from typing import List, Optional

RiskCategory = str

@dataclass
class QueryAnalysis:
    original_query: str
    query_type: str
    retrieval_layer: str
    confidence: str
    needs_legal_support: bool
    requires_human_review: bool
    detected_keywords: List[str]
    enriched_query_hint: str
    analyzer_used: str
    has_implicated_parties: bool = False
    detected_features: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class EnrichedQuery:
    original_query: str
    search_query: str
    expansion_terms: List[str]
