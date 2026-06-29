import os
import json
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Afegim el directori arrel al path per poder importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.bresol_context.bresol_intake_analyzer import BresolIntakeAnalyzer
from src.bresol_context.case_information_evaluator import CaseInformationEvaluator

# Diccionari de mapes per les categories
CATEGORY_MAP = {
    "Assetjament escolar (Bullying)": "assetjament_escolar",
    "Ciberassetjament": "ciberassetjament",
    "Conducta suïcida": "conducta_suicida",
    "Autolesions i autoagressió": "autolesions",
    "Violència sexual o Abús": "violencia_sexual",
    "Violències masclistes": "violencies_masclistes",
    "Maltractament infantil": "maltractament_infantil",
    "Trastorns de la conducta alimentària (TCA)": "tca",
    "Conductes d'odi i discriminació": "conductes_odi_discriminacio",
    "Faltes greument perjudicials i vandalisme": "falta_greument_perjudicial",
    "Consum de substàncies": "consum_substancies",
    "Pressió de grup": "pressio_grup",
    "Conflictes de convivència": "conflicte_convivencia",
    "Situació general de convivència": "general"
}

URGENCY_MAP = {
    "Alt": "high",
    "Mitjà": "medium",
    "Baix": "low"
}

def map_missing_info(intake, case_report) -> List[str]:
    mapped = []
    
    # 1. Si no falten paràmetres i s'ha identificat l'agressor
    if len(case_report.missing_parameters) == 0 and intake.aggressor_identified:
        mapped.append("Res, ja tinc tota la informació necessària per obrir protocol complet.")
        return mapped
        
    # 2. Falta identificar autors
    if not intake.aggressor_identified:
        mapped.append("Falta identificar els autors/agressors.")
        
    # Variables faltants detectades internament
    missing_names = [p.parameter_name for p in case_report.missing_parameters]
    
    # 3. Falta persistència
    if any(name in missing_names for name in ["repeticio_temporal", "puntual_o_repetit", "frequencia_o_tipus_consum", "repeticio_o_persistencia"]):
        mapped.append("Falta saber si el fet s'ha repetit en el temps (persistència).")
        
    # 4. Falta lloc
    if any(name in missing_names for name in ["context_del_fet", "lloc_o_context", "canal_digital", "context_o_lloc", "espai_fisic_o_digital", "espai_fisic_digital"]):
        mapped.append("Falta aclarir l'espai físic/digital on ha passat.")
        
    # 5. Falta adult de confiança / seguretat
    if any(name in missing_names for name in ["alumne_acompanyat_o_seguretat_actual", "risc_immediat", "adult_o_desequilibri_poder"]):
        mapped.append("Falta avaluar si la víctima té un adult de confiança o si està fora de perill ara mateix.")
        
    return mapped

def run_evaluation():
    # Carregar configuració
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY no trobada al fitxer .env")
        sys.exit(1)
        
    analyzer = BresolIntakeAnalyzer(gemini_api_key=gemini_api_key, temperature=0.0)
    evaluator = CaseInformationEvaluator()
    
    # Carregar Ground Truth
    json_path = os.path.join(os.path.dirname(__file__), 'prova_prerecuperacio.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
        
    results = []
    
    # Acumuladors de mètriques globals
    category_matches = 0
    urgency_matches = 0
    missing_info_matches = 0
    total_rag_score = 0.0
    total_survey_score = 0.0
    mae_sum = 0.0
    
    total_queries = len(ground_truth)
    
    print(f"Iniciant avaluació de {total_queries} consultes...\n")
    
    for idx, item in enumerate(ground_truth):
        query_id = item["consulta_id"]
        text_consulta = item["text_consulta"]
        tipus_autor = item["tipus_autor"]
        
        # Obtenir dades de l'enquesta (Ground Truth)
        survey_categories = [CATEGORY_MAP.get(cat, "general") for cat in item["categoria_risc"]]
        survey_urgency = URGENCY_MAP.get(item["nivell_urgencia"], "unknown")
        survey_score = float(item["nota_detall"])
        survey_missing_info = item["informacio_falta"]
        
        print(f"[{idx+1}/{total_queries}] Processant alerta ID {query_id}: '{text_consulta[:50]}...'")
        
        try:
            # Inferència del RAG
            intake = analyzer.analyze(text_consulta, tipus_autor)
            case_report = evaluator.evaluate(intake)
            
            rag_category = intake.risk_category
            rag_urgency = intake.urgency_level
            rag_score = case_report.minimum_information_score
            rag_missing_info = map_missing_info(intake, case_report)
            
            # Comprovació de matches
            # Category match si la categoria del RAG està entre les triades a l'enquesta
            cat_match = rag_category in survey_categories
            urg_match = rag_urgency == survey_urgency
            score_diff = abs(rag_score - survey_score)
            
            # Missing info match: si almenys UN dels traduïts pel RAG concorda amb els marcats a l'enquesta
            miss_match = False
            if rag_missing_info:
                for mi in rag_missing_info:
                    if mi in survey_missing_info:
                        miss_match = True
                        break
            
            # Guardar detalls
            case_result = {
                "consulta_id": query_id,
                "text_consulta": text_consulta,
                "ground_truth": {
                    "categories": survey_categories,
                    "urgency": survey_urgency,
                    "score": survey_score,
                    "missing_info": survey_missing_info
                },
                "rag_prediction": {
                    "category": rag_category,
                    "urgency": rag_urgency,
                    "score": rag_score,
                    "missing_info_mapped": rag_missing_info,
                    "raw_missing_parameters": [p.parameter_name for p in case_report.missing_parameters]
                },
                "metrics": {
                    "category_match": cat_match,
                    "urgency_match": urg_match,
                    "missing_info_match": miss_match,
                    "score_mae": score_diff
                }
            }
            results.append(case_result)
            
            # Sumar mètriques
            if cat_match: category_matches += 1
            if urg_match: urgency_matches += 1
            if miss_match: missing_info_matches += 1
            
            total_rag_score += rag_score
            total_survey_score += survey_score
            mae_sum += score_diff
            
            print(f"  -> Categoria RAG: {rag_category} (Match: {cat_match})")
            print(f"  -> Urgència RAG: {rag_urgency} (Match: {urg_match})")
            print(f"  -> Nota Detall RAG: {rag_score} vs Enquesta: {survey_score} (Diferència abs: {score_diff:.1f})")
            print(f"  -> Info Faltant Match: {miss_match}")
            print("-" * 50)
            
        except Exception as e:
            print(f"  [ERROR] Ha fallat la inferència per la consulta ID {query_id}: {str(e)}")
            print("-" * 50)

    # Càlcul de les mètriques agregades globals
    if total_queries > 0:
        cat_accuracy = (category_matches / total_queries) * 100
        urg_accuracy = (urgency_matches / total_queries) * 100
        miss_accuracy = (missing_info_matches / total_queries) * 100
        
        avg_rag_score = total_rag_score / total_queries
        avg_survey_score = total_survey_score / total_queries
        mean_absolute_error = mae_sum / total_queries
        mean_diff = avg_rag_score - avg_survey_score
        
        final_metrics = {
            "total_consultes": total_queries,
            "exactitud_categoria_percent": round(cat_accuracy, 2),
            "exactitud_urgencia_percent": round(urg_accuracy, 2),
            "exactitud_informacio_faltant_percent": round(miss_accuracy, 2),
            "nivell_detall_mitja_rag": round(avg_rag_score, 2),
            "nivell_detall_mitja_enquesta": round(avg_survey_score, 2),
            "nivell_detall_mae": round(mean_absolute_error, 2),
            "nivell_detall_diferencia_mitjanes": round(mean_diff, 2)
        }
        
        print("\n" + "="*50)
        print("MÈTRIQUES FINALS D'AVALUACIÓ")
        print("="*50)
        print(f"Exactitud de Categoria (Top-1): {final_metrics['exactitud_categoria_percent']}%")
        print(f"Exactitud d'Urgència:         {final_metrics['exactitud_urgencia_percent']}%")
        print(f"Exactitud Info Faltant (1+):  {final_metrics['exactitud_informacio_faltant_percent']}%")
        print("-" * 50)
        print("Nivell de Detall:")
        print(f"  Mitjana RAG:              {final_metrics['nivell_detall_mitja_rag']}")
        print(f"  Mitjana Enquesta:         {final_metrics['nivell_detall_mitja_enquesta']}")
        print(f"  Diferència de Mitjanes:   {final_metrics['nivell_detall_diferencia_mitjanes']}")
        print(f"  Error Mitjà Absolut (MAE):{final_metrics['nivell_detall_mae']}")
        print("="*50)
        
        # Desar resultats al JSON
        output_data = {
            "metrics_summary": final_metrics,
            "case_by_case_results": results
        }
        
        output_path = os.path.join(os.path.dirname(__file__), 'results_prerecuperacio.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
        print(f"\nResultats detallats desats a: {output_path}")
    else:
        print("No s'han trobat consultes al fitxer.")

if __name__ == "__main__":
    run_evaluation()
