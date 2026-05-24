import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore

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

    padre = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    hijo = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=65)

    DOCUMENTOS_PADRE = LocalFileStore(os.path.join(CHROMA_DIR, "documentos_padre"))

    vectorstore = Chroma(
        embedding_function=crear_embeddings(),
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )

    _retriever = ParentDocumentRetriever(
        child_splitter=hijo,
        parent_splitter=padre,
        vectorstore=vectorstore,
        docstore=create_kv_docstore(DOCUMENTOS_PADRE),
    )

    return _retriever
