# Documentació Tècnica: Arquitectura del Sistema RAG Avançat (b-resol)

Aquesta documentació tècnica descriu de forma clara el funcionament i l'arquitectura del **RAG** dissenyat per a la plataforma **b-resol**. L'objectiu principal d'aquest motor és guiar i assessorar de manera immediata els docents quan reben una alerta de risc d'un menor. Aquest document detalla com s'estructura tota l'arquitectura RAG. 


---

## 1. Visió General del Sistema i Flux de Dades

El sistema implementa una arquitectura **RAG Avançada amb Triatge Previ**. No es limita a fer una cerca semàntica simple sobre documents, sinó que funciona com un assistent intel·ligent que:
1. **Analitza i interpreta l'alerta** inicial (sovint fragmentada i escrita en llenguatge informal o argot juvenil). El docent introdueix una consulta inicial o alerta a la plataforma i el sistema inicia tot el procés
2. **Determina la viabilitat i urgència** de la informació abans de procedir a la cerca (evitant falsos positius i respostes inconsistents amb protocols).
3. **Aplica pre-filtres estrictes** basats en metadades inferides (capes de recuperació i categories de risc).
4. **Recupera, filtra i reordena** la normativa i els protocols vigents.
5. **Sintetitza una estratègia d'actuació adaptada**, que es lliura al docent juntament amb una guia d'indagació empàtica per al xat de b-resol.


---

#### Taula 1: Categories de Risc del Sistema(`risk_category`)

Aquesta taula recull les categories formalment admeses pel payload del chunk i utilitzades pel pre-filtrat de Qdrant. Són les categories que podran ser les alertes:

| Identificador (`risk_category`) | Descripció del Risc Associat |
| :--- | :--- |
| **`assetjament_escolar`** | Situacions d'assetjament (bullying) entre iguals al centre. |
| **`ciberassetjament`** | Assetjament realitzat a través de mitjans digitals/xarxes. |
| **`conductes_odi_discriminacio`** | Delictes d'odi, racisme, homofòbia, lgtbifòbia, xenofòbia. |
| **`violencies_masclistes`** | Violència exercida contra les dones per raó de gènere. |
| **`violencia_sexual`** | Abús sexual, agressió sexual, tocaments, exhibicionisme. |
| **`maltractament_infantil`** | Negligència domèstica, maltractament físic/emocional a la llar. |
| **`violencia_familiar`** | Violència en l'àmbit domèstic no masclista o creuada. |
| **`falta_greument_perjudicial`** | Infraccions molt greus de les normes de convivència del centre. |
| **`menor_14_infraccio_penal`** | Actes delictius comesos por menors de 14 anys (inimpuntables).|
| **`presumpte_delicte`** | Delictes generals que requereixen derivació a Mossos/Fiscalia. |
| **`extremisme_violent`** | Processos de radicalització, terrorisme o violència extrema. |
| **`conducta_suicida`** | Ideació suïcida activa o verbalitzada, plans de suïcidi. |
| **`autolesions`** | Talls, autolesions físiques o intents de fer-se mal. |
| **`tca`** | Trastorns de la Conducta Alimentària (anorèxia, bulímia). |
| **`consum_substancies`** | Consum de drogues, alcohol, tabac, vapeig a secundària. |
| **`conflicte_convivencia`** | Conflictes menors o problemes de convivència sense abús de poder.|
| **`acompanyament_alumnat_transgenere`** | Protocols de transició, canvi de nom o suport a alumnes trans. |
| **`general`** | Temes transversals de violència o protocols de convivència. |

---

## 2. Descripció Detallada de les Fases


### Fase 1: Rebuda alerta

Primer pas del pipeline, el sistema rep la consulta o alerta introduïda pel docent (sempre és el docent qui genera la consulta) a través de la plataforma b-resol
Aquesta consulta es rep del frontend en un format JSON que conté les seguents dades:
*   **`text`**: El missatge que ha introduït el docent.
*   **`reporting_mode`**: `"identified"` (si es coneix l'alumne) o `"anonymous"` (alerta anònima).
*   **`student_metadata`**: Diccionari amb edat, gènere i curs escolar (si el report és identificat).

Nota: la fase 2 i la fase 3 es fan en paral·lel ninguna depen de l'altre i l'ordre no importa. 

### Fase 2: Recepció de l'Alerta i Avaluació inicial d'aquesta

Aquesta fase, el seu objectiu és diagnosticar de manera automàtica i determinista l'estat inicial del cas presentat en la consulta del docent segons els criteris i la clasificació de b-resol (hi ha un fitxer dissenyat per b-resol amb les diferents categories de risc i les seves caracteristiques, veure). S'ha utilitzat el fitxer dissenyat per b-resol, inicialment estaba en pdf i s'ha convertit en un diccionari. El qual s'ha extret les categories de risc i de cada categoria de risc de la Taula 1 la seguent informació:

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

## 3. Fase 4: Ingestió, Segmentació Semàntica (Chunking) i Enriquiment de Metadades 

Aquesta fase és el nucli de la preparació de les dades en fred (ingestió offline). La seva finalitat és agafar els protocols oficials de la Generalitat, lleis i guies en PDF i transformar-los en fragments de text altament cercables, semàntics i enriquits per emmagatzemar-los a la base de dades vectorial.

Aquesta fase està explicada en detall al altre document fase4_chunking_documentacio.

---

## 5. Fase 5: Recuperació i Re-ranking Semàntic (RAG en Calent)

Un cop els chunks estan emmagatzemats amb la seva estructura de metadades a Qdrant, la cerca en temps real funciona sota una estratègia híbrida per maximitzar la precisió:

![Graf de la Fase d'Arquitectura](../../assets/img_documentacion/fase_arquitectura.png)


### A. Contextualització de Consultes i Gestió de l'Historial (Standalone Query)
Quan l'usuari realitza consultes de seguiment (ex. *"qui s'encarrega d'això?"* o *"i si és menor de 14 anys?"*), la consulta per si sola no conté prou context. Això provocaria que el triatge classifiqués la alerta com a buida/ambígua i que la cerca vectorial fallés.

Per solucionar-ho, s'ha implementat un component de memòria conversacional:
1. **Historial de conversa:** El pipeline rep de Streamlit la llista de missatges anteriors (`chat_history`).
2. **Reescriptura de consulta (Standalone Query):** S'invoca un model LLM amb temperatura `0.0` que agrupa els darrers 6 missatges i la nova consulta. Genera una consulta autònoma en català (ex: *"Qui s'ha d'encarregar d'aplicar les mesures de protecció en el cas d'assetjament escolar a 4t d'ESO?"*).
3. **Propagació del context:** Aquesta consulta condensada és la que s'envia a Bresol Intake, a l'analitzador d'intencions, i al retriever de Qdrant.
4. **Preservació del fil al Generador:** L'historial de la conversa es concatena de forma neta al prompt final (Fase 6), permetent que el model respongui amb coherència de context (ex: *"Com he comentat anteriorment..."*).

### B. Pre-filtrat Estricto en Qdrant
Qdrant no realitza una cerca purament vectorial sobre tot el volum de dades. Abans de calcular la distància de cosinus de l'embedding, aplica un **pre-filtrat lògic estricte** utilitzant els metadades inyectats a la Fase 4:
1.  **Filtre de Capa (`retrieval_layer`)**: Si es pregunta què fer, es filtra per recuperar només chunks de `"application"`. Si es demana normativa, es filtra per `"legal_support"`.
2.  **Filtre de Categoria de Risc (`risk_category`)**: Si el triatge predice `"tca"`, Qdrant només avaluarà chunks amb `risk_category == "tca"` o `risk_category == "general"`.
3.  **Filtre de Jurisdicció**: Condició per defecte `"Catalunya"`.

Això redueix el soroll documental al 0% abans de realitzar cap operació de semblança.

### B. Recuperación Vectorial Inicial (`Top-K`)
*   Es genera el vector de la consulta enriquida mitjançant el model d'embeddings.
*   Es recuperen els millors **$K$ candidats** (configurat en `top_k = 15`). El score retornat per Qdrant és una similitud de cosinus (valors típics de 0.40 a 0.75).

### C. Re-ranking Semàntic Profund (`Cross-Encoder Reranker`)
Per solucionar la bretxa lèxica (quan la consulta de l'usuari no utilitza les mateixes paraules exactes que el protocol), els 15 fragments passen pel re-ranquejador:
*   **Model**: Cross-Encoder especialitzat (basat en MS-MARCO).
*   **Funcionament**: Avalua l'atenció creuada completa (query-chunk) de forma bidireccional.
*   **Sortida**: Reordena els fragments i selecciona exclusivament els **$N$ fragmentos superiors** (`top_n = 4` o `top_n = 5`). Aquests fragments finals són el context amb el que treballa el generador.

---

## 6. Fase 6: Generació de la Resposta i Prompt Dinàmic

El `ContextBuilder` agrupa els fragments en un sol text, assegurant que cada un contingui la seva referència a la font en format de cita natural (ex. *"Segons la pàgina 12 del Protocol d'Assetjament Escolar..."*).
El model generador final rep aquest context lliure de soroll juntament amb les metadades de triatge i processa el prompt dinàmic generant la sortida estructurada en tres eixos:
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



---

## 8. Aspectes comentats a la reunió d'evolució

A continuació, es detallen dues de les qüestions tècniques comentades durant la reunió de seguiment, per tal de deixar constància de la seva justificació tècnica i la solució implementada.

### 8.1. Per què la puntuació de similitud dels fragments recuperats pot semblar "baixa" (ex. 0.5)?

Es pot observar que els fragments (`chunks`) seleccionats com a "millors candidats" després de cada consulta a vegades retornen una puntuació de similitud del cosinus (Cosine Similarity) que oscil·la al voltant del 0.5 o el 0.6. A primera vista, això pot semblar un encert "baix" (com si fos un 5 sobre 10 a l'escola), però en l'àmbit dels *embeddings* d'alta dimensionalitat i la cerca semàntica asimètrica, aquesta interpretació no és correcta. 

**Justificació i exemple pràctic:**
La similitud del cosinus no mesura si les paraules són idèntiques, sinó la proximitat dels conceptes en un espai matemàtic molt complex.
*   **Consulta de l'usuari:** *"Un alumne de tercer m'ha dit que li roben l'esmorzar cada dia i li diuen insults al pati."* (Llenguatge natural, quotidià, curt i específic).
*   **Fragment normatiu (Chunk recuperat):** *"Conductes reiterades d'apropiació indeguda de pertinences i vexacions verbals en espais comuns del centre que constitueixen assetjament escolar..."* (Llenguatge tècnic, formal, llarg i general).

Com que l'estil, el to i la densitat del vocabulari són diametralment oposats, el model d'embeddings els assigna una distància que pot reflectir un *score* de 0.55. Això no significa que el document sigui irrellevant, sinó que és **semànticament proper sense ser lèxicament idèntic**. Una similitud de 0.5 - 0.7 és, de fet, l'estàndard esperat i saludable per a resultats extremadament vàlids en entorns RAG legals i educatius, on s'intenta connectar el llenguatge del docent estressat amb el llenguatge fred d'un protocol de la Generalitat.

### 8.2. Millora implementada: Prevenció de la pèrdua del fil de conversa al xat

Inicialment, durant les proves es va comentar que el sistema fallava quan l'usuari feia preguntes de seguiment curtes, provocant que el xat "perdés el fil". Per exemple:
1.  **Usuari:** *"Què he de fer si un alumne pateix assetjament?"* (El sistema respon bé amb el protocol).
2.  **Usuari:** *"I si passa fora del centre?"* (Aquí el sistema fallava originalment perquè cercava literalment *"I si passa fora del centre?"*, una frase sense prou context per trobar documents legals sobre l'assetjament).

**Solució implementada: Contextualització de Consultes (Standalone Query)**
Aquesta problemàtica s'ha solucionat de manera robusta mitjançant la tècnica de memòria conversacional (detallada en profunditat al llarg de la Fase 5 de l'arquitectura). 

Ara, abans d'anar a buscar res a la base de dades vectorial, el sistema passa per una sub-fase de reescriptura. S'agafa l'historial del xat i la pregunta nova, i s'utilitza un model LLM per unificar-ho tot en una única consulta autònoma, rica i independent:
*   **Pregunta original de l'usuari:** *"I si passa fora del centre?"*
*   **Pregunta interna reescrita pel sistema:** *"Quins són els passos a seguir segons el protocol si l'assetjament escolar entre alumnes ocorre fora de les instal·lacions del centre educatiu?"*

Aquesta nova consulta "reescrita" o condensada és la que realment s'envia a Qdrant per fer la cerca vectorial. Això garanteix que la cerca tingui absolutament tot el context necessari, que es trobin els fragments de text correctes, i que l'assistent virtual **no perdi mai el fil** de la conversa amb el docent.

[def]: assets/img_documentacion/fase_arquitectura.png