import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Afegir la arrel del projecte al sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from src.rag.rag_pipeline import AdvancedRAGPipeline


def run_test_case(pipeline: AdvancedRAGPipeline, description: str, query: str):
    print("\n" + "="*80)
    print(f"TEST CASE: {description}")
    print(f"Query: '{query}'")
    print("="*80)
    
    result = pipeline.run(user_query=query)
    
    print("\n=== ANÀLISI DETALLAT ===")
    print(f"• Categoria de risc: {result['bresol_intake'].risk_category}")
    print(f"• Reporting mode: {result['bresol_intake'].reporting_mode}")
    print(f"• Victim identified: {result['bresol_intake'].victim_identified}")
    print(f"• Minimum Information Score: {result['case_report'].minimum_information_score}/10")
    print(f"• Response Type: {result['response_plan'].response_type}")
    print(f"• Should Run Documental RAG: {result['response_plan'].should_run_documental_rag}")
    
    print("\n=== RECOMANACIONS DE CONVIVÈNCIA ===")
    print(f"• Empathy Statement: {result['teacher_guidance'].empathy_statement}")
    print("• Recommended Questions:")
    for q in result['teacher_guidance'].recommended_questions:
        print(f"  - {q}")
    print("• Avoid Questions:")
    for q in result['teacher_guidance'].avoid_questions:
        print(f"  - {q}")
        
    print("\n=== RESPOSTA GENERADA PEL LLM ===")
    print(result['answer'])
    print("="*80 + "\n")


def main():
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("ERROR: No s'ha trobat la GEMINI_API_KEY a l'entorn.")
        return

    # Use user chosen model
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    print("Inicialitzant pipeline RAG v2 amb triatge intel·ligent...")
    pipeline = AdvancedRAGPipeline(gemini_api_key=gemini_api_key, gemini_model=gemini_model)
    
    cases = [
        ("Cas 1: Alerta amb molt poca informació", "Crec que hi ha un problema amb un alumne."),
        ("Cas 2: Ciberassetjament / Assetjament sense identitat explícita", "No sé qui és, però al pati a l'hora de l'esmorzar sempre insulten un alumne de 1r ESO."),
        ("Cas 3: Cas robust per a protocol", "He parlat amb l'alumne. Té 13 anys. Porten dos mesos insultant-lo."),
        ("Cas 4: Risc Vital / Urgència (Art. 16 LOPIVI)", "Un alumne diu que no vol viure."),
        ("Cas 5: Consulta purament normativa (Legal support)", "Quina normativa regula l'assetjament?")
    ]

    for desc, query in cases:
        run_test_case(pipeline, desc, query)


if __name__ == "__main__":
    main()
