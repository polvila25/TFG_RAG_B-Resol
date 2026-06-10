# Documentació Tècnica: Arquitectura del Motor de Triatge i RAG Avançat (b-resol)

Aquesta documentació tècnica descriu exhaustivament el funcionament, l'arquitectura i el flux de dades del **Motor de Triatge Intel·ligent i Generació Recuperada per Context (RAG)** dissenyat per a la plataforma **b-resol**. Aquest document està pensat com a guia de referència per als equips d'enginyeria i desenvolupament que realitzaran la integració en producció.

---

## 1. Visió General del Sistema i Flux de Dades

El sistema implementa una arquitectura **RAG Avançada amb Triatge Previ**. No se limita a fer una cerca semàntica simple sobre documents, sinó que actua com un processador cognitiu que:
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

#### Taula 1: Categories de Risc del Sistema(`risk_category`)

Aquesta taula recull les categories formalment admeses pel payload del chunk i utilitzades pel pre-filtrat de Qdrant. Són les categories que podran ser les alertes:

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

## 2. Descripció Detallada de les Fases

### Fase 1: Bresol Intake & Evaluation (Anàlisi del Cas i Gravetat)

Aquesta fase, el seu objectiu és diagnosticar de manera automàtica i determinista l'estat inicial del cas presentat en la consulta del docent segons els criteris i la clasificació de b-resol. S'ha utilitzat el fitxer dissenyat per b-resol, inicialment estaba en pdf i s'ha convertit en un diccionari. El qual conté de cada categoria de risc de la Taula 1 la seguent informació:

| Nom del Camp | Tipus de Dada | Descripció |
| :--- | :--- | :--- |
| **`label`** | `String` | El nom de la categoria de risc (ex. "Bullying o assetjament escolar"). |
| **`definition`** | `String` | Una descripció de què constitueix aquell risc segons el document b-resol. |
| **`minimum_elements`** | `List[String]` | Llista dels elements obligatoris que s'han de complir per aplicar el protocol (ex. repetició temporal). |
| **`key_indicators`** | `List[String]` | Llista de paraules clau que ajuden a l'LLM a detectar el risc dins del text lliure del docent. |
| **`missing_info_questions`** | `List[String]` | Preguntes empàtiques ja predefinides per si falten dades dels elements mínims a la consulta i s'ha de preguntar pel xat a l'alumne. |
| **`safe_identification_questions`** | `List[String]` | Preguntes específiques per obtenir context de l'alumne sense forçar noms ni trencar l'anonimat. |
| **`avoid_questions`** | `List[String]` | Llista de preguntes prohibides per a quan s'interactui amb l'alumne. |
*   **Funcionament de l'Anàlisi de Risc i de Fase**:
    *   **Diagnòstic inicial amb LLM i Injecció del Diccionari**: El procés comença amb un prompt estructurat que s'envia a un LLM. El sistema agafa el diccionari complet de categories de risc (detallat a la taula superior) i l'injecta directament dins d'aquest prompt, juntament amb la consulta escrita pel docent. Així, el LLM pot comparar exactament els fets relatats amb els criteris oficials de b-resol. Aquest prompt restringeix el model perquè no doni cap resposta narrativa, sinó que retorni exclusivament el següent esquema JSON:

```json
{
  "bresol_case_type": "string (Categoria de risc detectada)",
  "risk_category": "string (Igual que bresol_case_type)",
  "detected_indicators": ["string (Llista d'indicadors presents)"],
  "missing_information": ["string (Informació clau que falta)"],
  "missing_minimum_elements": ["string (Elements obligatoris del protocol absents)"],
  "reporter_role": "string (Rol de la persona informant)",
  "victim_identified": "boolean (Si la víctima està identificada)",
  "aggressor_identified": "boolean (Si l'agressor està identificat)",
  "phase_assessment": "string (Nivell de gravetat legal inicial)",
  "possible_crime_indicators": ["string (Llista de possibles delictes)"],
  "requires_urgent_review": "boolean (Si hi ha risc vital o urgència crítica)",
  "enriched_context_hint": "string (Pista de context per cerca RAG)",
  "notes": "string (Anotacions addicionals)"
}
```
**Avaluació determinista per codi**: El sistema processa el JSON generat pel model LLM i fa una avaluació mitjançant lògica. L'avaluador creua la informació del JSON amb el protocol per detectar exactament quines dades clau falten i preparar les preguntes per obtenir més informació.

A més servirà més endavant per donar-li al Chatbot (en les fases posteriors) un "guió" exacte de què li ha de preguntar a l'usuari, és a dir podrem realitzar un prompt molt més acurat per obtenir millor resposta i assegurant que recull tota la informació obligatòria de manera guiada i segura abans de tancar el cas.

### Fase 2: Consulta del docent, Contextualització i Anàlisi de la Consulta (fase pre-recuperació)

Primer pas del pipeline, el sistema rep la consulta o alerta introduïda pel docent (sempre és el docent qui genera la consulta) a través de la plataforma b-resol
Aquesta consulta es rep del frontend en un format JSON que conté les seguents dades:
*   **`text`**: El missatge que ha introduït el docent.
*   **`reporting_mode`**: `"identified"` (si es coneix l'alumne) o `"anonymous"` (alerta anònima).
*   **`student_metadata`**: Diccionari amb edat, gènere i curs escolar (si el report és identificat).

### Fase 3: Anàlisi de la Consulta incial del docent (fase pre-recuperació)
 L'objectiu d'aquesta fase és exclusivament "entendre i classificar" què està demanant el docent abans d'anar a buscar res a la base de dades. És una fase de pre-processament on només s'utilitza la consulta del docent. 
 
 S'ha utilitzat un model LLM (Gemini) per analitzar semànticament la consulta per extreure un esquema JSON estrictamente estructurat sense respondre encara a l'usuari. Aquest anàlisi prediu:
*   **`query_type`**: Tipus de consulta (`application` per a acció/protocol, `legal_support` per a lleis, `mixed` per a ambdues, `unknown`).
*   **`retrieval_layer`**: Capa d'acció' (`application`, `legal_support`, `unknown`).
*   **`risk_category`**: Categoria principal de risc sota una taxonomia predefinida de 18 categories es poden veure a la taula  (ex. `assetjament_escolar`, `tca`, `consum_substancies`, `conducta_suicida`).
*   **`urgency_level`**: Nivell d'urgència (`high`, `medium`, `low`, `ambiguous`).
*   **`has_implicated_parties`**: Flag que determina si es fan referències a persones implicades concretes.
*   **`detected_features`**: Llista d'etiquetes específiques que descriuen l'agressió o incident (ex. "violència física", "exclusió").

### Fase 3: Planificació de la Resposta i Enrutament (`ResponsePlanner`)

He dissenyat una estategia d'enrutament que rep l'avaluació de les dades del cas (Fase 1) i l'anàlisi de la intencionalitat de la consulta (Fase 2) per prendre la decisió estratègica de com ha de respondre el sistema. La seva funció és establir la ruta de la resposta, decidir si s'ha d'executar o no la cerca documental (RAG) i preparar instruccions directives clares per al model.

Aquesta planificació s'aplica mitjançant un arbre de decisions per codi amb 4 prioritats clares:

1.  **Fora de Domini (Prioritat 1)**: Si la consulta no té cap relació amb l'entorn escolar, el sistema desactiva el RAG i rebutja la interacció per protegir els recursos.
2.  **Risc Vital Urgent (Prioritat 2)**: Si es detecta perill vital imminent (ex: autolesions, violència greu), el sistema prioritza exclusivament cercar mesures de protecció i seguretat física immediata, ignorant procediments secundaris.
3.  **Alerta Anònima (Prioritat 3)**: Si l'usuari ha usat el canal anònim, s'avalua la quantitat de dades aportades:
    *   **Informació incompleta**: S'activa un pla d'indagació segura dissenyat per investigar la situació evitant fer preguntes directes que puguin posar en perill l'anonimat de l'emissor.
    *   **Informació suficient**: S'activa la cerca del protocol corresponent afegint instruccions molt estrictes per garantir i protegir la identitat de qui reporta.
4.  **Cas Estàndard i Identificat (Prioritat 4)**: Per a les consultes generals, l'enrutador revisa si falten elements obligatoris i el tipus de petició:
    *   **Consulta Legal**: El RAG es focalitza exclusivament a cercar marc normatiu i legislació.
    *   **Consulta de Protocol / Pràctica**: Segons la completesa de l'alerta:
        *   **Massa ambigua o insuficient**: L'enrutador evita donar un procediment definitiu per seguretat. En comptes d'això, llança una resposta d'orientació preventiva recolzant-se en el xat empàtic per demanar les dades que falten.
        *   **Ambigüitat Parcial**: Es retorna la part aplicativa del protocol inicial i es combina amb la petició de les dades pendents.
        *   **Informació completa**: El cas està perfectament tipificat i madur. S'activa la ruta per retornar el procediment d'actuació de manera completa, directa i executiva.

Com a resultat, el planificador retorna un a resposta que conte el camps: `response_type` (ruta final de la resposta), `should_run_documental_rag` (si s'executa la cerca RAG a Qdrant o no si es fora de context), `urgent_actions` (accions de seguretat immediates (només alertes urgents)) i `rag_instructions` (instruccions semàntiques directes al generador final (són com meta-instruccions)).

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
El procés comença a la classe `PdfLoader`.
*   **Mètode utilitzat**: `PyMuPDFLoader` de LangChain.
*   **Funcionament**: Llegeix el fitxer PDF físic pàgina per pàgina. Genera un objecte `Document` per a cada pàgina, conservant la propietat `page_content` i un diccionari de metadatos amb la ruta original (`source`) i el número de pàgina (`page`). És a dir cada pagina del pdf es converteix en un objecte Document.
*   **Justificació**: `PyMuPDF` es un dels parsers de PDF més ràpids en Python. El més important per a un entorn legal-educatiu és que **manté la delimitació estricta de les pàgines reals del PDF original**. Això ens permet registrar el número exacto de pàgina en les metadades de cada chunk, garantint cites normatives precises i verificables per part dels docents en el dashboard.

---

### B. Segmentació Semàntica de Text (`Chunker`) [Detall i Justificació]
La segmentació es gestiona mitjançant una classe creada anomenada `Chunker` a `document_pipeline.py`. Aquest component és crucial: si el text es talla malament, es pot perdre el context d'un protocol o fragmentar una definició legal, fent que el RAG recuperi informació incompleta. S'ha optat per utilitzar diferents estrategies segons el tipus de document, he decidit dividir-ho en protocols i lleis utilitzant una estrategia i després circuits d'actuació, degut a una estructura completament diferent, s'ha utilitzat un altre mètode. 

#### 1. Mètode de Divisió per Protocols i lleis:

S'ha utilitzat la clase de divisió de text `RecursiveCharacterTextSplitter` de la llibreria `langchain_text_splitters`. Aquest component treballa de forma totalment local. 

**Com funciona?**
A diferència d'una estratègia de fragmentació simple (que talla fixament cada $N$ caràcters o paraules sense respectar l'estructura), aquest mètode treballa de manera intel·ligent. En passar-li un text, es basa en els següents paràmetres clau:
*   **Separadors**: El splitter busca els caràcters indicats (salts de línia, espais, puntuació) per decidir on tallar, utilitzant-los de forma jeràrquica.
*   **Chunk Size (Mida màxima)**: Cada fragment resultant no excedirà mai la longitud màxima establerta.
*   **Chunk Overlap (Solapament)**: Es defineix una quantitat de caràcters que es repetiran entre el final d'un fragment i l'inici del següent, permetent que comparteixin context.
*   **Resultat**: Finalment, retorna una llista de fragments llestos per ser usats en la següent etapa del flux (generació d'embeddings).
*   **Funcionament de l'Algoritme Pas a Pas**:
    1. Rep el text d'una pàgina individual del PDF.
    2. Avalua la llista de separadors de forma ordenada: `["\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""]`.
    3. Intenta dividir el text pel primer separador (`\n\n`, paràgrafs). Si la mida dels fragments resultants és inferior a la mida objectiu (`chunk_size`), els manté així.
    4. Si algun bloc de text supera el `chunk_size`, l'algoritme fa una crida recursiva sobre aquest bloc en concret utilitzant el següent separador de la llista (el salt de línia simple `\n`).
    5. Aquest procés es repeteix descendint pels separadors (espais en blanc, punts, comes) fins que tots els fragments compleixen la condició de mida.
    6. **El separador final `""` (buit)** serveix com a fallback de seguretat extrema: si un paràgraf sencer no té cap tipus de puntuació ni espai i supera el límit, es talla a nivell de caràcters per evitar un error de desbordament.

#### 2. Justificació dels Paràmetres de Configuració Utilitzats

Explicaré els caràcters de la clase `RecursiveCharacterTextSplitter` per justificar el seu ús en el meu projecte. 

*   **Mida del Chunk (`chunk_size = 1000` caràcters)**:
    *   Equival aproximadament a unes 150-220 paraules. Un chunk massiu (ex. 3000 caràcters) redueix la potència dels embeddings semàntics, ja que barregen massa idees en un sol vector. Un chunk massa petit (ex. 200 caràcters) no conté prou context lògic per a què l'LLM redacti una acció coherent. Els 1000 caràcters són el *punt òptim* que permet encabir un article legal complet, un pas d'un circuit de derivació o una recomanació pedagògica sencera.
*   **Solapament (`chunk_overlap = 150` caràcters)**:
    *   Per asegurar la continuïtat semàntica, he triat un solapament de 150 caràcters (un 15% de la mida del chunk) actua com una finestra lliscant que copia el final d'un chunk a l'inici del següent. Això és vital per a **evitar la pèrdua de continuïtat semàntica**. Si una frase clau com *"En cas d'assetjament greu, s'ha d'avisar immediatament a Inspecció"* queda tallada per la meitat exactament en el caràcter 1000, cap dels dos fragments tindria sentit complet. Amb el solapament, la frase apareix sencera com a mínim en un dels dos chunks colindants.
*   **Llista de Separadors**: `["\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""]`
    *   Aquest separadors estan triats per respectar de manera intel·ligent l'estructura dels documents normatius. El divisor de paràgraf (`\n\n`) i el salt de línia (`\n`) tenen la màxima prioritat perquè els protocols solen estar formats per llistes numerades. Així, el sistema intentarà primer dividir el text per paràgrafs; només si un paràgraf sencer excedeix els 1000 caràcters del `chunk_size`, l'algoritme baixarà de nivell i provarà de tallar-lo pel següent separador disponible (salts de línia simples, després espais `" "`, punts `"."`, comes `","`, etc.). D'aquesta manera s'evita trencar frases per la meitat o barrejar punts de llistes diferents, garantint que cada pas d'actuació es mantingui com una unitat lògica. El separador final buit (`""`) actua com a mesura de seguretat extrema, forçant un tall per caràcter si un bloc massiu de text no conté puntuació.
*   **Segmentació a nivell de Pàgina (Page-Boundary Awareness)**:
    *   Com s'ha explicat al principi, el pipeline realitza la divisió de text **pàgina per pàgina** en lloc de concatenar tot el PDF en un sol text. Això s'ha dissenyat així per dues raons: primer, per mantenir una correlació estricta i lliure d'errors amb el número de pàgina font (`source_page`) i així saber exactament cada fragment a quina pàgina pertany, clau per després poder referenciar i citar la resposta. Segon, perquè el canvi de pàgina en un protocol sovint marca una transició de secció, i respectar aques límit ajuda a mantenir la cohesió semàntica del fragment.

---

### B.1. Arquitectura Específica per a Circuits d'Actuació: Del Diagrama Visual al Graf de Decisió Semàntic

Els circuits d'actuació originals del Departament d'Educació són representacions visuals (diagrames de flux) amb múltiples camins, condicions i derivacions. Donat que la segmentació lineal tradicional (tallar el text cada $N$ caràcters) destruiria la lògica seqüencial d'aquests diagrames, s'ha implementat una arquitectura alternativa basada en **Grafs de Decisió Semàntics**.

#### Concepte Arquitectònic

En lloc de tractar un circuit com un text pla, com es fa emb els protocols o lleis, el sistema el descompon en **nodes discrets** (chunks). Cada node representa un pas específic del circuit, una decisió o una derivació externa. Aquests nodes estan enllaçats entre si perquè l'LLM i el sistema RAG puguin «navegar» pel protocol de la mateixa manera que un humà seguiria les fletxes d'un diagrama. Realment el que es segueix a les metadates es crear una estructura de graf. 

#### Tipologia de Nodes (`chunk_type`)

L'arquitectura defineix diversos tipus de chunks per caracteritzar la naturalesa de cada pas del circuit:

| Tipus de Node | Descripció |
| :--- | :--- |
| **`document_identity`** | Node arrel que defineix el propòsit general i l'abast del circuit. |
| **`trigger`** | L'acció o event que activa el circuit (ex. coneixement o sospita de violència). |
| **`phase`** | Una etapa genèrica del circuit (ex. detecció, valoració, comunicació). |
| **`decision_node`** | Punt de bifurcació crítica on el camí a seguir depèn de certes condicions (ex. «És una conducta contrària o una falta greu?»). |
| **`action_step`** | Un pas purament operatiu (ex. aplicar mesures educatives). |
| **`external_derivation`** | Punt on el cas surt de l'àmbit del centre educatiu i passa a agents externs (Mossos, DGAIA, Fiscalia). |
| **`classification`** | Classificació de la infracció o conducta. |
| **`communication`** | Comunicacions requerides a parts interessades o agents. |

#### Estructura de Dades del Payload del Node

Cada node del circuit s'emmagatzema en format JSON pur. L'estructura de metadades del `payload` està dissenyada per suportar cerques vectorials híbrides i reconstrucció de context de grafs:

##### Enrutament i Connectivitat (El Graf)

*   **`step_id`**: Identificador únic del pas actual (ex. `circuit_violencia_004_decisio_ambit`).
*   **`previous_step_id`**: Identificador del pas immediatament anterior.
*   **`next_step_ids`**: Array amb els IDs dels passos següents possibles. Permet a l'LLM saber exactament quines opcions hi ha a continuació i «caminar» pel graf.

##### Contingut i Representació Semàntica

*   **`text`**: La descripció textual literal de l'acció que s'ha de realitzar en aquest node.
*   **`embedding_text`**: Un text super-enriquit dissenyat exclusivament per ser vectoritzat. Conté paraules clau addicionals, sinònims i context implícit que maximitzen la probabilitat de ser recuperat correctament per **Qdrant**.
*   **`chunk_title`**: Títol clar del node per referenciar-lo en les respostes generades.

##### Lògica de Decisió Dinàmica (`decision_logic`)

Per als nodes de tipus `decision_node`, s'incrusta un sub-objecte algorítmic que explica a l'LLM les rutes lògiques condicionals:

```json
"decision_logic": {
  "decision_question": "La situació és una conducta contrària o una falta greu?",
  "conditions": [
    {
      "condition_id": "conducta_contraria_convivencia",
      "next_action": "abordatge_NOFC_PdC_accio_tutorial",
      "next_step_id": "circuit_violencia_008_conductes_contraries"
    },
    {
      "condition_id": "falta_greument_perjudicial",
      "next_action": "passar_a_direccio_i_equip_valoracio",
      "next_step_id": "circuit_violencia_010_faltes_greument_perjudicials"
    }
  ]
}
```

> [!IMPORTANT]
> Aquest disseny permet que, en recuperar aquest chunk, el model generatiu sàpiga exactament **què preguntar a l'usuari** en mode exploratori (ex. a través de la suggerència d'interacció al xat) per poder derivar-lo al següent pas correcte del circuit.

##### Agents, Sistemes i Responsables

Els nodes registren quines entitats han d'intervenir en aquell moment precís mitjançant llistes predefinides:
*   **`actors_involved`** / **`responsible`**: Qui ha d'executar l'acció (ex. *direcció*, *equip de valoració*, *alumnat_menor_18_anys*).
*   **`support_agents`**: Assessorament extern però dins l'àmbit educatiu (ex. *EAP*, *USAV*).
*   **`external_agents`**: Entitats fora d'educació obligades a actuar en derivacions (ex. *Fiscalia*, *Jutjat de guàrdia*).
*   **`systems`**: Sistemes informàtics oficials a usar (ex. registre obligatori al *REVA*).

##### Alineació Normativa i Legal

*   **`legal_references`**: Mencions crues a les normatives vinculants.
*   **`normalized_legal_references`**: Estructures normalitzades que mapegen la llei exacta per creuar-la de forma relacional amb la base de dades de legislació (`legal_support`).

#### Integració dels Circuits en el Pipeline d'Ingesta

Per evitar errors humans o desalineaments estructurals en els nodes base proporcionats als arxius JSON, l'script [llenar_chunks_correct.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/ingestion/llenar_chunks_correct.py) actua com una capa de normalització, validació estricta i auto-completat d'inferència per als circuits:

1.  **Capa de Recuperació**: L'script assegura que tot document de tipus `circuit_actuacio` rep obligatòriament els metadats `retrieval_layer = "application"` i `application_layer = true`.
2.  **Inferència de Protocols Relacionats**: Si un node de circuit no defineix explícitament a quin protocol oficial respon, l'script creua el nom del fitxer amb un diccionari estàtic i li assigna la macro-referència (`protocol_violencia_ambit_educatiu`).
3.  **Inferència Semàntica de Riscos (`risk_category`)**:
    *   Si és un circuit determinista (ex. Drogues), se li assigna la seva categoria fixa (`consum_substancies`) mitjançant regles de fallback basades en el nom del fitxer.
    *   Si és un circuit transversal (ex. Violència, que alberga múltiples violències dins), l'script avalua tot el text semàntic del node (`build_risk_context_text()`) i mitjançant una sèrie de **Regles de Contingut basades en Expressions Regulars Lleugeres** (Content Rules) etiqueta el node específic amb sub-riscos com *assetjament_escolar* o *maltractament_infantil*.

#### Beneficis Operatius dels Grafs de Decisió en el Motor RAG

La transformació de diagrames visuals en aquests **Grafs de Decisió Semàntics** en JSON atorga avantatges d'alt rendiment en producció:

1.  **Prevenció d'Al·lucinacions Estructurals**: En estar codificats mitjançant un ID propi i punters directes `next_step_ids`, l'LLM es converteix en un simple «caminant del graf» que no inventa el següent pas d'un protocol, sinó que llegeix forçosament les rutes programades.
2.  **Recuperació Vectorial Altament Precisada**: En indexar-se al vector store, el pipeline pot realitzar *Hard-Filtering* estricte (ex. filtrar només chunks on `risk_category == "falta_greument_perjudicial"`) abans d'usar algoritmes de similitud basats en Embeddings, reduint enormement la latència.
3.  **Memòria Conversacional Contextual**: En un RAG multi-torn, si l'alumne respon «sí, és una falta greu», el generador extreu immediatament el `next_step_id` associat a aquella condició del `decision_logic` anterior, i enfoca el `Retrieval` sobre l'ID objectiu d'aquell node del circuit.

---

### C. Estratègia d'Enriquiment, Model de Llenguatge i Normalització de Metadades [Estructura de Payload]

Un fragment de text vectoritzat sense metadades és molt difícil de filtrar amb seguretat. Per aconseguir un RAG de grau de producció lliure d'al·lucinacions, processem els chunks a través de [llenar_chunks_correct.py](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/ingestion/llenar_chunks_correct.py), que insereix un payload altament descriptiu.

#### Model de Llenguatge (LLM) per a l'Extracció de Metadades

Per a la generació, extracció i enriquiment dels metadats estructurats s'ha dissenyat un pipeline automatitzat i híbrid que combina intel·ligència artificial i regles de negoci deterministes:

*   **Model**: **`gpt-4o-mini`** d'OpenAI.
*   **Configuració**: Temperatura `0.0` per garantir un comportament determinista, repetitiu i evitar al·lucinacions en la classificació o en els arrays relacionals.
*   **Integració**: S'utilitza la funció `.with_structured_output(Schema)` de LangChain combinada amb models de **Pydantic** (`ProtocolChunkMetadata` i `LegalChunkMetadata`). Això obliga l'LLM a retornar un esquema JSON amb tipus de dades estrictament validats sota taxonomies predefinides (`RiskCategory`, `Phase`, `ChunkType`, `SeverityContext`).
*   **Prompting d'Extracció**: L'LLM rep el contingut del fragment de text i el context de la seva ubicació en el document (capçaleres). A partir d'això, s'encarrega de resumir i optimitzar la cerca mitjançant la redacció de l'`embedding_text`, identificar els responsables de les mesures correctores (`actors_involved`, `responsible`), mapejar agents interns/externs de suport o derivació, i extreure les referències normatives.
*   **Mecanismes de Fallback**: Si l'LLM falla, no pot ser contactat o produeix un error de validació de l'esquema de sortida, el pipeline utilitza funcions deterministes en Python que calculen automàticament paràmetres com la fase o la categoria de risc mitjançant el mapeig lexema/paraula clau i expressions regulars aplicades directament sobre el text del chunk.

A continuació es detallen els metadats gestionats en la fase de chunking mitjançant taules estructurades:

#### Taula 1: Esquema Complet de Metadades del Payload del Chunk

| Camp de la Metadada | Tipus de Dades | Mètode de Càlcul / Inferència | Descripció i Utilitat en el RAG |
| :--- | :--- | :--- | :--- |
| **`step_id`** / **`id`** | `String` | Assignat estàticament (graf de circuits) o derivat de l'estructura. | Identificador únic del fragment a la base de dades vectorial. Permet la traçabilitat exacta de les accions. |
| **`document_type`** | `String` | Assignat en la lectura segons l'arxiu d'origen. | Defineix el tipus de document (ex. `protocol`, `law`, `guidance`, `circuit_actuacio`). |
| **`retrieval_layer`** | `String` | Inferred de `document_type` (regla estàtica). | Divideix la cerca en dues capes lògiques: `"application"` (com actuar) o `"legal_support"` (normativa legal). |
| **`application_layer`** | `Boolean` | Inferred de `document_type`. | Flag booleà equivalent a `retrieval_layer == "application"`. Facilita filtres ràpids en base de dades. |
| **`representation_type`** | `String` | Mapeig estàtic segons el `document_type`. | Indica l'estil formal del fragment (ex. `"redacted_protocol"`, `"visual_circuit"`, `"legal_text"`) per ajustar el format de sortida de l'LLM. |
| **`related_protocols`** | `List[String]` | Inferred pel nom del fitxer en circuits, o extret per LLM. | Llista de protocols associats a un diagrama/circuit visual, permetent enllaçar conceptes relacionats. |
| **`risk_category`** | `String` | Híbrid (Nom del fitxer + Anàlisi de paraules clau en text / LLM). | **[Metadada Crítica]** Categoria de la taxonomia de risc assignada al chunk per realitzar pre-filtrat estricte. |
| **`source_document`** | `String` | Extret del path de l'arxiu original. | Nom de l'arxiu de referència (ex. `protocol-transgenere.pdf`). |
| **`source_page`** | `Integer` \| `Null` | Extret del metadat de pàgina de PyMuPDF o assignat per l'analitzador. | Pàgina exacta on es troba el text original, utilitzat per a citacions de font sense al·lucinacions. |
| **`chunk_title`** | `String` | Extret estructuradament per LLM (`gpt-4o-mini`). | Títol representatiu i resumit de la secció o pas concret al qual pertany el text. |
| **`chunk_type`** | `String` | Extret estructuradament per LLM (`gpt-4o-mini`). | Tipus funcional del chunk en el protocol (ex. `decision_node`, `action_step`, `external_derivation`, `trigger`). |
| **`phase`** | `String` | Inferred per capçaleres de secció / LLM (`gpt-4o-mini`). | Fase del procediment a la qual correspon el fragment (ex. `deteccio_identificacio`, `valoracio`, `comunicacio`, `normativa`). |
| **`embedding_text`** | `String` | Enriquit i redactat per LLM (`gpt-4o-mini`). | Text súper optimitzat per a la cerca semàntica, enllaçant sigles, definicions, sinònims i referències de suport. |
| **`actors_involved`** / **`responsible`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Rols o subjectes que tenen l'obligació de dur a terme l'acció (ex. `direccio_centre`, `docent`, `familia`). |
| **`support_agents`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Equips interns de suport educatiu que poden assessorar en el cas (ex. `EAP`, `USAV`, `Inspeccio`). |
| **`external_agents`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Agents judicials o de protecció social de derivació obligada (ex. `Mossos`, `Fiscalia`, `DGAIA`). |
| **`systems`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Eines informàtiques o de registre on s'ha de bolcar la incidència (ex. registre al `REVA`). |
| **`decision_logic`** | `Object` \| `Null` | Extret estructuradament per LLM (`gpt-4o-mini`). | JSON amb branques i condicions per derivar l'usuari cap a següents nodes lògics de la decisió. |
| **`legal_references`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Mencions literals de lleis o articles presents al fragment de text. |
| **`normalized_legal_references`** | `List[Object]` | Extret estructuradament per LLM (`gpt-4o-mini`) + normalitzador. | Objectes relacionals (ex. `law_abbreviation == 'LEC'`, `article == '37.1'`) per creuament documental. |
| **`requires_external_activation`** | `Boolean` | Inferred segons la presència de derivacions externes. | Indica si el pas actual exigeix notificar immediatament entitats judicials o policials. |
| **`requires_human_review`** | `Boolean` | Fixat per defecte (`true`). | Defineix si el chunk requereix revisió/aprovació humana en lloc d'automatització total. |
| **`keywords`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Llista de conceptes clau per millorar la recuperació per paraules clau exactes. |
| **`language`** | `String` | Fixat per defecte (`"ca"`). | Idioma del contingut textual. |
| **`jurisdiction`** | `String` | Fixat per defecte (`"Catalunya"`). | Àmbit territorial legislatiu. |

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
