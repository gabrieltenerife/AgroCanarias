import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"
COLLECTION_FULLPDF = "FullPDFs"
DATA_PDF = "Data/pdf"
DATA_MD = "Data/md"
DATA_FULLPDF = "Data/fullpdf"
BATCH_SIZE = 40


def cargar_pdfs(carpeta: str):
    documentos = []
    if not os.path.exists(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return []

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            ruta = os.path.join(carpeta, archivo)
            try:
                loader = PyPDFLoader(ruta)
                docs = loader.load()
                documentos.extend(docs)
                print(f"Cargado PDF: {archivo} ({len(docs)} páginas)")
            except Exception as e:
                print(f"Error al cargar {archivo}: {e}")

    return documentos


def partir_pdfs(documentos):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
    return splitter.split_documents(documentos)


def cargar_y_partir_mds(carpeta: str):
    chunks = []
    if not os.path.exists(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return []

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "section")])
    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".md"):
            ruta = os.path.join(carpeta, archivo)
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    texto = f.read()
                docs = splitter.split_text(texto)
                for d in docs:
                    d.metadata["source"] = archivo
                chunks.extend(docs)
                print(f"Cargado MD: {archivo} ({len(docs)} secciones)")
            except Exception as e:
                print(f"Error al cargar {archivo}: {e}")

    return chunks


def cargar_fullpdfs(carpeta: str):
    documentos = []
    if not os.path.exists(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return []

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            ruta = os.path.join(carpeta, archivo)
            try:
                loader = PyPDFLoader(ruta)
                pages = loader.load()
                texto = "\n\n".join(p.page_content for p in pages)
                doc = Document(
                    page_content=texto,
                    metadata={"source": archivo, "type": "fullpdf"},
                )
                documentos.append(doc)
                print(f"Cargado full PDF: {archivo} ({len(pages)} páginas, 1 doc)")
            except Exception as e:
                print(f"Error al cargar {archivo}: {e}")

    return documentos


def crear_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
    )


def crear_vectorstore(embeddings, chunks, collection_name: str = COLLECTION_NAME):
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=collection_name,
    )
    if vectorstore._collection.count() == 0:
        print(f"Indexando {len(chunks)} documentos en colección '{collection_name}'...")
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            vectorstore.add_documents(batch)
    else:
        print(f"Colección '{collection_name}' ya existe con {vectorstore._collection.count()} documentos.")
    return vectorstore


def main():
    embeddings = crear_embeddings()

    docs_pdf = cargar_pdfs(DATA_PDF)
    chunks_pdf = partir_pdfs(docs_pdf)
    chunks_md = cargar_y_partir_mds(DATA_MD)
    todos = chunks_pdf + chunks_md
    print(f"Total chunks: {len(todos)} (PDF: {len(chunks_pdf)}, MD: {len(chunks_md)})")
    crear_vectorstore(embeddings, todos, COLLECTION_NAME)

    fullpdfs = cargar_fullpdfs(DATA_FULLPDF)
    print(f"Total fullpdfs: {len(fullpdfs)}")
    crear_vectorstore(embeddings, fullpdfs, COLLECTION_FULLPDF)


if __name__ == "__main__":
    main()
