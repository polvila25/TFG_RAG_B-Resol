# Contexto del Proyecto: TFG_RAG_B-Resol

Este archivo contiene la especificación de contexto a largo plazo para el proyecto **TFG_RAG_B-Resol**. Su propósito es servir de memoria histórica sobre el propósito del sistema, su arquitectura y sus reglas de negocio.

---

## Propósito del Proyecto

El proyecto es un **Trabajo de Final de Grado (TFG)** enfocado en el diseño e implementación de un sistema **RAG (Retrieval-Augmented Generation) Agéntico** en Python. 

Su función principal es ayudar a los docentes, orientadores y responsables de convivencia en el entorno escolar a gestionar, categorizar y resolver de forma ágil y protocolada las alertas (tanto anónimas como identificadas) de incidencias escolares sensibles (tales como acoso escolar, ciberacoso, trastornos de conducta alimentaria, autolesiones o conductas de riesgo). El sistema está integrado con el entorno y la suite de gestión de la plataforma **b-resol**.

---

## Arquitectura y Módulos Clave

El proyecto está estructurado como una solución modular que combina modelos fundacionales de lenguaje (LLMs) con bases de datos vectoriales y lógica de negocio determinista:

1. **Frontend (`frontend/app.py`):** Desarrollado con **Streamlit**, provee una interfaz gráfica interactiva en formato chat de soporte para los docentes, con un formulario de feedback y avaluación final integrado.
2. **Triaje y Clasificación (`src/bresol_context` y `src/rag/query_analizer.py`):**
   - **`BresolIntakeAnalyzer`**: Realiza el intake inicial de la alerta determinando el riesgo y la completitud del reporte.
   - **`QueryAnalyzer`**: Analiza semánticamente la intención del docente extraída de la consulta, identificando el tipo de consulta (`application`, `legal_support`, `mixed`), el nivel de urgencia/intensidad (`high`, `medium`, `low`, `ambiguous`), la presencia de implicados (`has_implicated_parties`) y la categoría de riesgo principal.
3. **Planificador de Ruta (`src/bresol_context/response_planner.py`):** Decide de forma condicional qué tipo de respuesta aplicar y si se debe ejecutar el RAG documental.
4. **Recuperación Semántica y Re-ranking (`src/rag/retriever.py` y `src/rag/reranker.py`):**
   - **`QdrantRetriever`**: Recupera fragmentos normativos y de protocolos escolares de la Generalitat de Catalunya almacenados en una base de datos vectorial local **Qdrant**.
   - **`CrossEncoderReranker`**: Reordena semánticamente los fragmentos usando un modelo Cross-Encoder (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) para mejorar la relevancia del contexto.
5. **Generador de Respuestas (`src/rag/generator.py` y `src/rag/prompt_builder.py`):** Genera la guía final personalizada para el docente combinando el contexto recuperado y las directivas de trazabilidad.
6. **Integración Extterna:** Conexión con **Google Sheets** (mediante la librería `gspread`) para recopilar las evaluaciones del formulario de feedback.

---

## Reglas de Negocio Críticas

- **Protección y Privacidad de Menores (RGPD / LOPIVI):**
  Es una directriz estricta omitir datos de carácter personal en las respuestas del modelo. Si una alerta es de carácter anónimo, el sistema tiene prohibido interrogar o presionar para obtener nombres reales. Debe priorizar preguntas periféricas de contexto (espacio, lloc, curs).
- **Cero Alucinaciones en Citas Documentales:**
  El sistema tiene prohibido inventar o alucinar datos, leyes o números de página. Las citas normativas o de protocolos de la Generalitat de Catalunya deben hacerse de forma natural e integrada en el texto. **Si no consta el número de página en los fragmentos de contexto recuperados, el LLM únicamente citará el nombre del documento**, omitiendo la página para evitar invenciones.
- **Acciones Directas y Trazabilidad:**
  El sistema no debe comportarse como un consultor pasivo (ej. "revisa el protocolo"). Debe generar listas de acciones estructuradas, secuenciales e imperativas (ej. *"És fonamental que el primer pas a realitzar sigui..."*). Cada recomendación práctica debe vincularse directamente con una herramienta de b-resol (*Dashboard*, *Xat*, *Identificació*, *Característiques*, *Actuaciones*, *Fitxers*, *Specialist*, *Historial PDF*) para garantizar la trazabilidad legal del caso.
- **Manejo Gradual de Ambigüedad:**
  Ante alertas con poca información o ambiguas, el RAG documental no se bloquea; se realiza una búsqueda preliminar y se instruye de forma absoluta que la **Acción Prioritaria Nº 1** es indagar y esbrinar detalles usando el **Xat** y el **Dashboard** para validar indicios antes de activar medidas formales del centro.
