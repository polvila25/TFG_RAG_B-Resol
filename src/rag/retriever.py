import os
import faiss
from qdrant_client import QdrantClient
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain_huggingface import HuggingFaceEmbeddings
from uuid import uuid4

'''
Módulo de gestión del vector store semántico.
Contiene la clase VectorStore, que indexa, almacena y busca fragmentos de texto usando FAISS y embeddings.
Ahora con PERSISTENCIA: guarda y carga los vectores desde el disco para no reprocesar el PDF.
'''
class VectorStore:
    def __init__(self, persist_dir="data/vector_store", collection='normativa_educativa'):
        self.persist_dir = persist_dir
        self.collection_name = collection
        self.embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        #1. Inicialización del Cliente Qdrant con persistencia en disco
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = QdrantClient(path=self.persist_dir)

        # 2. Verificamos y creamos la colección
        if not self.client.collection_exists(collection_name=self.collection_name):
            #obtenemos la dimension del modelo de embeddings
            dimension = len(self.embeddings.embed_query("prueba de dimensión"))
            print(f'Dimension del emmbeding: {dimension}')

            self.client.create_collection(
                collection_name=self.collection_name,
                #configuramos dimension de cada vector y distancia
                vectors_config=VectorParams(
                    size=dimension, 
                    distance=Distance.COSINE # Métrica recomendada para embeddings de texto
                ),
            )

        # 3. Enlace con la abstracción de LangChain
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
      
      # # Comprobamos si ya existe una base de datos guardada en la carpeta
      # if os.path.exists(os.path.join(self.persist_dir, "index.faiss")):
      #     # Si existe, la cargamos directamente (¡Súper rápido!)
      #     self.vector_store
      #     self.vector_store = FAISS.load_local(
      #         folder_path=self.persist_dir,
      #         embeddings=self.embeddings,
      #         allow_dangerous_deserialization=True # Requerido por FAISS por seguridad local
      #     )
      # else:
      #     # Si no existe, creamos una vacía desde cero
      #     dimension = len(self.embeddings.embed_query("hola món"))
      #     self.index = faiss.IndexFlatL2(dimension)
      #     self.vector_store = FAISS(
      #         embedding_function=self.embeddings,
      #         index=self.index,
      #         docstore=InMemoryDocstore(),
      #         index_to_docstore_id={},
      #     )

    def add_docs(self, list_of_docs):
        uuids = [str(uuid4()) for _ in range(len(list_of_docs))]
        self.vector_store.add_documents(documents=list_of_docs, ids=uuids)
        
        
    def search_docs(self, query, k=6):
        # QdrantVectorStore soporta nativamente la Búsqueda de Máxima Relevancia Marginal (MMR).
        results = self.vector_store.max_marginal_relevance_search(query, k=k, fetch_k=20)
        return results