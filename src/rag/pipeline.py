import os
from dotenv import load_dotenv
from typing import Optional

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
    # Añadimos type hinting (str) para mayor rigor académico en el código
    def __init__(self, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"):
        self.vectorStore = VectorStore()
        self.pdfloader = PdfLoader()
        self.chunker = Chunker()
        self.prompt = get_prompt()
        self.generator = LLMGenerator(gemini_api_key, gemini_model, self.prompt)

    def run(self, filePath: str, query: str) -> str:
        """
        Ejecuta el pipeline RAG. Si los documentos ya están indexados, salta la lectura del PDF.
        """
        # Comprobamos si el archivo de FAISS ya existe en el disco
        if not os.path.exists("data/vector_store/index.faiss"):
            print("[1/5] 📄 Leyendo el documento PDF por primera vez...")
            docs = self.pdfloader.read_file(filePath)
            
            print("[2/5] ✂️  Fragmentando el texto (Chunking)...")
            list_of_docs = self.chunker.chunk_docs(docs)
            
            print(f"[3/5] 🧠 Indexando y GUARDANDO {len(list_of_docs)} fragmentos en disco...")
            self.vectorStore.add_docs(list_of_docs)
        else:
            print("[1-3/5] ⚡ Base de datos cargada desde disco. Saltando procesamiento del PDF.")

        print("[4/5] 🔍 Buscando información legal relevante...")
        results = self.vectorStore.search_docs(query, k=6)
        
        answer_context = "\n\n".join([
            f"--- PÀGINA {res.metadata.get('page', 0) + 1} ---\n{res.page_content}"
            for res in results
        ])
        
        print("[5/5] 🤖 Generando la respuesta fundamentada con IA...")
        return self.generator.generate(query, answer_context)

def run_app():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Actualizado a gemini-1.5-flash (es más rápido y mejor para RAG actual que gemini-pro)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") 
    
    # Verificación de seguridad antes de arrancar
    if not GEMINI_API_KEY:
        print("❌ ERROR: No se encontró la GEMINI_API_KEY. Revisa tu archivo .env")
        return

    rag = RAG(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)
    filePath = "data/raw/protocol-actuacio-davant-violencia.pdf"
    
    # Prueba enfocada al caso crítico de validación
    query = "Quines mesures d'urgència s'han de prendre si un alumne rep patades diàries i està aterrit?"
    
    try:
        print(f"\n💬 PREGUNTA DEL DOCENT: {query}\n")
        response = rag.run(filePath, query)
        
        print("\n" + "="*50)
        print("=== 🎓 RESPOSTA DE L'ASSISTENT EDUGUARD ===")
        print("="*50)
        print(response)
        print("="*50 + "\n")
        
    except FileNotFoundError:
        print(f"❌ ERROR: No se encuentra el archivo PDF en la ruta: {filePath}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al ejecutar el motor RAG: {e}")

if __name__ == "__main__":
    run_app()