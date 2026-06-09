# Documentació Tècnica: Arquitectura del Motor de Triatge i RAG Avançat (b-resol)

Aquesta documentació tècnica descriu exhaustivament el funcionament, l'arquitectura i el flux de dades del **Motor de Triatge Intel·ligent i Generació Recuperada per Context (RAG)** dissenyat per a la plataforma **b-resol**. Aquest document està pensat com a guia de referència per als equips d'enginyeria i desenvolupament que realitzaran la integració en producció.

---

## 1. Visió General del Sistema i Flux de Dades

El sistema implementa una arquitectura **RAG Avançada con Triaje Clínico-Educativo Integrado**. No se limita a fer una cerca semàntica simple sobre documents, sinó que actua com un processador cognitiu que:
1. **Analitza i interpreta l'alerta** inicial (sovint fragmentada i escrita en llenguatge informal o argot juvenil).
2. **Determina la viabilitat i urgència** de la informació abans de procedir a la cerca (evitant falsos positius i respostes inconsistents amb protocols).
3. **Aplica pre-filtres estrictes** basats en metadades inferides (capes de recuperació i categories de risc).
4. **Recupera, filtra i reordena** la normativa i els protocols vigents.
5. **Sintetitza una estratègia d'actuació adaptada**, que es lliura al docent juntament amb una guia d'indagació empàtica per al xat de b-resol.

### Diagrama de Flux del Pipeline (Arquitectura Completa)

```mermaid
flowchart TD
    subgraph Entrada
        A[Alerta de l'Alumne/Docent] -->|Text + Reporting Mode + Metadades Estudiant| B(Pipeline d'Entrada)
    end

    subgraph Fase 2: Triatge Intel·ligent
        B -->|Ingesta en RAM| C[BresolIntakeAnalyzer + QueryAnalyzer]
        C -->|Extracció Estructurada| D{¿Alerta Vàlida / No Ambígua?}
    end

    subgraph Fase 3: Enrutament de Resposta
        D -->|Sí| E[ResponsePlanner: Activar RAG]
        D -->|No o Info Insuficient| F[ResponsePlanner: Ruta d'Indagació Preventiva]
    end

    subgraph Fase 4 i 5: Recuperación y RAG
        E -->|Query Enrichment| G[Generació de Súper Consulta]
        G -->|Cerca Vectorial + Filtre Metadades| H[(Qdrant Vector Store)]
        H -->|Top-K Chunks Candidats| I[Cross-Encoder Reranker]
        I -->|Top-N Chunks Seleccionats| J[Context Builder]
    end

    subgraph Fase 6: Generació i Sortida
        J --> K[LLM Generator: Prompt Dinàmic]
        F --> K
        K -->|Estratègia + Guia d'Indagació + Pla d'Acció| L[Callback / Webhook de Sortida]
    end

    style A fill:#e1f5fe,stroke:#01579b
    style C fill:#fff3e0,stroke:#e65100
    style E fill:#e8f5e9,stroke:#1b5e20
    style F fill:#ffebee,stroke:#c62828
    style H fill:#e8f5e9,stroke:#1b5e20
    style I fill:#f3e5f5,stroke:#4a148c
    style L fill:#e1f5fe,stroke:#01579b
```

---

## 2. Descripció Detallada de les Fases

### Fase 1: Ingesta i Contextualització Crítica
El pipeline rep un payload JSON enviat pel backend core de b-resol. Els dades d'entrada inclouen:
*   **`text`**: El cos de l'alerta en text lliure.
*   **`reporting_mode`**: `"identified"` (si es coneix l'alumne) o `"anonymous"` (alerta anònima).
*   **`student_metadata`**: Diccionari amb edat, gènere i curs escolar (si el report és identificat).

### Fase 2: Triatge Intel·ligent i Anàlisi Predictiu
Un model LLM (Gemini) analitza semànticament la consulta per extreure un esquema JSON estrictamente estructurat sense respondre encara a l'usuari. Aquest anàlisi prediu:
*   **`query_type`**: Tipus de consulta (`application` per a acció/protocol, `legal_support` per a lleis, `mixed` per a ambdues, `unknown`).
*   **`retrieval_layer`**: Capa documental preferent (`application`, `legal_support`, `unknown`).
*   **`risk_category`**: Categoria principal de risc sota una taxonomia predefinida de 18 categories (ex. `assetjament_escolar`, `tca`, `consum_substancies`, `conducta_suicida`).
*   **`urgency_level`**: Nivell d'urgència (`high`, `medium`, `low`, `ambiguous`).
*   **`has_implicated_parties`**: Flag que determina si es fan referències a persones implicades concretes.
*   **`detected_features`**: Llista d'etiquetes específiques que descriuen l'agressió o incident (ex. "violència física", "exclusió").

### Fase 3: Planificació de la Resposta i Enrutament (`ResponsePlanner`)
El planificador avalua el resultat de la Fase 2 i calcula la **puntuació de completesa** de l'alerta (`minimum_information_score`). 
*   **Si `score <= 3` o `urgency_level == "ambiguous"`**: Es determina que l'alerta és massa ambígua per activar mesures punitives o protocols específics de forma segura. L'enrutador **no bloqueja el RAG**, sinó que redirigeix la generació cap a un pla preventiu prioritzant la **Indagació a través del Xat de b-resol** per obtenir les dades que falten, recolzant-se en la guia pedagògica de comunicació empàtica.
*   **Si la informació es suficient**: S'activa la recuperació documental RAG completa per obtenir protocols de resolució detallats.

---

## 3. Fase 4: Ingestió, Segmentació Semàntica (Chunking) i Enriquiment de Metadades [Deep Dive]

Aquesta fase és el nucli de la preparació de les dades en fred (ingestió offline). La seva finalitat és agafar els protocols oficials de la Generalitat, lleis i guies en PDF i transformar-los en fragments de text altament cercables, semàntics i enriquits per emmagatzemar-los a la base de dades vectorial.

```
[Document PDF] ➔ (PdfLoader) ➔ [Pàgines amb Text] 
               ➔ (Chunker: Splitter) ➔ [Chunks en Brut]
               ➔ (llenar_chunks_correct.py) ➔ [Chunks Enriquecidos con Payload]
               ➔ (Embedding) ➔ [Qdrant Vector Store]
```

### A. Càrrega de Documents (`PdfLoader`)
El procés comença a la classe `PdfLoader` (ubicada a [document_pipeline.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/ingestion/document_pipeline.py)).
*   **Mètode utilitzat**: `PyMuPDFLoader` de LangChain.
*   **Funcionament**: Llegeix el fitxer PDF físic pàgina per pàgina. Genera un objecte `Document` per a cada pàgina, conservant la propietat `page_content` i un diccionari de metadatos amb la ruta original (`source`) i el número de pàgina (`page`).
*   **Justificació tècnica**: `PyMuPDF` es un dels parsers de PDF més ràpids en Python. El més important per a un entorn legal-educatiu és que **manté la delimitació estricta de les pàgines reals del PDF original**. Això ens permet registrar el número exacto de pàgina en les metadades de cada chunk, garantint cites normatives precises i verificables per part dels docents en el dashboard.

---

### B. Segmentació Semàntica de Text (`Chunker`) [Detall i Justificació]
La segmentació es gestiona mitjançant la classe `Chunker` a `document_pipeline.py`. Aquest component és crucial: si el text es talla malament, es pot perdre el context d'una mesura correctora o fragmentar una definició legal, fent que el RAG recuperi informació incompleta.

#### 1. Mètode de Divisió: `RecursiveCharacterTextSplitter`
A diferència dels splitters simples (que tallen fixament cada $N$ caràcters o paraules sense respectar l'estructura), el `RecursiveCharacterTextSplitter` funciona de manera intel·ligent a través de separadors jeràrquics.
*   **Funcionament de l'Algoritme Pas a Pas**:
    1. Rep el text d'una pàgina individual del PDF.
    2. Avalua la llista de separadors de forma ordenada: `["\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""]`.
    3. Intenta dividir el text pel primer separador (`\n\n`, paràgrafs). Si la mida dels fragments resultants és inferior a la mida objectiu (`chunk_size`), els manté així.
    4. Si algun bloc de text supera el `chunk_size`, l'algoritme fa una crida recursiva sobre aquest bloc en concret utilitzant el següent separador de la llista (el salt de línia simple `\n`).
    5. Aquest procés es repeteix descendint pels separadors (espais en blanc, punts, comes) fins que tots els fragments compleixen la condició de mida.
    6. **El separador final `""` (buit)** serveix com a fallback de seguretat extrema: si un paràgraf sencer no té cap tipus de puntuació ni espai i supera el límit, es talla a nivell de caràcters per evitar un error de desbordament.

#### 2. Justificació dels Paràmetres de Configuració
*   **Mida del Chunk (`chunk_size = 1000` caràcters)**:
    *   *Justificació:* Equival aproximadament a unes 150-220 paraules. Aquest format s'anomena **"granularitat mitjana"**. Un chunk massiu (ex. 3000 caràcters) dilueix la potència dels embeddings semàntics, ja que barregen massa idees en un sol vector. Un chunk massa petit (ex. 200 caràcters) no conté prou context lògic per a què l'LLM redacti una acció coherent. Els 1000 caràcters són el *sweet spot* que permet encabir un article legal complet, un pas d'un circuit de derivació o una recomanació pedagògica sencera.
*   **Solapament (`chunk_overlap = 150` caràcters)**:
    *   *Justificació:* El solapament de 150 caràcters (un 15% de la mida del chunk) actua com una finestra lliscant que copia el final d'un chunk a l'inici del següent. Això és vital per a **evitar la pèrdua de continuïtat semàntica**. Si una frase clau com *"En cas d'assetjament greu, s'ha d'avisar immediatament a Inspecció"* queda tallada per la meitat exactament en el caràcter 1000, cap dels dos fragments tindria sentit complet. Amb el solapament, la frase apareix sencera com a mínim en un dels dos chunks colindants.
*   **Separadors Prioritaris**:
    *   *Justificació:* Estan dissenyats específicament per a documents oficials i normatius. Els paràgrafs (`\n\n`) i els salts de línia (`\n`) són prioritaris perquè els protocols solen estructurar-se en llistes numerades o passos consecutius. Tallar respectant els salts de línia evita barrejar punts de llistes diferents, garantint que cada pas d'actuació es llegeixi com una unitat lògica autònoma.
*   **Segmentació a nivell de Pàgina (Page-Boundary Awareness)**:
    *   *Justificació:* El pipeline realitza la divisió de text **pàgina per pàgina** en lloc de concatenar tot el PDF en un sol text massiu. Això s'ha dissenyat així per dues raons: primer, per mantenir una correlació estricta i lliure d'errors amb el número de pàgina font (`source_page`); segon, perquè el canvi de pàgina en un protocol sovint marca una transició de secció, i respectar aquesta frontera de forma inherent ajuda a mantenir la cohesió semàntica del fragment.

---

### C. Enriquiment i Normalització de Metadades [Estructura de Payload]
Un fragment de text vectoritzat sense metadades és molt difícil de filtrar amb seguretat. Per aconseguir un RAG de grau de producció lliure d'alucinacions, processem els chunks a través de [llenar_chunks_correct.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/ingestion/llenar_chunks_correct.py), que insereix un payload altament descriptiu.

A continuació es detallen els metadatos gestionats en la fase de chunking mitjançant taules estructurades:

#### Taula 1: Esquema de Metadades del Payload del Chunk

| Camp de la Metadada | Tipus de Dades | Mètode de Càlcul / Inferencia | Descripció i Utilitat en el RAG |
| :--- | :--- | :--- | :--- |
| **`document_type`** | `String` | Assignat en la lectura segons l'arxiu d'origen. | Defineix el tipus de document (ex. `protocol`, `law`, `guidance`, `circuit_actuacio`). |
| **`retrieval_layer`** | `String` | Inferred de `document_type` (regla estàtica). | Divideix la cerca en dues capes lògiques: `"application"` (com actuar) o `"legal_support"` (normativa legal). |
| **`application_layer`** | `Boolean` | Inferred de `document_type`. | Flag booleà equivalent a `retrieval_layer == "application"`. Facilita filtres ràpids en base de dades. |
| **`representation_type`**| `String` | Mapeig estàtic segons el `document_type`. | Indica l'estil formal del fragment (ex. `"redacted_protocol"`, `"visual_circuit"`, `"legal_text"`) per ajustar el format de sortida de l'LLM. |
| **`related_protocols`** | `List[String]`| Inferred pel nom del fitxer en circuits. | Llista de protocols associats a un diagrama/circuit visual, permetent enllaçar conceptes relacionats. |
| **`risk_category`** | `String` | Híbrid (Nom del fitxer + Anàlisi de paraules clau en text). | **[Metadada Crítica]** Categoria de la taxonomia de risc assignada al chunk per realitzar pre-filtrat estricte. |
| **`source_document`** | `String` | Extret del path de l'arxiu original. | Nom de l'arxiu de referència (ex. `protocol-transgenere.pdf`). |
| **`source_page`** | `Integer` | Extret del metadat de pàgina de PyMuPDF. | Pàgina exacta on es troba el text original. Utilitzat per a les cites de font. |
| **`chunk_title`** | `String` | Extret del processat d'encapçalaments. | Títol de la secció o pas concret a la qual pertany el text. |
| **`language`** | `String` | Fixat per defecte en la ingesta (`"ca"`). | Idioma del text del chunk. Permet suport multiidioma. |
| **`jurisdiction`** | `String` | Fixat per defecte (`"Catalunya"`). | Àmbit territorial normatiu del document. |

---

#### Taula 2: Taxonomia de la Categoria de Risc (`risk_category`)

Aquesta taula recull les categories formalment admeses pel payload del chunk i utilitzades pel pre-filtrat de Qdrant:

| Identificador (`risk_category`) | Descripció del Risc Associat | Mètode d'Inferència al Chunk |
| :--- | :--- | :--- |
| **`assetjament_escolar`** | Situacions d'assetjament (bullying) entre iguals al centre. | Anàlisi de paraules clau o per fitxer origen. |
| **`ciberassetjament`** | Assetjament realitzat a través de mitjans digitals/xarxes. | Anàlisi de paraules clau o per fitxer origen. |
| **`conductes_odi_discriminacio`** | Delictes d'odi, racisme, homofòbia, lgtbifòbia, xenofòbia. | Anàlisi de paraules clau o per fitxer origen. |
| **`violencies_masclistes`** | Violència exercida contra les dones per raó de gènere. | Anàlisi de paraules clau o per fitxer origen. |
| **`violencia_sexual`** | Abús sexual, agressió sexual, tocaments, exhibicionisme. | Anàlisi de paraules clau o per fitxer origen. |
| **`maltractament_infantil`** | Negligència domèstica, maltractament físic/emocional a la llar. | Anàlisi de paraules clau o per fitxer origen. |
| **`violencia_familiar`** | Violència en l'àmbit domèstic no masclista o creuada. | Anàlisi de paraules clau o per fitxer origen. |
| **`falta_greument_perjudicial`** | Infraccions molt greus de les normes de convivència del centre. | Anàlisi de paraules clau o per fitxer origen. |
| **`menor_14_infraccio_penal`** | Actes delictius comesos por menors de 14 anys (inimpuntables).| Anàlisi de paraules clau o per fitxer origen. |
| **`presumpte_delicte`** | Delictes generals que requereixen derivació a Mossos/Fiscalia. | Anàlisi de paraules clau o per fitxer origen. |
| **`extremisme_violent`** | Processos de radicalització, terrorisme o violència extrema. | Anàlisi de paraules clau o per fitxer origen. |
| **`conducta_suicida`** | Ideació suïcida activa o verbalitzada, plans de suïcidi. | Anàlisi de paraules clau o per fitxer origen. |
| **`autolesions`** | Talls, autolesions físiques o intents de fer-se mal. | Anàlisi de paraules clau o per fitxer origen. |
| **`tca`** | Trastorns de la Conducta Alimentària (anorèxia, bulímia). | Anàlisi de paraules clau o per fitxer origen. |
| **`consum_substancies`** | Consum de drogues, alcohol, tabac, vapeig a secundària. | Anàlisi de paraules clau o per fitxer origen. |
| **`conflicte_convivencia`** | Conflictes menors o problemes de convivència sense abús de poder.| Anàlisi de paraules clau o per fitxer origen. |
| **`acompanyament_alumnat_transgenere`** | Protocols de transició, canvi de nom o suport a alumnes trans. | Anàlisi de paraules clau o per fitxer origen. |
| **`general`** | Temes transversals de violència o protocols de convivència. | Fallback quan no es detecta cap risc específic. |

---

#### Taula 3: Mapeig de Tipus de Document (`document_type`) i Representació (`representation_type`)

Aquesta matriu determina la transformació estructural des del tipus de document d'origen cap a la capa de RAG i l'estil d'exposició final:

| Tipus de Document (`document_type`) | Capa RAG (`retrieval_layer`) | Capa Aplicació (`application_layer`) | Tipus Representació (`representation_type`) | Estil de Sortida en la Resposta LLM |
| :--- | :--- | :--- | :--- | :--- |
| **`protocol`** | `application` | `True` | `redacted_protocol` | Directrius textuals extretes directament del redactat de protocols oficials. |
| **`framework_protocol`** | `application` | `True` | `redacted_protocol` | Protocols marc d'actuació a nivell de comunitat o departament. |
| **`guidance`** | `application` | `True` | `educational_guide` | Guies pedagògiques de prevenció i detecció a l'aula (estil educatiu/orientador). |
| **`circuit_actuacio`** | `application` | `True` | `visual_circuit` | Passos d'accions concretes i fluxos visuals traduïts a llistes de derivació ràpides. |
| **`protocol_circuit`** | `application` | `True` | `visual_circuit` | Diagrama de flux simplificat d'actuació davant de la urgència. |
| **`law`** | `legal_support` | `False` | `legal_text` | Articles legislatius detallats de lleis nacionals o autonòmiques. |
| **`law_decree`** | `legal_support` | `False` | `legal_text` | Decrets llei i disposicions addicionals. |
| **`organic_law`** | `legal_support` | `False` | `legal_text` | Llei orgànica de protecció de menors (estil purament jurídic). |

---

## 5. Fase 5: Recuperació i Re-ranking Semàntic (RAG en Calent)

Un cop els chunks estan emmagatzemats amb la seva estructura de metadades a Qdrant, la cerca en temps real funciona sota una estratègia híbrida per maximitzar la precisió:

```
[Query Original] + [Chat History] ➔ (Query Condensation) ➔ [Query Condensada]
                                                                  │
                                                                  ▼
                                                   [Triatge i QueryAnalyzer] ➔ [Intent & Filtres]
                                                                                     │
[Súper Consulta] ◄── (QueryEnricher) ◄───────────────────────────────────────────────┘
       │
 (Embeddings Model)
       │
[Vector de la Query] ➔ [Cerca en Qdrant amb Pre-Filtrado] ➔ [Top-K Chunks]
                                                                  │
  [Top-N Chunks Seleccionats] ◄─── (Cross-Encoder Reranker) ◄─────┘
```

### A. Condensació de Consulta i Resolució de Coreferències (Conversational RAG)
Quan l'usuari realitza consultes de seguiment (ex. *"qui s'encarrega d'això?"* o *"i si és menor de 14 anys?"*), la consulta per si sola no conté prou context. Això provocaria que el triatge classifiqués la alerta com a buida/ambígua i que la cerca vectorial fallés.

Per solucionar-ho, s'ha implementat un component de memòria conversacional:
1. **Historial de conversa:** El pipeline rep de Streamlit la llista de missatges anteriors (`chat_history`).
2. **Reescriptura de consulta (Standalone Query):** S'invoca un model LLM amb temperatura `0.0` que agrupa els darrers 6 missatges i la nova consulta. Genera una consulta autònoma en català (ex: *"Qui s'ha d'encarregar d'aplicar les mesures de protecció en el cas d'assetjament escolar a 4t d'ESO?"*).
3. **Propagació del context:** Aquesta consulta condensada és la que s'envia a Bresol Intake, a l'analitzador d'intencions, i al retriever de Qdrant.
4. **Preservació del fil al Generador:** L'historial de la conversa es concatena de forma neta al prompt final (Fase 6), permetent que el model respongui amb coherència de context (ex: *"Com he comentat anteriorment..."*).

### B. Pre-filtrat Estricto en Qdrant (`_build_filter` en `retriever.py`)
Qdrant no realitza una cerca purament vectorial sobre tot el volum de dades. Abans de calcular la distància de cosinus de l'embedding, aplica un **pre-filtrat lògic estricte** utilitzant els metadades inyectats a la Fase 4:
1.  **Filtre de Capa (`retrieval_layer`)**: Si es pregunta què fer, es filtra per recuperar només chunks de `"application"`. Si es demana normativa, es filtra per `"legal_support"`.
2.  **Filtre de Categoria de Risc (`risk_category`)**: Si el triatge predice `"tca"`, Qdrant només avaluarà chunks amb `risk_category == "tca"` o `risk_category == "general"`.
3.  **Filtre de Jurisdicció**: Condició per defecte `"Catalunya"`.

Això redueix el soroll documental al 0% abans de realitzar cap operació de semblança.

### B. Recuperación Vectorial Inicial (`Top-K`)
*   Es genera el vector de la consulta enriquecida (`QueryEnricher`) mitjançant el model d'embeddings.
*   Es recuperen els millors **$K$ candidats** (configurat en `top_k = 15`). El score retornat per Qdrant és una similitud de cosinus (valors típics de 0.40 a 0.75).

### C. Re-ranking Semàntic Profund (`Cross-Encoder Reranker`)
Per solucionar la bretxa lèxica (quan la consulta de l'usuari no utilitza les mateixes paraules exactes que el protocol), els 15 fragments passen pel re-ranquejador:
*   **Model**: Cross-Encoder especialitzat (basat en MS-MARCO).
*   **Funcionament**: Avalua l'atenció creuada completa (query-chunk) de forma bidireccional.
*   **Sortida**: Reordena els fragments i selecciona exclusivament els **$N$ fragmentos superiors** (`top_n = 4` o `top_n = 5`). Aquests fragments finals són el context amb el que treballa el generador.

---

## 6. Fase 6: Generació de la Resposta i Prompt Dinàmic

El `ContextBuilder` agrupa els fragments en un sol text, assegurant que cada un contingui la seva referència a la font en format de cita natural (ex. *"Segons la pàgina 12 del Protocol d'Assetjament Escolar..."*).
El generador final (`gemini-1.5-flash`) rep aquest context lliure de soroll juntament amb les metadades de triatge i processa el prompt dinàmic generant la sortida estructurada en tres eixos:
1.  **Valoració Inicial de la Situació**: Justificació del risc i de la urgència per al docent.
2.  **Mesures Operatives Immediates**: Accions exigides pel protocol per a les primeres 24-48 hores.
3.  **Guia d'Indagació i Entrevista**: Llista de preguntes empàtiques suggerides basades en la comunicació no violenta (CNV), dissenyades expressament per resoldre els buits d'informació detectats a la Fase 2 sense generar alarma.

---

## 7. Resum de Paràmetres Clau i Umbrales

| Fase | Paràmetre / Component | Configuració / Umbral | Propòsit Tècnic |
| :--- | :--- | :--- | :--- |
| **Fase 1** | Càrrega de PDF | `PyMuPDFLoader` | Rapidesa en el processat de PDF i extracció precisa dels límits de pàgina. |
| **Fase 4** | Mida del Chunk (`chunk_size`) | `1000` caràcters | Balanceig ideal de densitat semàntica i retenció de context. |
| **Fase 4** | Solapamiento del Chunk (`chunk_overlap`) | `150` caràcters | Finestra lliscant per a evitar pèrdues de sentit a les fronteres del tall. |
| **Fase 4** | Separadors del Splitter | `["\n\n", "\n", " ", ".", ...]`, `is_separator_regex = False` | Preserva l'estructura de paràgrafs i llistes sinó trencant paraules. |
| **Fase 5** | Cerca Vectorial (`top_k`) | `15` chunks | Fase de recall ampli per assegurar la captura de tots els potencials candidats. |
| **Fase 5** | Selecció Final (`top_n`) | `4` o `5` chunks | Reducció estricta del soroll documental enviat a l'LLM, millorant velocitat i coherència. |
| **Fase 3** | Puntuació de Completesa Mínima | `3` (Escala 1-10) | Umbral de seguretat sota el qual es prioritza la recerca d'informació via xat. |
