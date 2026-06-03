# Propostes de Millora Arquitectònica RAG per a B-Resol

Com a expert en Intel·ligència Artificial i arquitectures RAG (Retrieval-Augmented Generation), he analitzat l'estructura actual del teu projecte B-Resol (que ja compta amb pràctiques molt avançades com l'enriquiment de queries, filtratge per metadades, i reranking amb CrossEncoders).

A continuació, et presento les **5 millores arquitectòniques de més alt impacte** tenint en compte l'àmbit crític, normatiu i educatiu del projecte.

---

## 1. Implementació de Cerca Híbrida (Dense + Sparse)
Actualment utilitzeu recuperació densa (`self.embedding_model.encode`) a Qdrant. Els vectors densos capturen molt bé la semàntica, però fallen en la recuperació de **paraules clau exactes**.
- **El problema**: En dret i normatives (LOPIVI, protocols específics, noms de formularis), la coincidència exacta de paraules clau és fonamental. Una cerca purament densa pot perdre un article específic si la semàntica general de la frase s'assembla més a un altre.
- **La solució**: Qdrant suporta **Hybrid Search** natiu (combinant vectors densos amb vectors espersos com *SPLADE* o *BM25*). Això permetria fusionar el millor d'ambdós mons (cerca per significat + cerca per paraula clau exacta) abans de fer el pas de reranking.

## 2. Agentic RAG: Avaluació CRAG (Corrective RAG) o Self-Reflection
Tot i que teniu un "Query Analyzer", el procés és lineal: Recuperació -> Generació.
- **El problema**: Si la base de dades no té la informació, el LLM pot acabar al·lucinant un protocol o generant una resposta molt fluixa.
- **La solució**: Incorporar un pas de **reflexió** abans de la generació final. El LLM (o un model més petit) avalua ràpidament si els chunks recuperats realment responen a la pregunta. Si no ho fan, el sistema aplica una re-escriptura de la query (*Query Rewriting*) i torna a buscar, o bé canvia a un mode "fallback" on admet de forma explícita i segura que no hi ha protocol definit.

## 3. Optimització de la Fragmentació (Semantic/Structural Chunking)
En protocols legals i educatius, l'estratègia amb què es tallen els documents (chunking) és tant o més important que l'embedding.
- **El problema**: Si utilitzeu talls de text fixos (ex. 1000 caràcters), podeu estar partint un article de la llei o un pas d'un protocol per la meitat, perdent el context de qui n'és el responsable.
- **La solució**: Utilitzar un **Structural Chunking** o **Semantic Chunking**. Talleu els documents respectant l'estructura dels PDF/Markdown (per títols, subtítols i números d'article). Qdrant permet emmagatzemar el `parent_id` de cada chunk, de manera que quan es recuperi un tros petit molt rellevant, el sistema pugui injectar automàticament el context del chunk pare al prompt (*Parent Document Retriever*).

## 4. GraphRAG per a Protocols (Cerca basada en Grafs)
Els protocols d'actuació (ex. assetjament, suïcidi) són bàsicament arbres de decisions i relacions entre entitats (*Equip directiu -> notifica -> Serveis Territorials*).
- **El problema**: Els RAGs vectorials són dolents responent preguntes globals o seguint passos estrictes on l'ordre i les entitats són inflexibles.
- **La solució**: Combinar Qdrant amb un Graf de Coneixement (GraphRAG). S'extreuen les entitats i les regles dels protocols i es guarden en un graf. Quan arriba una alerta, el sistema pot travessar el graf per assegurar-se que **cap pas intermedi se salta**, obtenint una precisió legal d'actuació que els vectors purs no poden garantir.

## 5. Rendiment: Generació Asíncrona i Streaming Real
Al veure que feu servir Streamlit i un pipeline síncron, en entorns de producció (especialment per a situacions de tensió on el docent vol respostes ràpides) l'espera pot ser frustrant.
- **La solució**: Tota la cadena (`QdrantClient`, `ChatGoogleGenerativeAI`) suporta versions asíncrones (`AsyncQdrantClient`). A més, assegureu-vos d'estar emetent (*streaming*) els tokens directament cap al frontend mentre es genera la resposta, reduint el *Time To First Token (TTFT)* a menys de 1 segon, enlloc d'esperar els 5-10 segons que pot trigar tota la canonada.

---

### Resum Executiu per a B-Resol
L'arquitectura actual (Triage -> Routing -> Retrieval -> CrossEncoder -> Dynamic Prompting) és **excel·lent** i està a nivell de producció de moltes startups. Si hagués de prioritzar els propers passos tècnics, atacaria primer la **Cerca Híbrida (BM25 + Vectors)** i el **Parent Document Retriever**, ja que tenen el cost d'implementació més baix (es poden fer amb la infraestructura actual) però l'impacte més alt en la reducció d'al·lucinacions legals.
