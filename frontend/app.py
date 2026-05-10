import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para poder importar 'src'
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
import os
from dotenv import load_dotenv
from src.rag.pipeline_v2 import AdvancedRAGPipeline

# Configuración de la página (opcional pero recomendado)
st.set_page_config(page_title="Assistent B-Resol", page_icon="🛡️")

#crear la interfice

#dos columnes per logo i titol
col1, col2 = st.columns([1,5])
with col1:
    # Usamos try/except por si la imagen no existe en ese path
    try:
        st.image('assets/logo_b-resol.png', width=80)
    except:
        st.write("🛡️")

with col2:
    st.title("Assistent RAG b-resol")


if "rag_model" not in st.session_state:
    with st.spinner("Carregant models de IA (Això pot trigar uns segons la primera vegada)..."):
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        # Usamos gemini-1.5-flash por defecto ya que es más rápido y mejor para RAG
        GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") 
        st.session_state["rag_model"] = AdvancedRAGPipeline(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial del chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input de usuario
if prompt := st.chat_input("Fes la teva consulta sobre els protocols..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Analitzant la consulta i buscant als protocols..."):
            try:
                rag: AdvancedRAGPipeline = st.session_state["rag_model"]
                
                # Llamamos a run() que ahora solo requiere user_query y devuelve un diccionario
                result = rag.run(user_query=prompt)
                response_text = result["answer"]
                
                # Mostramos la respuesta generada
                st.markdown(response_text)
                
                # Añadimos un apartado colapsable para ver la "magia" por debajo (Transparencia RAG)
                with st.expander("👁️ Veure anàlisi i fonts recuperades"):
                    st.write("**Anàlisi de la consulta:**")
                    st.write(f"- Tipus: `{result['analysis'].query_type}`")
                    st.write(f"- Risc: `{result['analysis'].risk_category}`")
                    st.write(f"- Nivell de seguretat: `{result['analysis'].safety_level}`")
                    
                    st.write("**Documents utilitzats:**")
                    for i, chunk in enumerate(result["chunks"], 1):
                        title = chunk.chunk_title or 'Sense títol'
                        source = chunk.source_document or 'Desconegut'
                        page = f" (Pàg. {chunk.source_page})" if chunk.source_page else ""
                        st.caption(f"**{i}. {title}** - {source}{page} [Score: {chunk.score:.2f}]")
                        
            except Exception as e:
                response_text = f"❌ Error en processar la consulta: {e}"
                import traceback
                traceback.print_exc() # Imprime en la consola para facilitar el debug
                st.error(response_text)
                
    st.session_state.messages.append({"role": "assistant", "content": response_text})