# Informe Técnico: Arquitectura de Chunks para Circuitos de Actuación (`circuit_actuacio`)

Este documento detalla el diseño arquitectónico, la estructura de datos y el flujo de integración de los chunks correspondientes a los **Circuitos de Actuación** dentro del motor RAG de **b-resol**. 

Dado que los circuitos de actuación originales son representaciones visuales (diagramas de flujo) con múltiples caminos, condiciones y derivaciones, la segmentación lineal tradicional (cortar el texto cada $N$ caracteres) destruiría la lógica secuencial. Para solucionarlo, se ha implementado una arquitectura basada en **Grafos de Decisión Semánticos**.

---

## 1. Concepto Arquitectónico: Del Diagrama Visual al Grafo Semántico

En lugar de tratar un circuito como un texto plano, el sistema lo descompone en **nodos discretos** (chunks). Cada nodo representa un paso específico del circuito, una decisión o una derivación externa. Estos nodos están enlazados entre sí para que el LLM y el sistema RAG puedan "navegar" por el protocolo de la misma manera que un humano seguiría las flechas de un diagrama.

### Tipología de Nodos (`chunk_type`)
La arquitectura define diversos tipos de chunks para caracterizar la naturaleza de cada paso:
*   **`document_identity`**: Nodo raíz que define el propósito general y el alcance del circuito.
*   **`trigger`**: La acción o evento que activa el circuito (ej. conocimiento o sospecha de violencia).
*   **`phase`**: Una etapa genérica del circuito (ej. detección, valoración, comunicación).
*   **`decision_node`**: Un punto de bifurcación crítica donde el camino a seguir depende de ciertas condiciones (ej. "Es una conducta contraria o una falta grave?").
*   **`action_step`**: Un paso puramente operativo (ej. aplicar medidas educativas).
*   **`external_derivation`**: Un punto donde el caso sale del ámbito del centro educativo y pasa a agentes externos (Mossos, DGAIA, Fiscalia).
*   **`classification`**: Clasificación de la infracción o conducta.
*   **`communication`**: Comunicaciones requeridas a partes interesadas o agentes.

---

## 2. Estructura de Datos del Payload del Chunk

Cada nodo del circuito se almacena en formato JSON puro. La estructura de metadatos del `payload` está diseñada para soportar búsquedas vectoriales híbridas y reconstrucción de contexto de grafos:

### A. Enrutamiento y Conectividad (El Grafo)
*   **`step_id`**: Identificador único del paso actual (ej. `circuit_violencia_004_decisio_ambit`).
*   **`previous_step_id`**: Identificador del paso inmediatamente anterior.
*   **`next_step_ids`**: Array con los IDs de los pasos siguientes posibles. Permite al LLM saber exactamente qué opciones hay a continuación y "caminar" por el grafo.

### B. Contenido y Representación Semántica
*   **`text`**: La descripción textual literal de la acción que debe realizarse en este nodo.
*   **`embedding_text`**: Un texto super-enriquecido diseñado exclusivamente para ser vectorizado. Contiene palabras clave adicionales, sinónimos y contexto implícito que maximizan la probabilidad de ser recuperado correctamente por **Qdrant**.
*   **`chunk_title`**: Título claro del nodo para referenciarlo en las respuestas generadas.

### C. Lógica de Decisión Dinámica (`decision_logic`)
Para los nodos de tipo `decision_node`, se incrusta un sub-objeto algorítmico que explica al LLM las rutas lógicas condicionales:
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
> Este diseño permite que, al recuperar este chunk, el modelo generativo sepa exactamente **qué preguntar al usuario** en modo exploratorio (ej. a través de la sugerencia de interacción en el chat) para poder derivarlo al siguiente paso correcto del circuito.

### D. Agentes, Sistemas y Responsables
Los nodos traquean qué entidades deben intervenir en ese momento preciso mediante listas predefinidas:
*   **`actors_involved`** / **`responsible`**: Quién debe ejecutar la acción (ej. *direcció*, *equip de valoració*, *alumnat_menor_18_anys*).
*   **`support_agents`**: Asesoramiento externo pero dentro del ámbito educativo (ej. *EAP*, *USAV*).
*   **`external_agents`**: Entidades fuera de educación obligadas a actuar en derivaciones (ej. *Fiscalia*, *Jutjat de guàrdia*).
*   **`systems`**: Sistemas informáticos oficiales a usar (ej. registro obligatorio en el *REVA*).

### E. Alineación Normativa y Legal
*   **`legal_references`**: Menciones crudas a las normativas vinculantes.
*   **`normalized_legal_references`**: Estructuras normalizadas que mapean la ley exacta para cruzarla de forma relacional con la base de datos de legislación (`legal_support`).

---

## 3. Integración en el Pipeline de Ingesta (El script `llenar_chunks_correct.py`)

Para evitar errores humanos o desalineamientos estructurales en los nodos base proporcionados en los archivos JSON, el script `llenar_chunks_correct.py` actúa como una capa de normalización de validación estricta y auto-completado de inferencia:

1.  **Capa de Recuperación**: El script asegura que todo documento de tipo `circuit_actuacio` recibe obligatoriamente los metadatos `retrieval_layer = "application"` y `application_layer = true`.
2.  **Inferencia de Protocolos Relacionados**: Si un nodo de circuito no define explícitamente a qué protocolo oficial responde, el script cruza el nombre del archivo con un diccionario estático y le asigna la macro-referencia (`protocol_violencia_ambit_educatiu`).
3.  **Inferencia Semántica de Riesgos (`risk_category`)**: 
    *   Si es un circuito determinista (ej. Drogas), se le asigna su categoría fija (`consum_substancies`) mediante reglas de fallback basadas en el nombre del fichero.
    *   Si es un circuito transversal (ej. Violencia, que alberga múltiples violencias dentro), el script evalúa todo el texto semántico del nodo (`build_risk_context_text()`) y mediante una serie de **Reglas de Contenido basadas en Expresiones Regulares Ligeras** (Content Rules) etiqueta el nodo específico con sub-riesgos como *assetjament_escolar* o *maltractament_infantil*.

---

## 4. Beneficios Operativos en el Motor de Triaje y RAG

La transformación de diagramas visuales en estos **Grafos de Decisión Semánticos** en JSON otorga ventajas de alto rendimiento en producción:

1.  **Prevención de Alucinaciones Estructurales**: Al estar codificados mediante un ID propio y punteros directos `next_step_ids`, el LLM se convierte en un simple "caminante del grafo" que no inventa el siguiente paso de un protocolo, sino que lee forzosamente las rutas programadas.
2.  **Recuperación Vectorial Altamente Precisada**: Al indexarse en el vector store, el pipeline puede realizar *Hard-Filtering* estricto (ej. filtrar solo chunks donde `risk_category == "falta_greument_perjudicial"`) antes de usar algoritmos de similitud basados en Embeddings, reduciendo enormemente la latencia.
3.  **Memoria Conversacional Contextual**: En un RAG multi-turno, si el alumno responde "sí, es una falta grave", el generador extrae inmediatamente el `next_step_id` asociado a esa condición del `decision_logic` anterior, y enfoca el `Retrieval` sobre el ID objetivo de ese nodo del circuito.


---

## 5. Estrategia y Modelo de Lenguaje (LLM) Utilizado

Para la generación, extracción y enriquecimiento de estos metadatos estructurados se ha diseñado un pipeline automatizado e híbrido que combina inteligencia artificial y reglas de negocio deterministas:

1. **Modelo de Lenguaje (LLM)**:
   * **Modelo**: **`gpt-4o-mini`** de OpenAI.
   * **Configuración**: Temperatura `0.0` para garantizar un comportamiento determinista, repetitivo y evitar alucinaciones en la clasificación o en los arrays relacionales.
   * **Integración**: Se utiliza la función `.with_structured_output(Schema)` de LangChain combinada con modelos de **Pydantic** (`ProtocolChunkMetadata` y `LegalChunkMetadata`). Esto obliga al LLM a devolver un esquema JSON con tipos de datos estrictamente validados bajo taxonomías predefinidas (`RiskCategory`, `Phase`, `ChunkType`, `SeverityContext`).

2. **Estrategia de Chunking y Enriquecimiento**:
   * **Segmentación Estructural y Jerárquica**: Los documentos se dividen usando cabeceras de Markdown (`MarkdownHeaderTextSplitter`) para protocolos y guías, o bien segmentación por Regex de artículos y apartados numerados para las leyes (LEC, Decret 102/2010).
   * **Prompting de Extracción**: El LLM recibe el contenido del fragmento de texto y el contexto de su ubicación en el documento (cabeceras). A partir de esto, se encarga de resumir y optimizar la búsqueda mediante la redacción del `embedding_text`, identificar a los responsables de las medidas correctivas (`actors_involved`, `responsible`), mapear agentes internos/externos de soporte o derivación, y extraer las referencias normativas.
   * **Mecanismos de Fallback**: Si el LLM falla, no puede ser contactado o produce un error de validación del esquema de salida, el pipeline utiliza funciones deterministicas en Python que calculan automáticamente parámetros como la fase o la categoría de riesgo mediante el mapeo lexema/palabra clave y expresiones regulares aplicadas directamente sobre el texto del chunk.

---

## 6. Taula 1: Esquema de Metadades del Payload del Chunk

A continuació, es descriu l'esquema de metadades estructurades que acompanya el payload de cada chunk de dades (tant de protocols com de lleis i circuits) utilitzat pel motor RAG:

| Camp de la Metadada | Tipus de Dades | Mètode de Càlcul / Inferencia | Descripció i Utilitat en el RAG |
| :--- | :--- | :--- | :--- |
| **`step_id`** / **`id`** | `String` | Assignat estàticament (graf) o derivat de l'estructura. | Identificador únic del fragment a la base de dades vectorial. Permet la traçabilitat exacta de les accions. |
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
| **`legal_references`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Menciones literals de lleis o articles presents al fragment de text. |
| **`normalized_legal_references`** | `List[Object]` | Extret estructuradament per LLM (`gpt-4o-mini`) + normalitzador. | Objectes relacionals (ex. `law_abbreviation == 'LEC'`, `article == '37.1'`) per creuament documental. |
| **`requires_external_activation`** | `Boolean` | Inferred segons la presència de derivacions externes. | Indica si el pas actual exigeix notificar immediatament entitats judicials o policials. |
| **`requires_human_review`** | `Boolean` | Fixat per defecte (`true`). | Defineix si el chunk requereix revisió/aprovació humana en lloc de d'automatització total. |
| **`keywords`** | `List[String]` | Extret estructuradament per LLM (`gpt-4o-mini`). | Llista de conceptes clau per millorar la recuperació per paraules clau exactes. |
| **`language`** | `String` | Fixat per defecte (`"ca"`). | Idioma del contingut textual. |
| **`jurisdiction`** | `String` | Fixat per defecte (`"Catalunya"`). | Àmbit territorial legislatiu. |

