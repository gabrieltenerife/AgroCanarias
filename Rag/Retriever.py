from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"

_retriever = None


def crear_embeddings():
    return OllamaEmbeddings(
        model="mxbai-embed-large",
        base_url="http://localhost:11434",
    )


def conectar_chroma():
    global _retriever
    if _retriever is not None:
        return _retriever
    vectorstore = Chroma(
        embedding_function=crear_embeddings(),
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    _retriever = vectorstore.as_retriever()
    return _retriever
