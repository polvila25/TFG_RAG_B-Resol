from qdrant_client import models

from src.vector_store.config import COLLECTION_NAME
from src.vector_store.qdrant_connection import get_qdrant_client


PAYLOAD_INDEXES = {
    "retrieval_layer": models.PayloadSchemaType.KEYWORD,
    "application_layer": models.PayloadSchemaType.BOOL,
    "document_type": models.PayloadSchemaType.KEYWORD,
    "representation_type": models.PayloadSchemaType.KEYWORD,
    "risk_category": models.PayloadSchemaType.KEYWORD,
    "procedure": models.PayloadSchemaType.KEYWORD,
    "source_document": models.PayloadSchemaType.KEYWORD,
    "language": models.PayloadSchemaType.KEYWORD,
    "jurisdiction": models.PayloadSchemaType.KEYWORD,
    "related_protocols": models.PayloadSchemaType.KEYWORD,
}


def create_payload_indexes() -> None:
    """
    Crea índices de payload en Qdrant.

    Esto será útil para búsquedas filtradas por:
    - application / legal_support
    - risk_category
    - document_type
    - language
    - jurisdiction
    """

    client = get_qdrant_client()

    print("=" * 80)
    print("[QDRANT] Creating payload indexes")
    print("=" * 80)

    for field_name, field_schema in PAYLOAD_INDEXES.items():
        try:
            print(f"[INFO] Creating index: {field_name}")

            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )

            print(f"[OK] Index created: {field_name}")

        except Exception as exc:
            message = str(exc).lower()

            if "already exists" in message or "already" in message:
                print(f"[INFO] Index already exists: {field_name}")
            else:
                print(f"[ERROR] Failed creating index: {field_name}")
                print(f"[ERROR] {exc}")
                raise