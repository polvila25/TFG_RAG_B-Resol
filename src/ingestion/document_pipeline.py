from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


'''
Módulo de carga y troceado de documentos PDF.
Contiene las clases PdfLoader (lectura de PDF) y Chunker (división en fragmentos).
Se utiliza en la fase de preprocesamiento antes de la indexación semántica.
'''

#clase para cargar el pdf 
class PdfLoader:
    def read_file(self, file_path):
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        return docs

#Troceado de documetnos 
class Chunker:
    def __init__(self, chunk_size=1000, chunk_overlap=150):
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\n", "\n", " ", ".", ",",
                "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""
            ],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_docs(self, docs):
        list_of_docs = []
        for doc in docs:
            tmp = self.text_splitter.split_text(doc.page_content)
            for chunk in tmp:
                list_of_docs.append(
                    Document(
                        page_content=chunk,
                        # Conservamos todos los metadatos (especialmente la página)
                        metadata=doc.metadata,
                    )
                )
        return list_of_docs