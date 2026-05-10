from typing import List
from src.rag.reranker import RerankedChunk

class ContextBuilder:
    """
    Construye el contexto final a partir de los chunks recuperados y reordenados.
    Prepara el texto de manera estructurada para que el LLM pueda fundamentar y citar sus respuestas.
    """
    
    @staticmethod
    def build(chunks: List[RerankedChunk]) -> str:
        if not chunks:
            return "No s'ha trobat informació rellevant als protocols per a aquesta consulta."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            title = chunk.chunk_title or "Document sense títol"
            doc_name = chunk.source_document or "Font desconeguda"
            page = chunk.source_page
            
            page_info = f", Pàgina {page}" if page else ""
            
            part = (
                f"--- FRAGMENT {i} ---\n"
                f"Títol: {title}\n"
                f"Font original: {doc_name}{page_info}\n"
                f"Contingut:\n{chunk.text}\n"
            )
            context_parts.append(part)
            
        return "\n\n".join(context_parts)
