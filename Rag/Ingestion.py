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
BATCH_SIZE = 40


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
    model="gemma4:e4b",
    temperature=0
)
llm_structured = llm.with_structured_output(Metadata)


def extraer_metadata_llm(texto: str) -> Metadata:
    prompt = f"""
    Analiza este documento agrícola canario y extrae TODOS los campos de metadata:

    - categoria: fitosanitario, ayuda, dop, cuaderno, exportacion u otros
    - cultivo: platano, tomate, papa, pimiento u otros
    - isla: tenerife, gran_canaria, la_palma, lanzarote, fuerteventura, la_gomera, el_hierro, todas, o null si no aplica
    - tipo_produccion: convencional, integrada, ecologica, o null si no aplica
    - tipo_certificacion: convencional, integrada, ecologica, globalGAP, o null si no aplica
    - dop: platano_canarias, papas_antiguas, miel_tenerife, vino_denominacion, otras, o null si no aplica
    - mercado_destino: union_europea, reino_unido, eeuu, otros, o null si no aplica
    - organismo: mapa, gobierno_canarias, fega, consejo_regulador, icex, eur_lex, cabildo, otros, o null si no aplica
    - anio_publicacion: año de publicación del documento, o null si no se puede determinar

    IMPORTANTE:
    - Responde SOLO con los valores correctos según el contenido del documento
    - Si un campo no aplica o no se puede determinar, usa null (no "otros")
    - Si no estás seguro del cultivo o categoria, usa "otros"

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
                texto_base = docs[0].page_content[:2000]
                metadata_llm = extraer_metadata_llm(texto_base)

                print(f"Metadata detectada para {archivo}: {metadata_llm}")

                metadata_dict = {
                    "categoria": metadata_llm.categoria,
                    "cultivo": metadata_llm.cultivo,
                    "isla": metadata_llm.isla,
                    "tipo_produccion": metadata_llm.tipo_produccion,
                    "tipo_certificacion": metadata_llm.tipo_certificacion,
                    "dop": metadata_llm.dop,
                    "mercado_destino": metadata_llm.mercado_destino,
                    "organismo": metadata_llm.organismo,
                    "anio_publicacion": metadata_llm.anio_publicacion,
                }
                metadata_limpia = {k: v for k, v in metadata_dict.items() if v is not None}

                for doc in docs:
                    doc.metadata.update(metadata_limpia)

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


    padre = RecursiveCharacterTextSplitter(chunk_size= 1700, chunk_overlap= 240) 
    hijo = RecursiveCharacterTextSplitter(chunk_size= 350, chunk_overlap= 80)


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

    
    for i in range(0, len(documentos), BATCH_SIZE):
        batch = documentos[i:i+BATCH_SIZE]
        rag.add_documents(batch)
    
    
    return rag, vectorstore

def main():

    documentos = cargar_documentos("Data")
    emmbedding = crear_embeddings()
    crear_vectorstore(emmbedding, documentos)
    


if __name__ == "__main__":
    main()