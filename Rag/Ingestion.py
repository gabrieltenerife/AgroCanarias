import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"
BATCH_SIZE = 40


def cargar_documentos(carpeta: str):
    documentos = []
    archivos_procesados = 0

    if not os.path.exists(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return []

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            ruta_completa = os.path.join(carpeta, archivo)
            try:
                loader = PyPDFLoader(ruta_completa)
                docs = loader.load()
                documentos.extend(docs)
                archivos_procesados += 1
                print(f"Cargado: {archivo} ({len(docs)} páginas)")
            except Exception as e:
                print(f"Error al cargar {archivo}: {e}")

    print(f"Total de archivos PDF procesados: {archivos_procesados}")
    return documentos


def crear_embeddings():
    return OllamaEmbeddings(
        model="mxbai-embed-large",
        base_url="http://localhost:11434",
    )


def crear_vectorstore(embeddings, documentos):
    padre = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    hijo = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=65)

    DOCUMENTOS_PADRE = LocalFileStore(os.path.join(CHROMA_DIR, "documentos_padre"))

    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )

    rag = ParentDocumentRetriever(
        child_splitter=hijo,
        parent_splitter=padre,
        vectorstore=vectorstore,
        docstore=create_kv_docstore(DOCUMENTOS_PADRE),
    )

    for i in range(0, len(documentos), BATCH_SIZE):
        batch = documentos[i:i+BATCH_SIZE]
        rag.add_documents(batch)

    return rag, vectorstore


def main():
    documentos = cargar_documentos("Data")
    embeddings = crear_embeddings()
    crear_vectorstore(embeddings, documentos)


if __name__ == "__main__":
    main()
