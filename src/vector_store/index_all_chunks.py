from src.vector_store.create_collection import recreate_qdrant_collection
from src.vector_store.create_payload_indexes import create_payload_indexes
from src.vector_store.generate_embeddings import generate_and_save_embeddings
from src.vector_store.upload_points import upload_embedded_chunks


def index_all_chunks() -> None:
    """
    Pipeline completo de indexación.

    Este script hace:

    1. Crear/recrear colección Qdrant.
    2. Crear índices de payload.
    3. Leer all_chunks.json.
    4. Validar chunks.
    5. Generar embeddings sobre payload.embedding_text.
    6. Guardar all_chunks_embedded.json.
    7. Crear Points.
    8. Subir Points a Qdrant.

    Este script NO hace recuperación.
    Este script NO hace búsqueda.
    Este script SOLO indexa.
    """

    print("\n" + "#" * 100)
    print("# BCN-RESOL RAG — QDRANT INDEXING PIPELINE")
    print("#" * 100)

    print("\n[STEP 1] Recreate Qdrant collection")
    recreate_qdrant_collection()

    print("\n[STEP 2] Create payload indexes")
    create_payload_indexes()

    print("\n[STEP 3] Generate embeddings from all_chunks.json")
    embedded_chunks = generate_and_save_embeddings()

    print("\n[STEP 4] Upload Points to Qdrant")
    upload_embedded_chunks(embedded_chunks)

    print("\n" + "#" * 100)
    print("# INDEXING COMPLETED SUCCESSFULLY")
    print("#" * 100)


if __name__ == "__main__":
    index_all_chunks()