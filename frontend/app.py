import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para poder importar 'src'
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
import os
import json
import uuid
from datetime import datetime
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

# Selector de modo de informe en la barra lateral
with st.sidebar:
    st.header("🗂️ Gestió d'Alertes")
    
    # Manejo de chats
    if "chats" not in st.session_state:
        first_id = str(uuid.uuid4())
        st.session_state.chats = {
            first_id: {"name": "Alerta 1", "messages": []}
        }
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
        
    chat_keys = list(st.session_state.chats.keys())
    
    # Render chats en el sidebar
    for c_id in chat_keys:
        c_name = st.session_state.chats[c_id]["name"]
        
        col_btn, col_edit, col_del = st.columns([7, 1.5, 1.5], gap="small")
        with col_btn:
            is_current = (c_id == st.session_state.current_chat_id)
            # Usar un pequeño indicador o negrita si es el actual
            btn_label = f"🟢 {c_name}" if is_current else f"⚪ {c_name}"
            if st.button(btn_label, key=f"sel_{c_id}", use_container_width=True):
                st.session_state.current_chat_id = c_id
                st.rerun()
        with col_edit:
            if st.button("✏️", key=f"edit_{c_id}", help="Canviar nom de l'alerta"):
                st.session_state[f"editing_{c_id}"] = not st.session_state.get(f"editing_{c_id}", False)
                st.rerun()
        with col_del:
            # Només es pot esborrar si hi ha més d'1 xat
            if len(chat_keys) > 1:
                if st.button("🗑️", key=f"del_{c_id}", help="Esborrar l'alerta"):
                    del st.session_state.chats[c_id]
                    if st.session_state.current_chat_id == c_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()
            else:
                st.button("🗑️", key=f"del_{c_id}", disabled=True)
                
        # Mostrar input per editar el nom
        if st.session_state.get(f"editing_{c_id}", False):
            new_name = st.text_input("Nou nom:", value=c_name, key=f"input_{c_id}")
            if st.button("Guardar nom", key=f"save_{c_id}"):
                if new_name.strip():
                    st.session_state.chats[c_id]["name"] = new_name.strip()
                st.session_state[f"editing_{c_id}"] = False
                st.rerun()

    st.markdown("---")
    
    if len(chat_keys) < 3:
        if st.button("➕ Nova Alerta", use_container_width=True):
            new_id = str(uuid.uuid4())
            # Cercar el número màxim per no repetir noms per defecte
            next_num = len(chat_keys) + 1
            st.session_state.chats[new_id] = {"name": f"Alerta {next_num}", "messages": []}
            st.session_state.current_chat_id = new_id
            st.rerun()
    else:
        st.info("Límit de 3 alertes simultànies assolit.")
        
    st.markdown("---")

    st.header("Configuració de l'Alerta")
    reporting_mode_selected = st.radio(
        "Tipus de comunicació:",
        options=["anonymous", "identified"],
        index=1, # Identificada por defecto
        format_func=lambda x: "👥 Anònima" if x == "anonymous" else "👤 Identificada",
        help="Defineix si la persona alertant vol mantenir el seu anonimat o identificar-se."
    )
    
    student_metadata_payload = {}
    if reporting_mode_selected == "identified":
        st.markdown("---")
        st.subheader("Dades de l'alumne implicat")
        
        curs_opciones = [
            "No especificat", 
            "Primer de Primària", "Segon de Primària", "Tercer de Primària", 
            "Quart de Primària", "Cinquè de Primària", "Sisè de Primària",
            "Primer d'ESO", "Segon d'ESO", "Tercer d'ESO", "Quart d'ESO",
            "Primer de Batxillerat", "Segon de Batxillerat"
        ]
        curs_selected = st.selectbox(
            "Curs escolar:",
            options=curs_opciones,
            index=0,
            help="Selecciona el curs de l'alumne implicat."
        )
        
        sexe_selected = st.selectbox(
            "Sexe:",
            options=["No especificat", "Masculí", "Femení"],
            index=0,
            help="Selecciona el sexe de l'alumne implicat."
        )
        
        rol_selected = st.selectbox(
            "Rol a l'incident:",
            options=["No especificat", "Víctima", "Agressor", "Observador"],
            index=0,
            help="El rol que té l'alumne a la situació."
        )
        
        student_metadata_payload = {
            "curs": curs_selected,
            "sexe": sexe_selected,
            "rol": rol_selected
        }
        
    st.markdown("---")
    st.markdown("""
    **Sobre l'Assistent b-resol**
    Aquest assistent utilitza intel·ligència artificial i cerca RAG per ajudar a gestionar alertes de convivència escolar i benestar emocional, seguint els protocols oficials.
    """)

if "chats" not in st.session_state:
    first_id = str(uuid.uuid4())
    st.session_state.chats = {
        first_id: {"name": "Alerta 1", "messages": []}
    }
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

current_chat = st.session_state.chats[st.session_state.current_chat_id]

# Avís explícit
st.info("⚠️ **Avís:** Per garantir la qualitat de l'anàlisi, aquesta conversa s'ha de centrar exclusivament en aquesta alerta. Si vols parlar d'un altre cas, si us plau, obre o selecciona un altre xat al menú lateral.")

# Mostrar el historial del chat
for i, message in enumerate(current_chat["messages"]):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            with st.expander("👁️ Veure anàlisi i fonts recuperades"):
                st.markdown(message["metadata"])
                
        # Formulari d'avaluació per a l'últim missatge de l'assistent
        if message["role"] == "assistant" and i == len(current_chat["messages"]) - 1:
            if not message.get("feedback_submitted", False) and "original_query" in message:
                with st.expander("📝 Avaluar aquesta resposta (Opcional)", expanded=False):
                    with st.form(key=f"feedback_form_{i}"):
                        st.markdown("### Avaluació de la resposta")
                        
                        val_global = st.slider("1. Valoració global de la resposta:", 1, 10, 5)
                        
                        cat_correcta = st.radio(
                            f"2. La categoria de risc detectada ({message.get('risk_category', 'Desconeguda')}) és correcta?",
                            ["Sí", "Parcialment", "No", "No ho sé"]
                        )
                        
                        cat_suggerida = st.selectbox(
                            "3. Si no és correcta, quina categoria hauria de ser?",
                            ["Selecciona una opció...", "conducta_suicida", "violencia_sexual", "tca", "assetjament_escolar", "ciberassetjament", "maltractament_infantil", "consum_substancies", "vandalisme", "general"],
                            index=0
                        )
                        
                        gestio_info = st.radio(
                            "4. El sistema ha gestionat bé el nivell d'informació disponible?",
                            [
                                "Sí, ha respost directament correctament",
                                "Sí, ha demanat més informació quan calia",
                                "Parcialment",
                                "No, ha respost massa aviat",
                                "No, ha demanat informació innecessària"
                            ]
                        )
                        
                        utilitat = st.slider("5. La resposta és útil per al docent?", 1, 10, 5)
                        to_adequat = st.slider("6. El to és adequat per a una situació sensible amb menors?", 1, 10, 5)
                        
                        preguntes_xat = st.radio(
                            "7. Les preguntes proposades pel xat b-resol són adequades?",
                            ["Sí", "Parcialment", "No", "No aplica"]
                        )
                        
                        comentari = st.text_area("8. Comentari o millora suggerida:")
                        
                        submit_button = st.form_submit_button("Enviar valoració")
                    
                        if submit_button:
                            feedback_data = {
                                "timestamp": datetime.now().isoformat(),
                                "original_query": message["original_query"],
                                "generated_response": message["content"],
                                "predicted_risk_category": message.get("risk_category", ""),
                                "feedback": {
                                    "valoracio_global": val_global,
                                    "categoria_correcta": cat_correcta,
                                    "categoria_suggerida": cat_suggerida if cat_suggerida != "Selecciona una opció..." else None,
                                    "gestio_informacio": gestio_info,
                                    "utilitat": utilitat,
                                    "to_adequat": to_adequat,
                                    "preguntes_xat": preguntes_xat,
                                    "comentari": comentari
                                }
                            }
                            
                            # --- GUARDAR EN LOCAL (Mecanisme de seguretat / Fallback) ---
                            try:
                                eval_dir = Path("data/evaluations")
                                eval_dir.mkdir(parents=True, exist_ok=True)
                                with open(eval_dir / "feedback_log.jsonl", "a", encoding="utf-8") as f:
                                    f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
                            except Exception as local_err:
                                st.error(f"Error guardant valoració en local: {local_err}")

                            # --- GUARDAR EN GOOGLE SHEETS ---
                            try:
                                import gspread
                                import os
                                
                                # Comprovem si estem en local (el fitxer existeix) o al núvol (fem servir secrets)
                                if os.path.exists("avaluacion-tfg-bresol-key.json"):
                                    # Entorn Local
                                    gc = gspread.service_account(filename="avaluacion-tfg-bresol-key.json")
                                else:
                                    # Entorn Streamlit Cloud
                                    # Converteix els secrets de Streamlit a un diccionari que entén Google
                                    credentials_dict = dict(st.secrets["gcp_service_account"])
                                    gc = gspread.service_account_from_dict(credentials_dict)
                                    
                                # Obrim l'Excel
                                sh = gc.open("B-Resol Feedback") 
                                worksheet = sh.sheet1
                                
                                # Truncar strings llargs per evitar límits de Google Sheets (50,000 chars per cel·la)
                                # Posem el límit a 4000 caràcters per seguretat i claredat.
                                query_str = str(feedback_data["original_query"])[:4000]
                                response_str = str(feedback_data["generated_response"])[:4000]
                                comment_str = str(comentari)[:4000] if comentari else ""
                                
                                worksheet.append_row([
                                    feedback_data["timestamp"],
                                    query_str,
                                    response_str,
                                    str(feedback_data["predicted_risk_category"]),
                                    str(val_global),
                                    str(cat_correcta),
                                    str(cat_suggerida) if cat_suggerida else "",
                                    str(gestio_info),
                                    str(utilitat),
                                    str(to_adequat),
                                    str(preguntes_xat),
                                    comment_str
                                ])
                            except Exception as gs_err:
                                st.warning(f"Avís: Error de connexió a Google Sheets ({gs_err}). La teva valoració s'ha guardat igualment de forma segura en local.")
                            
                            # Actualitzar estat per ocultar formulari
                            current_chat["messages"][i]["feedback_submitted"] = True
                            st.success("Valoració enviada correctament. Gràcies per ajudar-nos a millorar!")
                            st.rerun()

# Input de usuario
if prompt := st.chat_input("Fes la teva consulta sobre els protocols..."):
    current_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Analitzant la consulta i buscant als protocols..."):
            try:
                rag: AdvancedRAGPipeline = st.session_state["rag_model"]
                
                # Llamamos a run() que ara retorna el resultat final sencer
                result = rag.run(
                    user_query=prompt, 
                    reporting_mode=reporting_mode_selected, 
                    student_metadata=student_metadata_payload,
                    chat_history=current_chat["messages"][:-1]
                )
                response_text = result["answer"]
                
                # Mostramos la respuesta generada
                st.markdown(response_text)
                
                # Crear metadatos para guardar en el historial
                reporting_mode_map = {
                    "anonymous": "Anònima 👥",
                    "identified": "Identificada 👤",
                    "unknown": "Desconeguda ❓"
                }
                rep_mode = reporting_mode_map.get(result['bresol_intake'].reporting_mode, "Desconeguda ❓")
                
                metadata_md = f"**Anàlisi de la consulta:**\n"
                metadata_md += f"- Tipus: `{result['analysis'].query_type}`\n"
                metadata_md += f"- Risc: `{result['analysis'].risk_category}`\n"
                metadata_md += f"- Nivell de seguretat: `{result['analysis'].safety_level}`\n"
                metadata_md += f"- Mode de l'alerta: `{rep_mode}`\n"
                if result['bresol_intake'].reporting_mode == "identified" and student_metadata_payload:
                    meta_list = []
                    for k, v in student_metadata_payload.items():
                        if v and v != "No especificat":
                            meta_list.append(f"{k.capitalize()}: `{v}`")
                    if meta_list:
                        metadata_md += f"  - **Metadades:** " + ", ".join(meta_list) + "\n"
                metadata_md += f"- Puntuació d'informació: `{result['case_report'].minimum_information_score}/10`\n\n"
                
                metadata_md += "**Documents utilitzats:**\n"
                for i, chunk in enumerate(result["chunks"], 1):
                    title = chunk.chunk_title or 'Sense títol'
                    source = chunk.source_document or 'Desconegut'
                    page = f" (Pàg. {chunk.source_page})" if chunk.source_page else ""
                    metadata_md += f"{i}. **{title}** - {source}{page} [Score: {chunk.score:.2f}]\n"
                
                # Mostrar el expander en el mensaje actual
                with st.expander("👁️ Veure anàlisi i fonts recuperades"):
                    st.markdown(metadata_md)
                
                # Guardar el mensaje junto con sus metadatos en el historial
                current_chat["messages"].append({
                    "role": "assistant", 
                    "content": response_text,
                    "metadata": metadata_md,
                    "original_query": prompt,
                    "risk_category": result['analysis'].risk_category,
                    "feedback_submitted": False
                })
                st.rerun()
                        
            except Exception as e:
                response_text = f"❌ Error en processar la consulta: {e}"
                import traceback
                traceback.print_exc() # Imprime en la consola para facilitar el debug
                st.error(response_text)
                current_chat["messages"].append({"role": "assistant", "content": response_text})