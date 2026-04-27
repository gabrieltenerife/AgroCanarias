from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, Literal
from Rag.Retriever import conectar_crhroma

retriever_base = conectar_crhroma()


# 0. BUSQUEDA RAG GENERAL (sin filtros)
# =========================================
@tool()
def obtener_info_rag(pregunta: str):

    """ Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante. """

    retriever = conectar_crhroma()
    return retriever.invoke(pregunta)


# 1. MOTOR BASE DE BÚSQUEDA CON FILTROS DINÁMICOS
# =========================================
def motor_busqueda_chroma(query: str, filtros_dict: dict = None) -> str:
    """
    Función genérica que maneja la comunicación con ChromaDB, 
    aplica cualquier filtro dinámico y formatea la salida.
    """
    # Aplicar filtros si existen
    if filtros_dict:
        # Limpiamos los filtros que sean None
        filtros_limpios = {k: v for k, v in filtros_dict.items() if v is not None}
        
        if len(filtros_limpios) == 1:
            retriever_base.search_kwargs = {"filter": filtros_limpios}
        elif len(filtros_limpios) > 1:
            condiciones = [{k: v} for k, v in filtros_limpios.items()]
            retriever_base.search_kwargs = {"filter": {"$and": condiciones}}
    else:
        retriever_base.search_kwargs = {}

    # Ejecutar búsqueda
    try:
        documentos = retriever_base.invoke(query)
    except Exception as e:
        return f"Error en la base de datos: {e}"
    
    # Formatear salida
    if not documentos:
        return f"No se encontró información para la consulta: '{query}'."
        
    resultados = [
        f"--- Doc {i+1} ---\nCat: {doc.metadata.get('categoria', 'N/A')} | Cultivo: {doc.metadata.get('cultivo', 'N/A')}\n{doc.page_content}"
        for i, doc in enumerate(documentos)
    ]
    return "\n\n".join(resultados)


# 2. ESQUEMAS PYDANTIC (Uno por tool)
# ==========================================
class BusquedaFitosanitarioInput(BaseModel):
    query: str = Field(description="Plaga, enfermedad o producto a buscar.")
    cultivo: Optional[Literal["platano", "tomate", "papa", "pimiento", "otros"]] = Field(default=None)


# 3. DEFINICIÓN DE TOOLS CON FILTRO Y ESQUEMA PYDANTIC
# ==========================================
@tool("buscar_fitosanitarios", args_schema=BusquedaFitosanitarioInput)
def tool_buscar_fitosanitarios(query: str, cultivo: Optional[str] = None) -> str:
    """Busca exclusivamente información sobre productos fitosanitarios y plagas."""
    
    
    #Para elegir los filtros consultar la class Metadata en Ingestion
    filtros = {"categoria": "fitosanitario", "cultivo": cultivo}
    return motor_busqueda_chroma(query, filtros)


