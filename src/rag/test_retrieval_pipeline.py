import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Añadir la raíz del proyecto al sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from src.rag.pipeline_v2 import AdvancedRAGPipeline

def test_pipeline():
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        print("ERROR: No se encontró la GEMINI_API_KEY en el entorno.")
        return

    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    print("Construyendo Pipeline RAG v2...")
    pipeline = AdvancedRAGPipeline(gemini_api_key=gemini_api_key, gemini_model=gemini_model)
    
    # Consulta de prueba: Mixta (práctica + legal) sobre assetjament
    query = "¿Quin és el circuit d'actuació i la normativa aplicable si detectem un possible cas de bullying físic i reiterat al pati?"
    
    try:
        result = pipeline.run(user_query=query)
        pipeline.retriever.close()
        
        print("\n" + "="*80)
        print("RESPOSTA FINAL DEL LLM:")
        print("="*80)
        print(result["answer"])
        print("="*80)
        
    except Exception as e:
        print(f"\n Ha ocurrido un error en la ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
