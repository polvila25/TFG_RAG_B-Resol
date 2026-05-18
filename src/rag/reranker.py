import time
from typing import List

from sentence_transformers import CrossEncoder

from src.rag.retriever import RetrievedChunk


MAX_RERANK_CHARS = 1200


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
    Reranker basado en CrossEncoder.

    Importante:
    - Debe instanciarse una sola vez.
    - No debe cargarse en cada query.
    - Recibe top_k candidatos de Qdrant.
    - Devuelve top_n chunks finales.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        max_chars: int = MAX_RERANK_CHARS,
    ) -> None:
        self.model_name = model_name
        self.max_chars = max_chars

        start = time.perf_counter()

        self.model = CrossEncoder(model_name)

        end = time.perf_counter()
        print(f"[RERANKER] Model loaded: {model_name}")
        print(f"[RERANKER] Load time: {end - start:.3f}s")

    def _truncate_text(self, text: str) -> str:
        text = text.strip()

        if len(text) <= self.max_chars:
            return text

        return text[:self.max_chars]

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_n: int = 5,
    ) -> List[RerankedChunk]:
        start = time.perf_counter()

        if not chunks:
            return []

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.text and chunk.text.strip()
        ]

        if not valid_chunks:
            return []

        pairs = [
            [query, self._truncate_text(chunk.text)]
            for chunk in valid_chunks
        ]

        print(f"[RERANKER] Candidates: {len(valid_chunks)}")
        print(f"[RERANKER] Top_n: {top_n}")
        print(f"[RERANKER] Max chars per chunk: {self.max_chars}")

        scores = self.model.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False,
        )

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

        end = time.perf_counter()
        print(f"[RERANKER] Inference time: {end - start:.3f}s")

        return reranked_chunks[:top_n]