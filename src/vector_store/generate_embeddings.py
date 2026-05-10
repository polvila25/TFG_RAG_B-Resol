import json
from pathlib import Path
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.vector_store.config import (
    CHUNKS_PATH,
    EMBEDDED_CHUNKS_PATH,
    EMBEDDING_MODEL_NAME,
    VECTOR_SIZE,
)


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected all_chunks.json to contain a list of chunks.")

    return data


def validate_chunk_for_embedding(chunk: Dict[str, Any], index: int) -> None:
    chunk_id = chunk.get("id")
    payload = chunk.get("payload")

    if not chunk_id:
        raise ValueError(f"Chunk at index {index} has no 'id'.")

    if not isinstance(payload, dict):
        raise ValueError(f"Chunk {chunk_id} has no valid payload.")

    embedding_text = payload.get("embedding_text")
    text = payload.get("text")

    if not isinstance(embedding_text, str) or not embedding_text.strip():
        raise ValueError(f"Chunk {chunk_id} has empty payload.embedding_text.")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Chunk {chunk_id} has empty payload.text.")


def generate_embeddings(
    chunks: List[Dict[str, Any]],
    batch_size: int = 32,
) -> List[Dict[str, Any]]:
    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    embedded_chunks: List[Dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        validate_chunk_for_embedding(chunk, i)

    texts = [chunk["payload"]["embedding_text"] for chunk in chunks]

    print(f"[INFO] Generating embeddings for {len(texts)} chunks...")

    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    for chunk, vector in zip(chunks, vectors):
        vector_list = vector.tolist()

        if len(vector_list) != VECTOR_SIZE:
            raise ValueError(
                f"Invalid vector size for chunk {chunk.get('id')}. "
                f"Expected {VECTOR_SIZE}, got {len(vector_list)}."
            )

        chunk["vector"] = vector_list
        embedded_chunks.append(chunk)

    return embedded_chunks


def save_embedded_chunks(chunks: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"[OK] Embedded chunks saved to: {path}")


def generate_and_save_embeddings() -> List[Dict[str, Any]]:
    chunks = load_chunks(CHUNKS_PATH)
    print(f"[INFO] Loaded chunks: {len(chunks)}")

    embedded_chunks = generate_embeddings(chunks)

    save_embedded_chunks(embedded_chunks, EMBEDDED_CHUNKS_PATH)
    return embedded_chunks


def main() -> None:
    generate_and_save_embeddings()


if __name__ == "__main__":
    main()