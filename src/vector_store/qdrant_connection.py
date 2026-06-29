from qdrant_client import QdrantClient

from src.vector_store.config import (
    QDRANT_MODE,
    QDRANT_LOCAL_PATH,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_URL,
    QDRANT_API_KEY,
)


def get_qdrant_client() -> QdrantClient:
    """
    Retorna un client Qdrant.

    Mode local:
        Desa la base vectorial dins del projecte:
        data/qdrant_db/

    Mode server:
        Es connecta a Qdrant aixecat amb Docker o servidor.
        
    Mode cloud:
        Es connecta a Qdrant Cloud mitjançant URL i API Key.
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
        
    if QDRANT_MODE == "cloud":
        if not QDRANT_URL or not QDRANT_API_KEY:
            raise ValueError("QDRANT_URL i QDRANT_API_KEY han d'estar definits a .env per al mode cloud.")
        return QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=60,
        )

    raise ValueError(
        f"Invalid QDRANT_MODE: {QDRANT_MODE}. "
        "Use 'local' or 'server'."
    )