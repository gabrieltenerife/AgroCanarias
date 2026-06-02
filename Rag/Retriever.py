from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"
COLLECTION_FULLPDF = "FullPDFs"

_vectorstores = {}


def crear_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
    )


def _get_vectorstore(collection_name: str):
    if collection_name not in _vectorstores:
        _vectorstores[collection_name] = Chroma(
            embedding_function=crear_embeddings(),
            persist_directory=CHROMA_DIR,
            collection_name=collection_name,
        )
    return _vectorstores[collection_name]


def conectar_chroma():
    return _get_vectorstore(COLLECTION_NAME).as_retriever()


def conectar_chroma_fullpdfs():
    return _get_vectorstore(COLLECTION_FULLPDF).as_retriever()


def get_fullpdf(filename: str) -> str:
    vectorstore = _get_vectorstore(COLLECTION_FULLPDF)
    result = vectorstore.get(where={"source": filename})
    documents = result.get("documents", []) if isinstance(result, dict) else []
    return "\n\n".join(documents)
