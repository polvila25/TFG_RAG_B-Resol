from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser


class LLMGenerator:
    """
    Módulo generador de respuestas.
    Utiliza LCEL y StrOutputParser.
    """

    def __init__(self, gemini_api_key: str, gemini_model: str, prompt):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=0.05,
        )

        self.chain = prompt | self.llm | StrOutputParser()

    def generate(
        self,
        user_query: str,
        answer_context: str,
        query_type: str = "unknown",
        risk_category: str = "unknown",
        retrieval_layer: str = "unknown",
        safety_level: str = "unknown",
    ) -> str:
        response = self.chain.invoke({
            "user_query": user_query,
            "answer_context": answer_context,
            "query_type": query_type,
            "risk_category": risk_category,
            "retrieval_layer": retrieval_layer,
            "safety_level": safety_level,
        })

        return response