from qdrant_client import models

from src.vector_store.config import COLLECTION_NAME, VECTOR_SIZE
from src.vector_store.qdrant_connection import get_qdrant_client


def recreate_qdrant_collection() -> None:
    """
    Crea o recrea la colección Qdrant.

    IMPORTANTE:
    - En desarrollo va bien porque borra e indexa desde cero.
    - Más adelante, en producción, mejor usar colecciones versionadas.
    """

    client = get_qdrant_client()

    print("=" * 80)
    print("[QDRANT] Recreating collection")
    print("=" * 80)

    print(f"[INFO] Collection name: {COLLECTION_NAME}")
    print(f"[INFO] Vector size: {VECTOR_SIZE}")
    print("[INFO] Distance: Cosine")

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

    print("[OK] Collection recreated successfully.")
    print(f"[INFO] Collection status: {collection_info.status}")
    print(f"[INFO] Points count: {collection_info.points_count}")