from qdrant_client import models

from src.vector_store.config import COLLECTION_NAME, VECTOR_SIZE
from src.vector_store.qdrant_connection import get_qdrant_client


def recreate_qdrant_collection() -> None:
    """
    Crea o recrea la col·lecció Qdrant.

    IMPORTANT:
    - En desenvolupament va bé perquè esborra i indexa des de zero.
    - Més endavant, en producció, millor usar col·leccions versionades.
    """

    client = get_qdrant_client()

    print("=" * 80)
    print("[QDRANT] Recreant col·lecció")
    print("=" * 80)

    print(f"[INFO] Nom de la col·lecció: {COLLECTION_NAME}")
    print(f"[INFO] Mida del vector: {VECTOR_SIZE}")
    print("[INFO] Distància: Cosinus")

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )

    collection_info = client.get_collection(
        collection_name=COLLECTION_NAME,
    )

    print("[OK] Col·lecció recreada correctament.")
    print(f"[INFO] Estat de la col·lecció: {collection_info.status}")
    print(f"[INFO] Recompte de punts: {collection_info.points_count}")