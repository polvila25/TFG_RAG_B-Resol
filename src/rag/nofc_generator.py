import time
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.privacy.anonymizer import Anonymizer

NOFC_SYSTEM_PROMPT = """
Ets un assistent expert de la plataforma b-resol, especialitzat EXCLUSIVAMENT en la Normativa d'Organització i Funcionament del Centre (NOFC) que t'han proporcionat.

El teu objectiu és respondre als dubtes del docent sobre les normes, protocols interns, deures, drets i sancions específiques que dicti el document NOFC del centre educatiu.

DOCUMENT NOFC DEL CENTRE:
==================================================
{nofc_text}
==================================================

HISTORIAL DE LA CONVERSA ANTERIOR:
{history_context}

CONSULTA DEL DOCENT: {user_query}

REGLES D'OR OBLIGATÒRIES:
1. EXCLUSIVITAT: Respon ÚNICAMENT basant-te en la informació que apareix literalment o conceptualment al document NOFC proporcionat adalt.
2. NO INVENTIS NORMES: Si la resposta no es troba al document NOFC, indica clarament: "Aquesta informació no es troba detallada al document NOFC del centre que has pujat."
3. CITACIÓ: Fes referència a "segons la normativa interna del centre", "segons el document NOFC pujat", etc. 
4. PRIVACITAT: No facis preguntes investigadores sobre alumnes. Evita emetre judicis sobre alumnes concrets.
5. TO I FORMAT: Escriu en català amb un to formal, informatiu, directe i professional. Pots fer servir bullet points per organitzar la resposta si hi ha múltiples punts.

Has de començar SEMPRE la teva resposta (a la primera línia) exactament amb aquesta frase en català: "Aquest és un xat especialitzat per consultar la NOFC del centre. La resposta es basa únicament en el document carregat." Afegeix un salt de línia doble just després d'aquesta frase abans de començar la teva resposta.
"""

class NOFCGenerator:
    def __init__(self, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=0.2, # Temperatura baixa perquè la resposta sigui molt fidel al text del PDF
        )
        self.prompt = PromptTemplate.from_template(NOFC_SYSTEM_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.anonymizer = Anonymizer()

    def run(self, user_query: str, nofc_text: str, chat_history: List[Dict[str, str]] = None) -> str:
        print("="*60)
        print("INICIANT CONSULTA NOFC DIRECTA (SENSE RAG)")
        
        # 1. Anonimitzar query
        print("      - Anonimitzant consulta per seguretat...")
        anonymized_query = self.anonymizer.anonymize(user_query)
        
        # 2. Formatejar historial
        history_context = ""
        if chat_history:
            anonymized_history = self.anonymizer.anonymize_chat_history(chat_history[-6:])
            for msg in anonymized_history:
                role = "Docent" if msg["role"] == "user" else "Assistent NOFC"
                content = msg["content"]
                # Netejar frase introductòria de l'historial
                if content.startswith("Aquest és un xat especialitzat"):
                    parts = content.split("\n\n", 1)
                    if len(parts) > 1:
                        content = parts[1]
                history_context += f"- {role}: {content}\n"
        
        if not history_context:
            history_context = "Cap historial previ."
            
        print("      - Generant resposta llegint el document complet...")
        t0 = time.time()
        
        # 3. Invocar LLM amb tota la informació
        variables = {
            "nofc_text": nofc_text,
            "history_context": history_context,
            "user_query": anonymized_query
        }
        
        answer = self.chain.invoke(variables)
        
        # 4. Des-anonimitzar resposta final
        final_answer = self.anonymizer.deanonymize(answer)
        
        t_gen = time.time() - t0
        print(f"CONSULTA NOFC FINALITZADA en {t_gen:.3f}s")
        print("="*60)
        
        return final_answer
