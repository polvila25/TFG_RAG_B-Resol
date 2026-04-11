from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

'''
Módulo generador de respuestas optimizado.
Utiliza LCEL (LangChain Expression Language) y StrOutputParser.
'''

class LLMGenerator:
    def __init__(self, gemini_api_key, gemini_model, prompt):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=0.05
        )
        # Creem la pipeline (cadena) combinant el prompt, el LLM i el parser de text
        self.chain = prompt | self.llm | StrOutputParser()

    def generate(self, user_query, answer_context):
        # La invocació retorna directament una cadena de text neta
        response = self.chain.invoke({
            "user_query": user_query,
            "answer_context": answer_context,
        })
        return response