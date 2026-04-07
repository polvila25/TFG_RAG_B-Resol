import os
from dotenv import load_dotenv
from src.ingestion.document_pipeline import PdfLoader, Chunker
from src.rag.retriever import VectorStore
from src.rag.prompt_builder import get_prompt
from src.rag.generator import LLMGenerator

'''
Módulo orquestador principal del sistema RAG.
Define la clase RAG, que coordina la carga, troceado, indexación, búsqueda y generación de respuestas.
Contiene también la función run_app para pruebas o ejecución directa.
'''

class RAG:
    def __init__(self, gemini_api_key, gemini_model="gemini-pro"):
        self.vectorStore = VectorStore()
        self.pdfloader = PdfLoader()
        self.chunker = Chunker()
        self.prompt = get_prompt()
        self.generator = LLMGenerator(gemini_api_key, gemini_model, self.prompt)

    def run(self, filePath, query):
        docs = self.pdfloader.read_file(filePath)
        list_of_docs = self.chunker.chunk_docs(docs)
        self.vectorStore.add_docs(list_of_docs)
        results = self.vectorStore.search_docs(query, k=6)
        answer_context = "\n\n".join([
            f"--- PÁGINA {res.metadata.get('page', 0) + 1} ---\n{res.page_content}"
            for res in results
        ])
        return self.generator.generate(query, answer_context)

def run_app():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    rag = RAG(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)
    filePath = "data/raw/protocol-actuacio-davant-violencia.pdf"
    query = "Cual es la capital de Francia?"
    try:
        print("Cargando el documento y pensando la respuesta...")
        response = rag.run(filePath, query)
        print("\n=== RESPUESTA DEL ASISTENTE ===")
        print(response)
    except Exception as e:
        print(f"Ocurrió un error al ejecutar el RAG: {e}")