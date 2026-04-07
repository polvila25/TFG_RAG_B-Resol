from langchain_google_genai import ChatGoogleGenerativeAI

'''
Módulo generador de respuestas.
Contiene la clase LLMGenerator, que recibe el contexto y la pregunta, llama al modelo LLM y procesa la respuesta.
'''

class LLMGenerator:
    def __init__(self, gemini_api_key, gemini_model, prompt):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=0.05
        )
        self.prompt = prompt

    def generate(self, user_query, answer_context):
        chain = self.prompt | self.llm
        response = chain.invoke({
            "user_query": user_query,
            "answer_context": answer_context,
        })
        # Procesar la respuesta como en tu código original
        if hasattr(response, "content"):
            content = response.content
        else:
            content = response
        if isinstance(content, list):
            text = "\n".join([c["text"] for c in content if "text" in c])
        elif isinstance(content, dict) and "text" in content:
            text = content["text"]
        else:
            text = str(content)
        return text