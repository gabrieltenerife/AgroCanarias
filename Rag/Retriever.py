import os
import logging

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore

logger = logging.getLogger(__name__)

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"
EMBEDDING_MODEL = "mxbai-embed-large"
OLLAMA_BASE_URL = "http://localhost:11434"

_vectorstore = None
_docstore = None


def crear_embeddings():
    return OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=crear_embeddings(),
        )
    return _vectorstore


def get_docstore():
    global _docstore
    if _docstore is None:
        store = LocalFileStore(os.path.join(CHROMA_DIR, "documentos_padre"))
        _docstore = create_kv_docstore(store)
    return _docstore


def _construir_filtros(filtros_dict: dict | None) -> dict | None:
    if not filtros_dict:
        return None
    filtros_limpios = {k: v for k, v in filtros_dict.items() if v is not None}
    if not filtros_limpios:
        return None
    if len(filtros_limpios) == 1:
        return filtros_limpios
    return {"$and": [{k: v} for k, v in filtros_limpios.items()]}


def buscar_documentos(query: str, filtros: dict = None, k: int = 10) -> list:
    vectorstore = get_vectorstore()
    docstore = get_docstore()

    search_kwargs = {"k": k}
    filter_dict = _construir_filtros(filtros)
    if filter_dict:
        search_kwargs["filter"] = filter_dict

    try:
        child_docs = vectorstore.similarity_search(query, **search_kwargs)
    except Exception as e:
        logger.error("Error en similarity_search query=%r filtros=%r: %s", query, filtros, e)
        return []

    if not child_docs:
        logger.warning("similarity_search devolvio 0 resultados para query=%r filtros=%r", query, filtros)
        return []

    parent_ids = set()
    for doc in child_docs:
        doc_id = doc.metadata.get("doc_id")
        if doc_id:
            parent_ids.add(doc_id)

    if parent_ids:
        try:
            parent_docs = docstore.mget(list(parent_ids))
            parent_docs = [d for d in parent_docs if d is not None]
            if parent_docs:
                return parent_docs
        except Exception as e:
            logger.error("Error obteniendo parent docs de docstore: %s", e)

    logger.warning("No se encontraron parent docs, devolviendo child docs. parent_ids=%s", parent_ids)
    return child_docs


def format_resultados(documentos: list) -> str:
    if not documentos:
        return "No se encontro informacion para la consulta."
    resultados = [
        f"--- Doc {i+1} ---\nCat: {doc.metadata.get('categoria', 'N/A')} | Cultivo: {doc.metadata.get('cultivo', 'N/A')}\n{doc.page_content}"
        for i, doc in enumerate(documentos)
    ]
    return "\n\n".join(resultados)