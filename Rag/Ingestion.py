import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"
DATA_PDF = "Data/pdf"
DATA_MD = "Data/md"
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


def crear_embeddings():
    return OllamaEmbeddings(
        model="mxbai-embed-large",
        base_url="http://localhost:11434",
    )


def crear_vectorstore(embeddings, chunks):
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    if vectorstore._collection.count() == 0:
        print("Indexando documentos en Chroma...")
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            vectorstore.add_documents(batch)
    else:
        print(f"Colección ya existe con {vectorstore._collection.count()} documentos.")
    return vectorstore


def main():
    docs_pdf = cargar_pdfs(DATA_PDF)
    chunks_pdf = partir_pdfs(docs_pdf)
    chunks_md = cargar_y_partir_mds(DATA_MD)
    todos = chunks_pdf + chunks_md
    print(f"Total chunks: {len(todos)} (PDF: {len(chunks_pdf)}, MD: {len(chunks_md)})")
    embeddings = crear_embeddings()
    crear_vectorstore(embeddings, todos)


if __name__ == "__main__":
    main()
