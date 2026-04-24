from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from  langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore


from langgraph.checkpoint.memory import InMemorySaver
from ollama import embeddings

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"

def crear_embeddings():

    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large", # El modelo LLM a usar. Que sea el mismo con el que vectorizamos los documentos!
        base_url="http://localhost:11434",
    )
    return embeddings


def crear_retriever(vectorstore: Chroma):

    padre = RecursiveCharacterTextSplitter(chunk_size= 2000, chunk_overlap= 200) 
    hijo = RecursiveCharacterTextSplitter(chunk_size= 400, chunk_overlap= 50)

    #Almacen padre
    DOCUMENTOS_PADRE = LocalFileStore("Chroma_db/documentos_padre")

    #Almacen hijo
    vectorstore = Chroma(
        embedding_function= crear_embeddings(),
        persist_directory= CHROMA_DIR,
        collection_name= COLLECTION_NAME
    )

    retriever = ParentDocumentRetriever(
        child_splitter= hijo,
        parent_splitter= padre,
        vectorstore= vectorstore,
        docstore= create_kv_docstore(DOCUMENTOS_PADRE)
    )
    
    return retriever

def conectar_crhroma():
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=crear_embeddings(),
    )

    print("..Chromadb listp...")

    retriever = crear_retriever(vectorstore)

    print("...Chromadb integrado...")

    return retriever
