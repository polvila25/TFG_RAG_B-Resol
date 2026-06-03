import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para poder importar 'src'
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
import os
import json
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

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial del chat
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            with st.expander("👁️ Veure anàlisi i fonts recuperades"):
                st.markdown(message["metadata"])
                
        # Formulari d'avaluació per a l'últim missatge de l'assistent
        if message["role"] == "assistant" and i == len(st.session_state.messages) - 1:
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
                                
                                worksheet.append_row([
                                    feedback_data["timestamp"],
                                    feedback_data["original_query"],
                                    feedback_data["generated_response"],
                                    feedback_data["predicted_risk_category"],
                                    val_global,
                                    cat_correcta,
                                    cat_suggerida,
                                    gestio_info,
                                    utilitat,
                                    to_adequat,
                                    preguntes_xat,
                                    comentari
                                ])
                            except Exception as gs_err:
                                st.error(f"Error enviant a Google Sheets: {gs_err}")
                                
                                worksheet.append_row([
                                    feedback_data["timestamp"],
                                    feedback_data["original_query"],
                                    feedback_data["generated_response"],
                                    feedback_data["predicted_risk_category"],
                                    val_global,
                                    cat_correcta,
                                    cat_suggerida,
                                    gestio_info,
                                    utilitat,
                                    to_adequat,
                                    preguntes_xat,
                                    comentari
                                ])
                            except Exception as gs_err:
                                st.error(f"Error enviant a Google Sheets: {gs_err}")
                                
                            # --- GUARDAR EN LOCAL (Comentat segons la petició) ---
                            # eval_dir = Path("data/evaluations")
                            # eval_dir.mkdir(parents=True, exist_ok=True)
                            # with open(eval_dir / "feedback_log.jsonl", "a", encoding="utf-8") as f:
                            #     f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
                            
                            # Actualitzar estat per ocultar formulari
                            st.session_state.messages[i]["feedback_submitted"] = True
                            st.success("Valoració enviada correctament. Gràcies per ajudar-nos a millorar!")
                            st.rerun()

# Input de usuario
if prompt := st.chat_input("Fes la teva consulta sobre els protocols..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
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
                    student_metadata=student_metadata_payload
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
                st.session_state.messages.append({
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
                st.session_state.messages.append({"role": "assistant", "content": response_text})