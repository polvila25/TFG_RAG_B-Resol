import os
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from uuid import uuid4

'''
Módulo de gestión del vector store semántico.
Contiene la clase VectorStore, que indexa, almacena y busca fragmentos de texto usando FAISS y embeddings.
Ahora con PERSISTENCIA: guarda y carga los vectores desde el disco para no reprocesar el PDF.
'''
class VectorStore:
    def __init__(self, persist_dir="data/vector_store"):
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        # Comprobamos si ya existe una base de datos guardada en la carpeta
        if os.path.exists(os.path.join(self.persist_dir, "index.faiss")):
            # Si existe, la cargamos directamente (¡Súper rápido!)
            self.vector_store = FAISS.load_local(
                folder_path=self.persist_dir,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True # Requerido por FAISS por seguridad local
            )
        else:
            # Si no existe, creamos una vacía desde cero
            dimension = len(self.embeddings.embed_query("hola món"))
            self.index = faiss.IndexFlatL2(dimension)
            self.vector_store = FAISS(
                embedding_function=self.embeddings,
                index=self.index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )

    def add_docs(self, list_of_docs):
        uuids = [str(uuid4()) for _ in range(len(list_of_docs))]
        self.vector_store.add_documents(documents=list_of_docs, ids=uuids)
        
        # NUEVO: Guarda automáticamente los vectores en el disco después de añadirlos
        # Aseguramos que la carpeta exista
        os.makedirs(self.persist_dir, exist_ok=True)
        self.vector_store.save_local(self.persist_dir)

    def search_docs(self, query, k=6):
        results = self.vector_store.max_marginal_relevance_search(query, k=k, fetch_k=20)
        return results