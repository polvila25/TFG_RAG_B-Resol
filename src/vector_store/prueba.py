import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para poder importar 'src'
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from src.vector_store.config import COLLECTION_NAME

client = QdrantClient(path="storage/qdrant")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

query = "Possible cas de nen de 17 anys que consumeix marihuana i arriba a l'escola drogat cada dia. El seu comportament ha canviat i el seu rendiment acadèmic ha baixat."

query_vector = model.encode(
    query,
    normalize_embeddings=True,
).tolist()

query_filter = models.Filter(
    must=[
        models.FieldCondition(
            key="retrieval_layer",
            match=models.MatchValue(value="application"),
        ),
        models.FieldCondition(
            key="risk_category",
            match=models.MatchValue(value="consum_substancies"),
        ),
    ]
)

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vector,
    query_filter=query_filter,
    limit=5,
    with_payload=True,
    with_vectors=False,
)

for hit in results.points:
    print("Score:", hit.score)
    print("Title:", hit.payload.get("chunk_title"))
    print("Document:", hit.payload.get("source_document"))
    print("Page:", hit.payload.get("source_page"))
    print("Layer:", hit.payload.get("retrieval_layer"))
    print("Risk:", hit.payload.get("risk_category"))
    print()