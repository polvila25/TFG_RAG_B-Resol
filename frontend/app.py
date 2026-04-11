import streamlit as st
import os
from dotenv import load_dotenv
from src.rag.pipeline import RAG

#crear la interfice

#dos columnes per logo i titol
col1, col2 = st.columns([1,5])
with col1:
    st.image('assets/logo_b-resol.png', width=80)

with col2:
    st.title("Asistent RAG b-resol")


if "rag_model" not in st.session_state:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    st.session_state["rag_model"] = RAG(gemini_api_key=GEMINI_API_KEY, gemini_model=GEMINI_MODEL)

if "pdf_path" not in st.session_state:
    st.session_state["pdf_path"] = "data/raw/protocol-actuacio-davant-violencia.pdf"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Haz tu pregunta sobre el protocolo PDF..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                rag = st.session_state["rag_model"]
                pdf_path = st.session_state["pdf_path"]
                response = rag.run(pdf_path, prompt)
            except Exception as e:
                response = f"Error al procesar la consulta: {e}"
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})