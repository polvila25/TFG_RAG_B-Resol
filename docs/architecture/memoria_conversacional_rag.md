# Documentació de Disseny: Memòria Conversacional i Condensació de Consultes (Conversational RAG)

Aquest document detalla la solució implementada per resoldre el problema de pèrdua del fil de conversa al motor RAG de **b-resol**. S'explica el diagnòstic del problema, la solució arquitectònica triada, els detalls de la implementació als fitxers de codi i exemples pràctics.

---

## 1. El Problema: RAG Sense Estat (Stateless)

En les proves inicials i reunions de revisió, es va detectar que en realitzar 2 o 3 consultes seguides, el sistema perdia el fil i responia de manera genèrica o incompleta.

### Diagnòstic Tècnic:
L'arquitectura RAG inicial operava de manera **"stateless"** (sense estat). Cada consulta del docent es processava com un fet aïllat i independent:
* Si la primera consulta era: *"Tinc un alumne de 4t d'ESO que pateix insults diaris al pati per part d'uns companys."*, el sistema analitzava el cas correctament, extreia el risc `assetjament_escolar` i proposava les mesures adequades.
* Si la segona consulta (de seguiment) era: *"Qui s'ha d'encarrega d'aplicar aquestes mesures?"*, el pipeline rebia només el text *"Qui s'ha d'encarrega d'aplicar aquestes mesures?"*.
* Al no tenir context del missatge anterior, el **Motor de Triatge (`QueryAnalyzer`)** no detectava cap risc de bullying, cap edat, ni cap víctima. Per tant, determinava que la informació era insuficient (`minimum_information_score <= 3`) i forçava el prompt preventiu de conversa de xat, o bé recuperava informació errònia de Qdrant.

---

## 2. La Solució: Condensació de Consultes (Query Condensation)

Per solucionar aquest problema, s'ha integrat un patró de disseny de **RAG Conversacional** basat en la **Resolució de Coreferències**. Aquest procés transforma qualsevol pregunta de seguiment en una pregunta independent (*standalone query*) que conté de manera explícita tot el context necessari de la conversa anterior abans de passar pel triatge i la cerca semàntica.

### Flux de Dades amb Memòria:

```
[Nova Consulta de Seguiment] + [Historial del Xat]
                     │
                     ▼
        (LLM de Condensació a Temp 0.0)
                     │
                     ▼
          [Consulta Independent] (Standalone Query)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   [Motor de Triatge]     [Enriquiment i Cerca]
(Extrau Risc i Urgència)     (Query Vectorial)
         │                       │
         └───────────┬───────────┘
                     ▼
     [Generador Final (Amb Historial)]
                     │
                     ▼
     [Resposta Coherent i Continuada]
```

---

## 3. Implementació del Codi

La solució s'ha distribuït entre el pipeline de processament back-end de la IA i la gestió d'estats del xat al front-end.

### A. Back-End: [src/rag/rag_pipeline.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/rag/rag_pipeline.py)

#### 1. Mètode de Condensació (`_condense_query`):
S'ha afegit un mètode privat a la classe `AdvancedRAGPipeline` encarregat d'interactuar amb Gemini per reescriure la consulta si hi ha historial de xat.

```python
def _condense_query(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
    if not chat_history:
        return user_query

    # Construïm el format de text de l'historial (Últims 6 missatges)
    history_text = ""
    for msg in chat_history[-6:]:
        role = "Usuari" if msg["role"] == "user" else "Assistent"
        content = msg["content"]
        # Limitem per evitar saturar la finestra de context del model
        if len(content) > 300:
            content = content[:300] + "..."
        history_text += f"{role}: {content}\n"

    condense_prompt = f"""
Ets un assistent expert que reformula preguntes per a un sistema RAG de convivència escolar.
Donada la següent conversa i una pregunta de seguiment de l'usuari, reformula-la per a que sigui una pregunta independent (standalone question) en català, que contingui tot el context necessari de la conversa anterior.
No responguis a la pregunta, només reformula-la de manera concisa i directa. Si la pregunta de seguiment ja és independent o la conversa està buida, retorna-la tal qual.

Conversa anterior:
{{history_text}}

Pregunta de seguiment: {{user_query}}

Pregunta independent en català:"""

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            google_api_key=self.gemini_api_key,
            model=self.gemini_model,
            temperature=0.0 # Temperatura a 0.0 per evitar al·lucinacions
        )
        res = llm.invoke(condense_prompt)
        condensed = res.content.strip()
        if condensed.startswith('"') and condensed.endswith('"'):
            condensed = condensed[1:-1]
        print(f"      [Condense] Query original: '{{user_query}}' -> Standalone: '{{condensed}}'")
        return condensed
    except Exception as e:
        print(f"      [Condense] Error al condensar query: {{e}}. Usant original.")
        return user_query
```

#### 2. Modificació del Mètode `run`:
* S'ha actualitzat la firma del mètode per admetre `chat_history`:
  ```python
  def run(self, user_query: str, reporting_mode: str = "identified", student_metadata: dict = None, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
  ```
* Es calcula la `active_query` executant la condensació: `active_query = self._condense_query(user_query, chat_history)`.
* S'utilitza aquesta `active_query` per a les fases de **Bresol Intake**, **Query Intent Analysis** i **Recuperació semàntica a Qdrant**.
* S'injecta l'historial estructurat en format text (`history_context`) al prompt del generador final sota la variable `user_query` per assegurar que l'LLM conegui la seqüència cronològica:
  ```python
  "user_query": f"{history_context}{user_query}"
  ```

---

### B. Front-End: [frontend/app.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/frontend/app.py)

Al costat del client, cal enviar l'historial que Streamlit emmagatzema a `st.session_state.messages`.
* Es passa l'historial a la crida del pipeline de RAG excloent l'últim missatge afegit (que és la pròpia consulta en brut que s'està enviant en aquell instant):
  ```python
  result = rag.run(
      user_query=prompt, 
      reporting_mode=reporting_mode_selected, 
      student_metadata=student_metadata_payload,
      chat_history=st.session_state.messages[:-1] # Exclou l'últim per evitar bucle
  )
  ```

---

## 4. Exemple de Comportament (Abans vs. Després)

### Missatge 1:
* **Usuari:** *"Tinc sospites que un noi de 1r d'ESO pateix insults homòfobs al pati."*
* **RAG (Comú):** Activa el protocol d'odi i discriminació. Recupera el protocol de la Generalitat i aconsella obrir comissió i fer l'acompanyament.

### Missatge 2 (Pregunta de seguiment):
* **Usuari:** *"Com he de fer l'acompanyament?"*

| Comportament Antic (RAG Stateless) | Comportament Nou (RAG Conversacional) |
| :--- | :--- |
| El RAG processa només: *"Com he de fer l'acompanyament?"*. | El LLM de condensació llegeix el xat anterior i la pregunta actual. |
| El triatge de risc assigna categoria `"general"` perquè no sap qui pateix la situació ni de quin tipus de fet es tracta. | Genera la consulta independent: *"Com s'ha de fer l'acompanyament d'un alumne de 1r d'ESO que pateix insults homòfobs al pati segons el protocol d'odi i discriminació?"*. |
| Es perd el context específic de la homofòbia o assetjament. Es respon amb mesures genèriques d'acompanyament (ex: estar al costat de l'alumne). | El RAG filtra a Qdrant específicament per a la categoria `conductes_odi_discriminacio` i recupera els passos d'acompanyament singularitzats d'aquest protocol. |
| **Resultat:** Resposta buida de valor normatiu. | **Resultat:** Guia d'actuació precisa de com tractar la víctima del cas concret d'homofòbia. |

---

## 5. Beneficis de la Solució

1. **Robustesa del Triatge de Risc:** En mantenir el fil, les consultes curtes de seguiment no provoquen errors de classificació ni disparen falses alertes de "manca d'informació".
2. **Experiència d'Usuari Fluida:** El docent pot tenir una conversa natural amb el sistema, fent preguntes curtes de continuïtat com si estigués parlant amb un inspector d'educació o expert humà.
3. **Exactitud Legal:** Assegura que totes les cerques vectorials que es fan contra Qdrant apliquin correctament els pre-filtres de metadades del cas original durant tota la sessió de xat.
