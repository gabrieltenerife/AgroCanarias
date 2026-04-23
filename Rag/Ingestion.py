from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"


def cargar_documentos(fichero: str):

    file_path = "EjemplosRAG/ficheros/recetario_canario.pdf"
    loader = PyPDFLoader(file_path)

    documentos = loader.load() # cargamos el documento
    return documentos


"""
Creamos los embeddings
"""
def crear_embeddings():

    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large", # El modelo LLM a usar
        base_url="http://localhost:11434", # Esta es la URL de Ollama (local)
    )
    return embeddings


"""
Añadimos los embeddings a Chroma

"""
def crear_vectorstore(embeddings,documentos):


    padre = RecursiveCharacterTextSplitter(chunk_size= 2000, chunk_overlap= 200) 
    hijo = RecursiveCharacterTextSplitter(chunk_size= 400, chunk_overlap= 50)


    #Almacen padre
    DOCUMENTOS_PADRE = LocalFileStore("./documentos_padre")

    #Almacen hijo

    vectorstore = Chroma(
        embedding_function= embeddings,
        persist_directory= CHROMA_DIR,
        collection_name= COLLECTION_NAME
    )

    rag = ParentDocumentRetriever(
        child_splitter= hijo,
        parent_splitter= padre,
        vectorstore= vectorstore,
        docstore= create_kv_docstore(DOCUMENTOS_PADRE)
    )

    rag.add_documents(documentos)
    
    return rag

def main():

    documentos = cargar_documentos("/home/inta/Documentos/RAG/EjemplosRAG/RAG/xokas.txt")
    emmbedding = crear_embeddings()
    crear_vectorstore(emmbedding, documentos)
    


if __name__ == "__main__":
    main()