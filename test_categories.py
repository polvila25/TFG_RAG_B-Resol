import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.bresol_context.bresol_intake_analyzer import BRESOL_INTAKE_PROMPT, BRESOL_PHASE_2_CRITERIA
from src.bresol_context.risk_type import BRESOL_RISK_TAXONOMY

load_dotenv()
llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', google_api_key=os.getenv('GEMINI_API_KEY'), temperature=0)
chain = PromptTemplate.from_template(BRESOL_INTAKE_PROMPT) | llm | StrOutputParser()

queries = [
    "Un grup de nens li estan cridant marica cada dia a l'hora del pati, el nen plora.",
    "La Maria m'ha dit que el seu nòvio li controla el mòbil i no la deixa sortir amb nosaltres.",
    "Avui a classe de gimnàstica he vist que la Júlia portava talls als braços recents.",
    "Dos nens s'han barallat avui al pati per una pilota, ha estat una empenta.",
    "Uns nens de 4t han rebentat la porta del bany a cops de peu per fer la gràcia."
]

old_taxonomy = {k: v for k, v in BRESOL_RISK_TAXONOMY.items() if k not in ['conductes_odi_discriminacio', 'violencies_masclistes', 'autolesions']}
if 'falta_greument_perjudicial' in old_taxonomy:
    old_taxonomy['vandalisme'] = old_taxonomy.pop('falta_greument_perjudicial')
if 'conflicte_convivencia' in old_taxonomy:
    old_taxonomy['violencia_puntual'] = old_taxonomy.pop('conflicte_convivencia')

print('--- EXECUTING OLD TAXONOMY ---')
for q in queries:
    try:
        res = chain.invoke({
            'user_query': q,
            'reporting_mode': 'identificada',
            'risk_taxonomy': json.dumps(old_taxonomy, ensure_ascii=False),
            'phase_2_criteria': json.dumps(BRESOL_PHASE_2_CRITERIA, ensure_ascii=False)
        })
        data = json.loads(res.replace('```json', '').replace('```', '').strip())
        print(f"Q: {q}")
        print(f"Old Category: {data.get('risk_category')}")
    except Exception as e:
        print(f"Q: {q} -> ERROR: {e}")

print('\\n--- EXECUTING NEW TAXONOMY ---')
for q in queries:
    try:
        res = chain.invoke({
            'user_query': q,
            'reporting_mode': 'identificada',
            'risk_taxonomy': json.dumps(BRESOL_RISK_TAXONOMY, ensure_ascii=False),
            'phase_2_criteria': json.dumps(BRESOL_PHASE_2_CRITERIA, ensure_ascii=False)
        })
        data = json.loads(res.replace('```json', '').replace('```', '').strip())
        print(f"Q: {q}")
        print(f"New Category: {data.get('risk_category')}")
    except Exception as e:
        print(f"Q: {q} -> ERROR: {e}")
