from typing import List

from sentence_transformers import CrossEncoder

from src.rag.retriever import RetrievedChunk


class RerankedChunk(RetrievedChunk):
    def __init__(
        self,
        base_chunk: RetrievedChunk,
        rerank_score: float,
    ) -> None:
        super().__init__(
            point_id=base_chunk.point_id,
            score=base_chunk.score,
            payload=base_chunk.payload,
        )
        self.rerank_score = rerank_score


class CrossEncoderReranker:
    """
    Reranker basado en CrossEncoder multilingüe.

    Responsabilidades:
    - Recibe chunks recuperados por Qdrant.
    - Compara query + texto de cada chunk usando un modelo (ej: BAAI/bge-reranker-v2-m3).
    - Reordena por relevancia.
    - Devuelve top_n final.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
    ) -> None:
        # Usamos BAAI/bge-reranker-v2-m3 porque soporta catalán eficientemente.
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_n: int = 5,
    ) -> List[RerankedChunk]:
        if not chunks:
            return []

        pairs = [
            [query, chunk.text]
            for chunk in chunks
            if chunk.text.strip()
        ]

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.text.strip()
        ]

        if not pairs:
            return []

        scores = self.model.predict(pairs)

        reranked_chunks = [
            RerankedChunk(
                base_chunk=chunk,
                rerank_score=float(score),
            )
            for chunk, score in zip(valid_chunks, scores)
        ]

        reranked_chunks.sort(
            key=lambda chunk: chunk.rerank_score,
            reverse=True,
        )

        return reranked_chunks[:top_n]
