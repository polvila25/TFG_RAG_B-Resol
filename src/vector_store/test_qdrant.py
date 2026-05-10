from qdrant_client import QdrantClient

client = QdrantClient(path="storage/qdrant")
methods = [m for m in dir(client) if not m.startswith("_")]
with open("methods.txt", "w") as f:
    f.write(str(methods))
print("Saved methods to methods.txt")
