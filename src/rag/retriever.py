import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from uuid import uuid4

'''
Módulo de gestión del vector store semántico.
Contiene la clase VectorStore, que indexa, almacena y busca fragmentos de texto usando FAISS y embeddings.
Permite añadir documentos y realizar búsquedas por similitud.
'''
class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        dimension = len(self.embeddings.embed_query("hello world"))
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

    def search_docs(self, query, k=5):
        results = self.vector_store.similarity_search(query, k=k)
        return results