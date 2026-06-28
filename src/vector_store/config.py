from pathlib import Path

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_PATH = PROJECT_ROOT / "data" / "procesed" / "chunks" / "all_chunks.json"

EMBEDDED_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "procesed"
    / "embeddings"
    / "all_chunks_embedded.json"
)

# Carpeta local on Qdrant desarà la BD vectorial
QDRANT_LOCAL_PATH = PROJECT_ROOT / "storage" / "qdrant"

# ============================================================
# QDRANT CONFIG
# ============================================================
import os

# Mode actual recomanat per a desenvolupament:
QDRANT_MODE = os.getenv("QDRANT_MODE", "local")

# Futur mode Docker/servidor:
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Mode Cloud (Qdrant Cloud)
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "bresol_knowledge_base_minilm"

# ============================================================
# EMBEDDING MODEL CONFIG
# ============================================================

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384

DISTANCE_NAME = "Cosine"

# ============================================================
# INDEXING CONFIG
# ============================================================

EMBEDDING_BATCH_SIZE = 32
UPLOAD_BATCH_SIZE = 64

UUID_NAMESPACE = "bresol-rag-bbdd-documents-v1"