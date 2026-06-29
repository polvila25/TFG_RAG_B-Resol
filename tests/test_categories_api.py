import os
import json
import requests
from dotenv import load_dotenv
from src.bresol_context.bresol_intake_analyzer import BRESOL_INTAKE_PROMPT, BRESOL_PHASE_2_CRITERIA
from src.bresol_context.risk_type import BRESOL_RISK_TAXONOMY

load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')

def ask_gemini(prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0}
    }
    res = requests.post(url, json=payload).json()
    try:
        return res['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return str(res)

queries = [
    "Un grup de nens li estan cridant marica cada dia a l'hora del pati, el nen plora.",
    "La Maria m'ha dit que el seu nòvio li controla el mòbil i no la deixa sortir amb nosaltres.",
    "Avui a classe de gimnàstica he vist que la Júlia portava talls als braços recents.",
    "Dos nens s'han barallat avui al pati per una pilota, ha estat una empenta."
]

old_taxonomy = {k: v for k, v in BRESOL_RISK_TAXONOMY.items() if k not in ['conductes_odi_discriminacio', 'violencies_masclistes', 'autolesions']}
if 'falta_greument_perjudicial' in old_taxonomy: old_taxonomy['vandalisme'] = old_taxonomy.pop('falta_greument_perjudicial')
if 'conflicte_convivencia' in old_taxonomy: old_taxonomy['violencia_puntual'] = old_taxonomy.pop('conflicte_convivencia')

print('=== RESULTATS ANTICS (11 categories) ===')
for q in queries:
    prompt = BRESOL_INTAKE_PROMPT.format(
        risk_taxonomy=json.dumps(old_taxonomy, ensure_ascii=False),
        phase_2_criteria=json.dumps(BRESOL_PHASE_2_CRITERIA, ensure_ascii=False),
        user_query=q,
        reporting_mode='identificada'
    )
    res = ask_gemini(prompt)
    try:
        data = json.loads(res.replace('```json', '').replace('```', '').strip())
        print(f'Q: {q}')
        print(f'-> OLD Category: {data.get("risk_category")}')
    except:
        pass

print('\\n=== RESULTATS NOUS (14 categories) ===')
for q in queries:
    prompt = BRESOL_INTAKE_PROMPT.format(
        risk_taxonomy=json.dumps(BRESOL_RISK_TAXONOMY, ensure_ascii=False),
        phase_2_criteria=json.dumps(BRESOL_PHASE_2_CRITERIA, ensure_ascii=False),
        user_query=q,
        reporting_mode='identificada'
    )
    res = ask_gemini(prompt)
    try:
        data = json.loads(res.replace('```json', '').replace('```', '').strip())
        print(f'Q: {q}')
        print(f'-> NEW Category: {data.get("risk_category")}')
    except:
        pass
