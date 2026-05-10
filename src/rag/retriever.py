from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from src.vector_store.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    QDRANT_LOCAL_PATH,
)


class RetrievedChunk:
    def __init__(
        self,
        point_id: str,
        score: float,
        payload: Dict[str, Any],
    ) -> None:
        self.point_id = point_id
        self.score = score
        self.payload = payload

    @property
    def text(self) -> str:
        return self.payload.get("text", "")

    @property
    def source_document(self) -> str:
        return self.payload.get("source_document", "")

    @property
    def source_page(self) -> Any:
        return self.payload.get("source_page")

    @property
    def chunk_title(self) -> str:
        return self.payload.get("chunk_title", "")


class QdrantRetriever:
    """
    Retriever semántico sobre Qdrant.

    Responsabilidades:
    - Generar embedding de la query.
    - Aplicar filtros de payload.
    - Recuperar top_k candidatos.
    - Devolver chunks con score y metadatos.
    """

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        qdrant_path: str = str(QDRANT_LOCAL_PATH),
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        self.collection_name = collection_name
        self.client = QdrantClient(path=qdrant_path)
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def _build_filter(
        self,
        retrieval_layer: Optional[str] = None,
        risk_category: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        language: Optional[str] = None,
        jurisdiction: Optional[str] = "Catalunya",
    ) -> Optional[models.Filter]:
        must_conditions: List[models.Condition] = []

        if retrieval_layer and retrieval_layer != "unknown":
            must_conditions.append(
                models.FieldCondition(
                    key="retrieval_layer",
                    match=models.MatchValue(value=retrieval_layer),
                )
            )

        if risk_category and risk_category != "unknown":
            must_conditions.append(
                models.FieldCondition(
                    key="risk_category",
                    match=models.MatchValue(value=risk_category),
                )
            )

        if document_types:
            must_conditions.append(
                models.FieldCondition(
                    key="document_type",
                    match=models.MatchAny(any=document_types),
                )
            )

        if language:
            must_conditions.append(
                models.FieldCondition(
                    key="language",
                    match=models.MatchValue(value=language),
                )
            )

        if jurisdiction:
            must_conditions.append(
                models.FieldCondition(
                    key="jurisdiction",
                    match=models.MatchValue(value=jurisdiction),
                )
            )

        if not must_conditions:
            return None

        return models.Filter(must=must_conditions)

    def retrieve(
        self,
        query: str,
        retrieval_layer: Optional[str] = None,
        risk_category: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        top_k: int = 15,
        language: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Recupera chunks desde Qdrant.

        query:
            Query enriquecida.

        top_k:
            Número de candidatos iniciales antes del reranking.
        """

        query_vector = self.embedding_model.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        query_filter = self._build_filter(
            retrieval_layer=retrieval_layer,
            risk_category=risk_category,
            document_types=document_types,
            language=language,
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        chunks: List[RetrievedChunk] = []

        for hit in results.points:
            chunks.append(
                RetrievedChunk(
                    point_id=str(hit.id),
                    score=float(hit.score),
                    payload=hit.payload or {},
                )
            )

        return chunks

    def close(self) -> None:
        self.client.close()