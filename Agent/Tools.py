from Rag.Retriever import conectar_crhroma
from langchain.tools import tool


@tool()
def obtener_info_rag(pregunta: str):

    """ Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante. """

    retriever = conectar_crhroma()
    return retriever.invoke(pregunta)

