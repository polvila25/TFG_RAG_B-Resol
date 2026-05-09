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

# Carpeta local donde Qdrant guardará la BD vectorial
QDRANT_LOCAL_PATH = PROJECT_ROOT / "storage" / "qdrant"

# ============================================================
# QDRANT CONFIG
# ============================================================

# Modo actual recomendado para desarrollo:
QDRANT_MODE = "local"

# Futuro modo Docker/servidor:
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

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