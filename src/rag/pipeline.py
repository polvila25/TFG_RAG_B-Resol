import os
from dotenv import load_dotenv
from typing import Optional

from src.ingestion.document_pipeline import PdfLoader, Chunker
from src.rag.retriever import VectorStore
from src.rag.prompt_builder import get_prompt
from src.rag.generator import LLMGenerator

'''
Mòdul orquestrador principal del sistema RAG.
Defineix la classe RAG, que coordina la càrrega, fragmentació, indexació, cerca i generació de respostes.
Conté també la funció run_app per a proves.
'''

class RAG:

    def __init__(self, gemini_api_key: str, gemini_model: str = "gemini-1.5-flash"):
        self.vectorStore = VectorStore()
        self.pdfloader = PdfLoader()
        self.chunker = Chunker()
        self.prompt = get_prompt()
        self.generator = LLMGenerator(gemini_api_key, gemini_model, self.prompt)

    def run(self, file_path: str, query: str) -> str:
        """
        Ejecuta el pipeline RAG. Si los documentos ya están indexados, salta la lectura del PDF.
        """
        # Comprovar si el fitxer de FAISS ja existeix
        if not os.path.exists("data/vector_store/index.faiss"):
            print("[1/5] 📄 Llegint el document PDF per primera vegada...")
            docs = self.pdfloader.read_file(file_path)
            
            print("[2/5] ✂️  Fragmentant el text (Chunking)...")
            list_of_docs = self.chunker.chunk_docs(docs)
            
            print(f"[3/5] 🧠 Indexant i DESANT {len(list_of_docs)} fragments al disc...")
            self.vectorStore.add_docs(list_of_docs)
        else:
            print("[1-3/5] ⚡ Base de dades carregada des del disc. Saltant processament del PDF.")

        print("[4/5] 🔍 Cercant informació legal rellevant...")
        results = self.vectorStore.search_docs(query, k=6)
        
        answer_context = "\n\n".join([
            f"--- PÀGINA {res.metadata.get('page', 0) + 1} ---\n{res.page_content}"
            for res in results
        ])
        
        print("[5/5] 🤖 Generant la resposta fonamentada amb IA...")
        return self.generator.generate(query, answer_context)

def run_app():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") 
    
    if not GEMINI_API_KEY:
        print("❌ ERROR: No s'ha trobat la GEMINI_API_KEY. Revisa el teu fitxer .env")
        return

    rag = RAG(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)
    file_path = "data/raw/protocol-actuacio-davant-violencia.pdf"
    
    query = "Quines mesures d'urgència s'han de prendre si un alumne rep patades diàries i està aterrit?"
    
    try:
        print(f"\n💬 PREGUNTA DEL DOCENT: {query}\n")
        response = rag.run(file_path, query)
        
        print("\n" + "="*50)
        print("=== 🎓 RESPOSTA DE L'ASSISTENT EDUGUARD ===")
        print("="*50)
        print(response)
        print("="*50 + "\n")
        
    except FileNotFoundError:
        print(f"❌ ERROR: No s'ha trobat el fitxer PDF a la ruta: {file_path}")
    except Exception as e:
        print(f"❌ S'ha produït un error inesperat en executar el motor RAG: {e}")

if __name__ == "__main__":
    run_app()