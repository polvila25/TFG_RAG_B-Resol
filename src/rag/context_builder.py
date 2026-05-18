from typing import List

from src.rag.reranker import RerankedChunk


class ContextBuilder:
    """
    Construye contexto estructurado para el LLM.

    Objetivos:
    - Mantener trazabilidad.
    - Incluir documento y página.
    - Evitar pasar chunks sin fuente.
    - Dar formato claro al contexto.
    """

    def __init__(
        self,
        max_chars_per_chunk: int = 1800,
        max_total_chars: int = 9000,
    ) -> None:
        self.max_chars_per_chunk = max_chars_per_chunk
        self.max_total_chars = max_total_chars

    def _truncate(self, text: str, max_chars: int) -> str:
        text = text.strip()

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + "..."

    def build(self, chunks: List[RerankedChunk]) -> str:
        context_blocks = []
        total_chars = 0

        for index, chunk in enumerate(chunks, start=1):
            payload = chunk.payload

            source_document = payload.get("source_document", "Document desconegut")
            source_page = payload.get("source_page", "Pàgina no especificada")
            chunk_title = payload.get("chunk_title", "Fragment sense títol")
            document_type = payload.get("document_type", "Tipus no especificat")
            retrieval_layer = payload.get("retrieval_layer", "Capa no especificada")
            risk_category = payload.get("risk_category", "Categoria no especificada")

            text = payload.get("text", "")
            text = self._truncate(text, self.max_chars_per_chunk)

            block = f"""
[FONT {index}]
Document: {source_document}
Pàgina: {source_page}
Títol o apartat: {chunk_title}
Tipus de document: {document_type}
Capa documental: {retrieval_layer}
Categoria de risc: {risk_category}
Vector score: {chunk.score:.4f}
Rerank score: {chunk.rerank_score:.4f}

Contingut:
{text}
""".strip()

            if total_chars + len(block) > self.max_total_chars:
                break

            context_blocks.append(block)
            total_chars += len(block)

        if not context_blocks:
            return (
                "No s'ha recuperat cap context documental suficient "
                "per respondre amb garanties."
            )

        return "\n\n" + ("=" * 80) + "\n\n".join(context_blocks)