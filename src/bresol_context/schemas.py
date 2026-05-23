from dataclasses import dataclass, field
from typing import List, Literal, Optional

ReportingMode = Literal["anonymous", "identified", "unknown"]
ReporterRole = Literal["victim", "teacher", "observer", "parent", "unknown"]
IdentificationStatus = Literal["identified", "anonymous", "unknown"]
PhaseAssessment = Literal[
    "sense_indicis_delictius",
    "indicis_possibles",
    "indicis_clars_activitat_delictiva",
    "unknown",
]
ResponseType = Literal[
    "urgent_protection",
    "collect_minimum_information",
    "safe_identification_guidance",
    "anonymous_protocol",
    "protocol_with_missing_info",
    "protocol_response",
    "legal_support",
    "mixed_response",
    "insufficient_context",
    "out_of_scope",
]


@dataclass
class BresolIntakeAnalysis:
    original_query: str
    bresol_case_type: str = "unknown"
    risk_category: str = "unknown"
    
    detected_indicators: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    missing_minimum_elements: List[str] = field(default_factory=list)
    
    reporting_mode: ReportingMode = "unknown"
    reporter_role: ReporterRole = "unknown"
    victim_identified: bool = False
    aggressor_identified: bool = False
    
    phase_assessment: PhaseAssessment = "unknown"
    possible_crime_indicators: List[str] = field(default_factory=list)
    
    requires_urgent_review: bool = False
    enriched_context_hint: Optional[str] = None
    notes: Optional[str] = None



@dataclass
class MissingParameter:
    parameter_name: str
    parameter_label: str
    importance: Literal["high", "medium", "low"]
    question_context: str


@dataclass
class CaseInformationReport:
    completed_parameters: List[str] = field(default_factory=list)
    missing_parameters: List[MissingParameter] = field(default_factory=list)
    minimum_information_score: float = 0.0
    all_minimum_elements_met: bool = False


@dataclass
class TeacherGuidance:
    recommended_questions: List[str] = field(default_factory=list)
    avoid_questions: List[str] = field(default_factory=list)
    empathy_statement: str = ""


@dataclass
class ResponsePlan:
    response_type: ResponseType
    should_run_documental_rag: bool
    urgent_actions: List[str] = field(default_factory=list)
    rag_instructions: str = ""
