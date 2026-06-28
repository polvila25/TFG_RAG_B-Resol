import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Carregar entorn abans de qualsevol altre import per assegurar que tenim la API KEY
load_dotenv(override=True)

from src.rag.pipeline_v2 import AdvancedRAGPipeline

def load_test_cases(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_metrics(results):
    total = len(results)
    if total == 0:
        return {}
        
    correct_risk = sum(1 for r in results if r["expected"]["risk_category"] == r["actual"]["risk_category"])
    correct_urgency = sum(1 for r in results if r["expected"]["urgency_level"] == r["actual"]["urgency_level"])
    correct_routing = sum(1 for r in results if r["expected"]["response_type"] == r["actual"]["response_type"])
    
    # Recall de seguretat (Must Contain)
    total_must_contain = 0
    met_must_contain = 0
    
    # Precisió de seguretat (Must Not Contain)
    total_must_not_contain = 0
    met_must_not_contain = 0
    
    for r in results:
        actual_text = r["actual"]["answer"].lower()
        
        # Must contain
        for kw in r["expected"]["must_contain"]:
            total_must_contain += 1
            if kw.lower() in actual_text:
                met_must_contain += 1
                
        # Must not contain
        for kw in r["expected"]["must_not_contain"]:
            total_must_not_contain += 1
            if kw.lower() not in actual_text:
                met_must_not_contain += 1
                
    return {
        "total_cases": total,
        "accuracy_risk": (correct_risk / total) * 100,
        "accuracy_urgency": (correct_urgency / total) * 100,
        "accuracy_routing": (correct_routing / total) * 100,
        "recall_security": (met_must_contain / total_must_contain) * 100 if total_must_contain > 0 else 100.0,
        "precision_security": (met_must_not_contain / total_must_not_contain) * 100 if total_must_not_contain > 0 else 100.0
    }

def main():
    print("🚀 Iniciant Avaluació Automatitzada (Test Suite B-Resol)")
    
    # Rutas absolutas
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data" / "evaluations"
    test_file = data_dir / "test_cases.json"
    output_file = data_dir / "eval_results.json"
    
    if not test_file.exists():
        print(f"❌ No s'ha trobat el fitxer de proves: {test_file}")
        return
        
    test_cases = load_test_cases(test_file)
    print(f"📋 Carregats {len(test_cases)} casos de prova.")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no trobada a l'entorn.")
        return
        
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"⏳ Inicialitzant l'AdvancedRAGPipeline (Model: {GEMINI_MODEL})...")
    pipeline = AdvancedRAGPipeline(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)
    
    evaluation_results = []
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Avaluant: {tc['id']}")
        print(f"Query: {tc['query'][:60]}...")
        
        t0 = time.time()
        try:
            # Inhibim prints innecessaris per netejar la consola
            result = pipeline.run(
                user_query=tc["query"],
                reporting_mode=tc["reporting_mode"],
                student_metadata={},
                skip_generation=True
            )
            
            actual = {
                "risk_category": result["bresol_intake"].risk_category,
                "urgency_level": result["bresol_intake"].urgency_level,
                "response_type": result["response_plan"].response_type,
                "answer": result["answer"]
            }
            
            status_risk = "✅" if actual["risk_category"] == tc["expected"]["risk_category"] else f"❌ (Era: {tc['expected']['risk_category']}, Trobada: {actual['risk_category']})"
            print(f"Risc: {status_risk}")
            
            evaluation_results.append({
                "id": tc["id"],
                "query": tc["query"],
                "expected": tc["expected"],
                "actual": actual,
                "time_seconds": time.time() - t0,
                "error": None
            })
            
        except Exception as e:
            print(f"❌ Error processant {tc['id']}: {e}")
            evaluation_results.append({
                "id": tc["id"],
                "error": str(e)
            })
            
    print("\n" + "="*50)
    print("📊 RESULTATS DE L'AVALUACIÓ")
    print("="*50)
    
    valid_results = [r for r in evaluation_results if not r.get("error")]
    metrics = calculate_metrics(valid_results)
    
    if metrics:
        print(f"Casos avaluats: {metrics['total_cases']}")
        print(f"Accuracy Risc:       {metrics['accuracy_risk']:.1f}%")
        print(f"Accuracy Urgència:   {metrics['accuracy_urgency']:.1f}%")
        print(f"Accuracy Routing:    {metrics['accuracy_routing']:.1f}%")
        print(f"Recall Seguretat:    {metrics['recall_security']:.1f}%")
        print(f"Precisió Seguretat:  {metrics['precision_security']:.1f}%")
        
        print("\n" + "-"*50)
        print("❌ ERRORS DE CLASSIFICACIÓ DE RISC")
        print("-"*50)
        errors_found = False
        for r in valid_results:
            expected_risk = r["expected"]["risk_category"]
            actual_risk = r["actual"]["risk_category"]
            if expected_risk != actual_risk:
                errors_found = True
                print(f"Consulta: \"{r['query']}\"")
                print(f"  -> Esperat:   {expected_risk}")
                print(f"  -> Predicció: {actual_risk}\n")
        
        if not errors_found:
            print("  ✨ Cap error! Totes les classificacions són correctes.")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "metrics": metrics,
                "results": evaluation_results
            }, f, indent=2, ensure_ascii=False)
            
        print(f"\n💾 Informe detallat desat a {output_file}")
    else:
        print("❌ No s'han pogut calcular les mètriques (cap cas avaluat amb èxit).")

if __name__ == "__main__":
    main()
