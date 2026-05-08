import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore
from pydantic import BaseModel, Field
from typing import Literal, Optional

CHROMA_DIR = "Chroma_db"
COLLECTION_NAME = "Documents"


class Metadata(BaseModel):
    categoria: Literal[
        "fitosanitario",
        "ayuda",
        "dop",
        "cuaderno",
        "exportacion",
        "otros"
    ] = Field(description="Tipo de documento según su contenido principal")

    cultivo: Literal[
        "platano",
        "tomate",
        "papa",
        "pimiento",
        "otros"
    ] = Field(description="Cultivo principal al que hace referencia el documento")

    isla: Optional[Literal[
        "tenerife",
        "gran_canaria",
        "la_palma",
        "lanzarote",
        "fuerteventura",
        "la_gomera",
        "el_hierro",
        "todas"
    ]] = Field(default=None, description="Isla a la que aplica la normativa o convocatoria, si procede")

    tipo_produccion: Optional[Literal[
        "convencional",
        "integrada",
        "ecologica"
    ]] = Field(default=None, description="Modalidad de producción a la que aplica el documento")

    tipo_certificacion: Optional[Literal[
        "convencional",
        "integrada",
        "ecologica",
        "globalGAP"
    ]] = Field(default=None, description="Certificación a la que aplica el documento, relevante para cuaderno de campo y auditorías")

    dop: Optional[Literal[
        "platano_canarias",
        "papas_antiguas",
        "miel_tenerife",
        "vino_denominacion",
        "otras"
    ]] = Field(default=None, description="Denominación de Origen o IGP a la que hace referencia el documento")

    mercado_destino: Optional[Literal[
        "union_europea",
        "reino_unido",
        "eeuu",
        "otros"
    ]] = Field(default=None, description="Mercado de destino, relevante para documentos de exportación")

    organismo: Optional[Literal[
        "mapa",
        "gobierno_canarias",
        "fega",
        "consejo_regulador",
        "icex",
        "eur_lex",
        "cabildo",
        "otros"
    ]] = Field(default=None, description="Organismo emisor o fuente oficial del documento")

    anio_publicacion: Optional[int] = Field(
        default=None,
        description="Año de publicación del documento. Crítico para ayudas y convocatorias que cambian anualmente"
    )    


llm = ChatOllama(
    model="gemma4:26b",
    temperature=0
)
llm_structured = llm.with_structured_output(Metadata)


def extraer_metadata_llm(texto: str) -> Metadata:
    prompt = f"""
    Analiza este documento agrícola y extrae:

    - categoria: fitosanitario, ayuda, dop, cuaderno, exportacion u otros
    - cultivo: platano, tomate, papa, pimiento u otros

    IMPORTANTE:
    - Responde solo con los valores correctos
    - Si no estás seguro, usa "otros"

    Texto:
    {texto}
    """

    try:
        metadata = llm_structured.invoke(prompt)
        return metadata
    except Exception as e:
        print(f"Error extrayendo metadata: {e}")
        return Metadata(categoria="otros", cultivo="otros")


def cargar_documentos(carpeta: str):
    documentos = []
    archivos_procesados = 0
    
    # Verificamos si la carpeta existe
    if not os.path.exists(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return []

    for archivo in os.listdir(carpeta):
        
        if archivo.lower().endswith(".pdf"):
            ruta_completa = os.path.join(carpeta, archivo)
            
            try:
                loader = PyPDFLoader(ruta_completa)
                docs = loader.load()

                # 🔥 EXTRAER METADATA CON LLM (solo primer chunk)
                texto_base = docs[0].page_content[:1500]
                metadata_llm = extraer_metadata_llm(texto_base)

                print(f"Metadata detectada para {archivo}: {metadata_llm}")

                # 🔥 AÑADIR METADATA A TODOS LOS DOCS
                for doc in docs:
                    doc.metadata["categoria"] = metadata_llm.categoria
                    doc.metadata["cultivo"] = metadata_llm.cultivo

                documentos.extend(docs) 
                archivos_procesados += 1
                print(f"Cargado: {archivo} ({len(docs)} páginas)")

            except Exception as e:
                print(f"Error al cargar {archivo}: {e}")
        

    print(f"Total de archivos PDF procesados: {archivos_procesados}")
    
    return documentos


def crear_embeddings():

    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large", # El modelo LLM a usar
        base_url="http://localhost:11434", # Esta es la URL de Ollama (local)
    )
    return embeddings


def crear_vectorstore(embeddings,documentos):


    padre = RecursiveCharacterTextSplitter(chunk_size= 2000, chunk_overlap= 200) 
    hijo = RecursiveCharacterTextSplitter(chunk_size= 400, chunk_overlap= 50)


    #Almacen padre
    DOCUMENTOS_PADRE = LocalFileStore("Chroma_db/documentos_padre")

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
    
    return rag, vectorstore

def main():

    documentos = cargar_documentos("Data")
    emmbedding = crear_embeddings()
    crear_vectorstore(emmbedding, documentos)
    


if __name__ == "__main__":
    main()