from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

class LLMGenerator:
    def __init__(self, gemini_api_key: str, gemini_model: str, prompt_template):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=gemini_api_key,
            model=gemini_model,
            temperature=0.7,
        )
        self.prompt = prompt_template
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate(self, variables: Dict[str, Any]) -> str:
        """
        Generates the LLM response using the dynamically passed variables.
        """
        response = self.chain.invoke(variables)
        return response

    def generate_stream(self, variables: Dict[str, Any]):
        """
        Streams the LLM response. Returns a generator yielding strings.
        """
        for chunk in self.chain.stream(variables):
            if isinstance(chunk, str):
                yield chunk
            elif hasattr(chunk, "content"):
                yield chunk.content
            else:
                yield str(chunk)