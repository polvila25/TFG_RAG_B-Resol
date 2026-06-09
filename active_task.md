# Estado de la Tarea Actual

## Objetivo Principal
Estandarización de respuestas RAG y manejo de la ambigüedad en los reportes de alertas escolares.

---

## Checklist de Subtareas

- [x] Integrar citas naturales y fluidas en `prompt_builder.py` (citar únicamente el documento si no se encuentra la página en el contexto, prohibiendo alucinaciones de páginas).
- [x] Modificar `response_planner.py` para manejar consultas ambiguas o con puntuación de información insuficiente (`score <= 3` o `urgency_level == "ambiguous"`).
- [x] Establecer "Indagación a través del Xat y revisión del Dashboard" como la **Acción Prioritaria Nº 1** ante la presencia de ambigüedad, evitando el bloqueo completo de la recuperación RAG y ofreciendo orientación preventiva basada en protocolos.
- [x] Ajustar la estructura de salida y validaciones de `QueryAnalyzer` en `query_analizer.py` para incorporar la extracción predictiva de `urgency_level`, `has_implicated_parties` y `detected_features`.
- [x] Enriquecer las variables del generador del pipeline en `rag_pipeline.py` para inyectar estos metadatos y permitir que la plantilla de respuesta declare explícitamente el nivel de urgencia/intensidad al inicio de la recomendación.

---

## Archivos en Foco

Los siguientes archivos del proyecto han sido modificados para completar y estandarizar la tarea actual:

1. **[`src/rag/schemas.py`](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/rag/schemas.py):** Modelo del objeto `QueryAnalysis` con los nuevos campos de triaje.
2. **[`src/rag/query_analizer.py`](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/rag/query_analizer.py):** Extracción, normalización y fallback de urgencia, implicados y etiquetas de taxonomía.
3. **[`src/rag/rag_pipeline.py`](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/rag/rag_pipeline.py):** Inyección de metadatos predictivos en el diccionario de variables del generador.
4. **[`src/bresol_context/response_planner.py`](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/bresol_context/response_planner.py):** Lógica flexibilizada del planificador para no bloquear RAG ante alertas ambiguas.
5. **[`src/rag/prompt_builder.py`](file:///c:/Users/polvi/OneDrive/Escriptori/TFG/TFG_RAG_B-Resol/src/rag/prompt_builder.py):** Modificación del prompt del sistema para citas naturales, asertividad directa, determinación de urgencia e integración de la suite b-resol.
