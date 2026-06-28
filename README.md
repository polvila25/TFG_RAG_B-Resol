# Assistent RAG b-resol

L'objectiu principal d'aquest projecte és desenvolupar un sistema **Advanced RAG (Retrieval-Augmented Generation)** orientat a la gestió intel·ligent d'alertes sensibles en entorns educatius dins de la plataforma b-resol.

## Característiques principals

Aquest sistema assisteix els docents i responsables de convivència en la interpretació inicial d'alertes relacionades amb riscos psicosocials en l'entorn escolar. Concretament, permet:
- **Analitzar consultes en llenguatge natural** formulades per la comunitat docent.
- **Classificar l'alerta i avaluar-ne el risc inicial**, abastant situacions com assetjament escolar, ciberassetjament, autolesions, conducta suïcida, violència masclista, violència intrafamiliar, discriminació, trastorns alimentaris, consum de substàncies, entre d'altres.
- **Recuperar documents oficials rellevants**, com protocols d'actuació i legislació vigent, per contextualitzar la situació.
- **Generar respostes fonamentades i traçables**, dissenyades exclusivament a partir de la normativa i els protocols vigents, prioritzant sempre la protecció del menor i la minimització de dades.

## Arquitectura

El sistema es construeix sobre un pipeline d'Advanced RAG que orquestra diverses fases per garantir la precisió, seguretat i rellevància tècnica de les respostes:

1. **Query Analyzer**: Utilitza un model lleuger (LLM) per analitzar l'alerta inicial, extraient metadades clau (tipus de consulta, urgència, presència de dades sensibles) per determinar com s'ha de processar.
2. **Query Enricher**: Enriqueix la consulta inicial afegint-hi termes semàntics basats en la classificació prèvia i els indicadors de risc detectats per millorar la precisió en la cerca vectorial.
3. **Semantic Retriever (Qdrant)**: Realitza una cerca de similitud semàntica utilitzant embeddings per recuperar els fragments documentals (`chunks`) més rellevants de la base de dades vectorial.
4. **Cross-Encoder Reranker**: Reordena els candidats recuperats aplicant un model *cross-encoder* d'alta precisió per assegurar-se que els documents finalment utilitzats són els més pertinents per al cas.
5. **Context Builder**: Estructura i consolida els fragments reordenats, preservant la informació sobre la font i la pàgina per garantir-ne la traçabilitat absoluta.
6. **Prompt Builder**: Injecta de manera dinàmica instruccions institucionals i d'actitud (ex: instruccions de confidencialitat si el cas és anònim, o de protecció si és d'extrema gravetat) i construeix el *prompt* final.
7. **LLM Generator (Gemini)**: Genera la resposta final de forma condicionada pel context proporcionat i complint estrictament amb els rols assignats.

## Estructura del projecte

```text
src/
├── bresol_context/         # Lògica de negoci, triatge inicial, taxonomies de risc i avaluació
├── ingestion/              # Pipelines d'ingestió, processament i fragmentació de documents PDF
├── privacy/                # Eines d'anonimització de dades personals amb RegEx i NLP (spaCy)
├── rag/                    # Orquestració RAG: Anàlisi, recuperació, generació i ruteig de consultes
├── utils/                  # Funcions auxiliars i generadors documentals (ex: exportació PDF)
└── vector_store/           # Connexió, indexació i configuració de la base de dades vectorial Qdrant
```

*(A més, el projecte conté el directori `frontend/` on es defineix la interfície gràfica d'usuari i el directori `data/` per allotjar la base de dades i fitxers crues).*

## Flux de funcionament

1. **Entrada de l'alerta**: El docent o responsable introdueix el cas mitjançant la interfície web.
2. **Triatge i anonimització inicial**: El sistema desidentifica qualsevol dada personal (noms, correus, telèfons, DNI/NIE) gràcies al mòdul de privacitat i realitza una extracció del tipus de risc, urgència i característiques estructurals de la consulta.
3. **Anàlisi i enriquiment**: Es determina el focus de la consulta (pràctica, legal, mixta) i s'expandeix semànticament per millorar la recuperació d'informació oculta o implícita en la petició inicial.
4. **Recuperació i reordenació (Retrieval & Reranking)**: S'obtenen els protocols oficials de Qdrant i es reordenen utilitzant models avançats per trobar exactament quina part del document soluciona l'alerta de la manera més eficient.
5. **Generació condicionada**: S'assembla un context traçable (amb pàgines i títols de font) i un *prompt* dinàmic. Finalment, el model generatiu redacta les recomanacions.
6. **Postprocessament i desanonimització**: Es restaura la informació i els noms originaris exclusivament en l'etapa final per a la interfície del docent, assegurant que les dades sensibles mai viatgen a l'API del model generatiu.

## Instal·lació

Per posar en marxa el sistema en un entorn local, cal seguir aquests passos:

1. **Clonar el repositori i situar-se al directori arrel**.
2. **Crear i activar un entorn virtual** (recomanat per aïllar dependències):
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/MacOS
   source .venv/bin/activate
   ```
3. **Instal·lar les dependències requerides**:
   ```bash
   pip install -r requirements.txt
   # Comanda opcional per carregar les dependències spaCy de la llengua catalana si no s'instal·len automàticament:
   # python -m spacy download ca_core_news_sm
   ```
4. **Configurar les variables d'entorn**:
   Crear un fitxer `.env` a l'arrel del projecte basant-se en el següent apartat.

## Variables d'entorn

L'arxiu `.env` ha de contenir la següent configuració mínima perquè el sistema es connecti amb els proveïdors d'IA i la base de dades vectorial:

```env
GEMINI_API_KEY=la_teva_clau_api_de_google_ai_studio
GEMINI_MODEL=gemini-1.5-flash
QDRANT_MODE=local
```

*(El sistema suporta connexions remotes per a Qdrant. Pots consultar `src/vector_store/config.py` per revisar opcions addicionals per configurar instàncies Dockeritzades o Qdrant Cloud).*

## Ús

Per iniciar l'assistent i la interfície gràfica basada en Streamlit:

```bash
streamlit run frontend/app.py
```
Això desplegarà una aplicació accessible des del navegador web a `http://localhost:8501`.

## Exemple de consulta

**Consulta del docent:**
> "Avui a classe de gimnàstica he vist que la Júlia portava talls recents als braços. Quan li he preguntat què li passava, ha intentat amagar-se les mànigues de pressa, s'ha posat nerviosa i ha començat a plorar."

**Resposta del sistema:**
L'assistent detectarà l'alerta sota la taxonomia `autolesions`, anonimitzarà automàticament el nom "Júlia" pel token genèric `[ALUMNA_1]` durant el procés de consulta als LLM, i retornarà pautes precises per a la protecció immediata emmarcades dins els protocols vigents educatius, evitant un to alarmista però aplicant mesures de prioritat de salut mental i física, junt amb les instruccions específiques que cal realitzar dins del centre.

## Base documental

El sistema recupera informació des d'una col·lecció indexada alimentada per documentació escolar especialitzada de la Generalitat de Catalunya:
* **Protocols d'actuació**: (Violència, Assetjament, Transgènere, etc.)
* **Circuits d'intervenció**: Passos formals i procedimentals que els docents han d'aplicar.
* **Normativa legal**: Decrets de convivència escolar, lleis de protecció de menors (com la LOPIVI).
* **Guies pràctiques**: Orientacions educatives de prevenció.

## Sistema de recuperació

- **Embeddings**: El sistema codifica els textos utilitzant el model multilingual `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` per capturar adequadament la semàntica del català i del castellà.
- **Qdrant**: Utilitzat com a base de dades vectorial. S'empra la distància *Cosinus* per retornar els documents (Candidats Inicials Top-K) que tenen major grau de similitud amb la consulta original enriquida.
- **Reranking (Reordenació)**: Atès que la fase de *Retrieval* inicial pot retornar fragments enganyosos a causa de la naturalesa bidireccional dels embeddings, s'aplica una segona fase on un model de tipus *Cross-Encoder* (`mmarco-mMiniLMv2-L12-H384-v1`) examina cada parella [Consulta, Fragment Recuperat] detalladament i els assigna una puntuació rigorosa final, descartant els menys pertinents.

## Limitacions actuals

- **No substitutiu**: El sistema no actua en cap cas com a substitut d'un diagnòstic mèdic, legal, directiu o del servei d'Inspecció Educativa.
- **Risc d'Al·lucinacions**: Tot i ancorar la generació mitjançant RAG, atès el funcionament estocàstic dels grans models de llenguatge (LLM), encara existeix la possibilitat que es puguin extrapolar lleugeres afirmacions fora de protocol si la base documental interna manca d'informació clara per a una qüestió particular.
- **Manteniment Normatiu**: Requereix que els administradors re-indexin i mantinguin actualitzats els documents PDF interns a mesura que surten noves lleis i decrets oficials.

## Treball futur

- Afegir integració amb els Sistemes d'Informació de Centres per poder extreure de manera segura històrics d'incidències per contextualitzar de forma més automàtica.
- Incorporar una infraestructura d'avaluació en continu, avaluant les mètriques de precisió semàntica (*Retrieval Accuracy*).
- Desplegament de l'aplicació sencer en arquitectures basades en el núvol (Cloud Computing).

## Consideracions ètiques i privacitat

L'ús de la Intel·ligència Artificial en el tractament d'alertes d'alumnes menors d'edat comporta greus responsabilitats legals i un deure de cura excepcional:

* **Compliment RGPD i LOPIVI**: El sistema compleix la normativa mitjançant el seu mòdul dedicat d'anonimització; la informació de caràcter identificable s'elimina dels *prompts* abans que els serveis d'inferència la processin.
* **Protecció del Menor**: El sistema prohibeix i censura explícitament accions i interrogatoris revictimitzadors a les respostes generades. Prioritza sistemàticament la protecció de l'estudiant i una cura centrada en el suport actiu.
* **Traçabilitat**: Es rebutgen solucions *Black Box*. Les actuacions retornades indiquen les fonts documentals utilitzades juntament amb la valoració i decisió adoptada inicialment en la fase de triatge.
* **Minimització de dades**: S'adopta la política de tractar exclusivament les variables indispensables. Cap dada del context de la incidència s'arxiva de forma persistent o insegura dins l'arquitectura del model LLM generatiu.
* **Supervisió humana i decisió (*Human-in-the-loop*)**: El sistema és exclusivament un suport consultiu, i sempre indica explícitament i categòricament als usuaris que les pertinents decisions crítiques formals seran executades per l'equip humà responsable del centre.
