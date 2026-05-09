from qdrant_client import QdrantClient

from src.vector_store.config import (
    QDRANT_MODE,
    QDRANT_LOCAL_PATH,
    QDRANT_HOST,
    QDRANT_PORT,
)


def get_qdrant_client() -> QdrantClient:
    """
    Devuelve un cliente Qdrant.

    Modo local:
        Guarda la base vectorial dentro del proyecto:
        storage/qdrant/

    Modo server:
        Se conecta a Qdrant levantado con Docker o servidor.
    """

    if QDRANT_MODE == "local":
        QDRANT_LOCAL_PATH.mkdir(parents=True, exist_ok=True)

        return QdrantClient(
            path=str(QDRANT_LOCAL_PATH),
        )

    if QDRANT_MODE == "server":
        return QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            timeout=60,
        )

    raise ValueError(
        f"Invalid QDRANT_MODE: {QDRANT_MODE}. "
        "Use 'local' or 'server'."
    )