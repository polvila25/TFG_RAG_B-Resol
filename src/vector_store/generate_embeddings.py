import uuid
from typing import Any, Dict, Iterable, List

from qdrant_client import models
from tqdm import tqdm

from src.vector_store.config import (
    COLLECTION_NAME,
    UPLOAD_BATCH_SIZE,
    UUID_NAMESPACE,
    VECTOR_SIZE,
)
from src.vector_store.qdrant_connection import get_qdrant_client


Chunk = Dict[str, Any]


PAYLOAD_FIELDS = [
    "text",
    "embedding_text",
    "chunk_title",
    "chunk_type",
    "document_type",
    "representation_type",
    "retrieval_layer",
    "application_layer",
    "source_document",
    "source_page",
    "language",
    "domain",
    "jurisdiction",
    "phase",
    "procedure",
    "related_protocols",
    "previous_step_id",
    "next_step_ids",
    "risk_category",
    "requires_human_review",
    "keywords",
]


def deterministic_uuid_from_chunk_id(chunk_id: str) -> str:
    """
    Genera un UUID determinista a partir del chunk_id.

    Mismo chunk_id -> mismo UUID.
    Esto evita duplicados al reindexar.
    """

    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, UUID_NAMESPACE)
    return str(uuid.uuid5(namespace, chunk_id))


def validate_embedded_chunk(chunk: Chunk, index: int) -> None:
    """
    Valida que el chunk tenga vector antes de subirlo a Qdrant.
    """

    chunk_id = chunk.get("id")
    payload = chunk.get("payload")
    vector = chunk.get("vector")

    if not chunk_id:
        raise ValueError(f"Chunk at index {index} has no id.")

    if not isinstance(payload, dict):
        raise ValueError(f"Chunk {chunk_id} has invalid payload.")

    if not isinstance(vector, list):
        raise ValueError(
            f"Chunk {chunk_id} has no vector. "
            "Embeddings must be generated before uploading."
        )

    if len(vector) != VECTOR_SIZE:
        raise ValueError(
            f"Chunk {chunk_id} has invalid vector size. "
            f"Expected {VECTOR_SIZE}, got {len(vector)}."
        )

    embedding_text = payload.get("embedding_text")
    text = payload.get("text")

    if not isinstance(embedding_text, str) or not embedding_text.strip():
        raise ValueError(f"Chunk {chunk_id} has empty embedding_text.")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Chunk {chunk_id} has empty text.")


def build_qdrant_payload(chunk: Chunk) -> Dict[str, Any]:
    """
    Construye el payload que se guardará en Qdrant.
    """

    original_payload = chunk["payload"]

    qdrant_payload: Dict[str, Any] = {
        "chunk_id": chunk["id"],
    }

    for field in PAYLOAD_FIELDS:
        qdrant_payload[field] = original_payload.get(field)

    return qdrant_payload


def chunk_to_point(chunk: Chunk) -> models.PointStruct:
    """
    Convierte un chunk embebido en un PointStruct de Qdrant.
    """

    chunk_id = str(chunk["id"])
    point_id = deterministic_uuid_from_chunk_id(chunk_id)

    return models.PointStruct(
        id=point_id,
        vector=chunk["vector"],
        payload=build_qdrant_payload(chunk),
    )


def batched(items: List[Any], batch_size: int) -> Iterable[List[Any]]:
    """
    Divide una lista en lotes.
    """

    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def build_points_from_chunks(chunks: List[Chunk]) -> List[models.PointStruct]:
    """
    Convierte todos los chunks embebidos en Points de Qdrant.
    """

    print("=" * 80)
    print("[POINTS] Building Qdrant points")
    print("=" * 80)

    points: List[models.PointStruct] = []

    for index, chunk in enumerate(chunks):
        validate_embedded_chunk(chunk, index)
        point = chunk_to_point(chunk)
        points.append(point)

    print(f"[OK] Points built: {len(points)}")

    return points


def upload_points_to_qdrant(points: List[models.PointStruct]) -> None:
    """
    Sube los Points a Qdrant por lotes.
    """

    client = get_qdrant_client()

    print("=" * 80)
    print("[QDRANT] Uploading points")
    print("=" * 80)

    print(f"[INFO] Collection: {COLLECTION_NAME}")
    print(f"[INFO] Points to upload: {len(points)}")
    print(f"[INFO] Upload batch size: {UPLOAD_BATCH_SIZE}")

    total_uploaded = 0
    batches = list(batched(points, UPLOAD_BATCH_SIZE))

    for batch in tqdm(batches, desc="Uploading to Qdrant"):
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True,
            )

            total_uploaded += len(batch)

        except Exception as exc:
            print("[ERROR] Failed while uploading batch to Qdrant.")
            print(f"[ERROR] Batch size: {len(batch)}")
            print(f"[ERROR] Exception: {exc}")
            raise

    collection_info = client.get_collection(
        collection_name=COLLECTION_NAME,
    )

    print("[OK] Upload completed.")
    print(f"[INFO] Uploaded points: {total_uploaded}")
    print(f"[INFO] Qdrant points count: {collection_info.points_count}")


def upload_embedded_chunks(chunks: List[Chunk]) -> None:
    """
    Pipeline:
    1. Convierte chunks en Points.
    2. Sube Points a Qdrant.
    """

    points = build_points_from_chunks(chunks)

    upload_points_to_qdrant(points)