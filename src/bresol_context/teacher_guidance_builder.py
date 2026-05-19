from src.bresol_context.schemas import (
    BresolIntakeAnalysis,
    CaseInformationReport,
    TeacherGuidance,
)
from src.bresol_context.risk_type import BRESOL_RISK_TAXONOMY


class TeacherGuidanceBuilder:
    """
    Constructs the conversational guidance for the teacher.
    Ensures empathy, strict LOPIVI anonymity compliance, and prevents interrogation fatigue.
    """

    def build(
        self, intake: BresolIntakeAnalysis, report: CaseInformationReport
    ) -> TeacherGuidance:
        empathy_statement = self._build_empathy_statement(intake)
        
        # 1. Build avoid questions dynamically from the taxonomy config
        risk_category = intake.risk_category
        taxonomy_info = BRESOL_RISK_TAXONOMY.get(risk_category, BRESOL_RISK_TAXONOMY["general"])
        
        avoid_questions = list(taxonomy_info.get("avoid_questions", []))

        # Add general anonymity fallbacks if not already present and mode is anonymous
        if not intake.victim_identified or intake.reporting_mode == "anonymous":
            general_fallbacks = [
                "Evita demanar el nom complet de la víctima directament.",
                "Evita demanar dades identificatives del informant si vol mantenir l'anonimat.",
            ]
            for q in general_fallbacks:
                if q not in avoid_questions:
                    avoid_questions.append(q)

        # 2. Build recommended questions
        # Prioritize high importance missing parameters
        sorted_missing = sorted(
            report.missing_parameters,
            key=lambda x: 0 if x.importance == "high" else (1 if x.importance == "medium" else 2)
        )

        raw_questions = [mp.question_context for mp in sorted_missing]

        # 3. Apply dynamic question limits
        limit = 2  # Default
        
        if intake.requires_urgent_review:
            # Urgent cases: 1-2 critical questions only (focus on safety)
            limit = 2
        elif report.minimum_information_score <= 3:
            # Complex/poor info cases: we need more info, max 4
            limit = 4
            
        recommended_questions = raw_questions[:limit]

        return TeacherGuidance(
            recommended_questions=recommended_questions,
            avoid_questions=avoid_questions,
            empathy_statement=empathy_statement,
        )

    def _build_empathy_statement(self, intake: BresolIntakeAnalysis) -> str:
        if intake.requires_urgent_review:
            return (
                "Entenc que aquesta és una situació molt delicada i que requereix atenció prioritària. "
                "La seguretat de l'alumne/a és el més important ara mateix."
            )
            
        if intake.risk_category == "assetjament_escolar":
            return (
                "Gràcies per compartir aquesta informació. L'escola és un espai segur, i el teu "
                "avís ens ajuda a mantenir-lo lliure de violències."
            )
            
        if intake.risk_category == "ciberassetjament":
            return (
                "Agraeixo molt que ens informis d'això. El món digital a vegades és complex, "
                "però estem aquí per protegir l'alumnat també en aquest àmbit."
            )
            
        if intake.risk_category in ["conducta_suicida", "autolesions", "tca"]:
            return (
                "Aquesta és una situació molt sensible que abordarem amb la màxima cura i respecte. "
                "La salut emocional i física de l'alumne/a és la nostra prioritat absoluta."
            )

        return (
            "Moltes gràcies per estar atent/a i compartir aquesta inquietud. "
            "Acompanyarem aquesta situació amb sensibilitat i professionalitat."
        )
