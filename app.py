from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from langchain.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
import asyncio

from Rag.Retriever import conectar_crhroma
from Integrations.aemet import obtener_herramientas

@tool()
def obtener_info_rag(pregunta: str):

    """ Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante. """

    retriever = conectar_crhroma()
    return retriever.invoke(pregunta)

async def hablarConChat(agente):
    while (prompt := input("> ")) != "end":
        async for paso in agente.astream(
            {
                "messages": [HumanMessage(prompt)]
            },
            stream_mode="values",
            config={"configurable": {"thread_id": "Gabrielito"}}
        ):
            ultimo_mensaje = paso["messages"][-1]

            hayRazonamiento = ""
            if hasattr(ultimo_mensaje, "additional_kwargs"):
                hayRazonamiento = ultimo_mensaje.additional_kwargs.get("reasoning_content", "")

            if hayRazonamiento:
                print("\n=== PENSANDO ===")
                print(hayRazonamiento)

            print("\n=== MENSAJE ===")
            ultimo_mensaje.pretty_print()


def Agente(tools: list = []):
    modelo = ChatOllama(model="gemma4:26b", num_ctx=16000)
    agente = create_agent(
    
    model=modelo,
    tools=tools + [obtener_info_rag],
    checkpointer=InMemorySaver(),

    system_prompt = """
    Eres un agente basado en RAG (Retrieval Augmented Generation) diseñado para responder preguntas utilizando información
    relevante obtenida de una base de datos.
    Eres un cocinero experto en recetas canarias, y deves de responder de manera cercana y amigable, como si fueras un amigo que comparte sus conocimientos culinarios.
    Debes de responder a las preguntas de manera clara y sencilla, utilizando la información relevante que obtienes de la base de datos. Si no encuentras información relevante, debes responder con un mensaje claro indicando que no se encontró información relevante.""")

    return agente



tools, _, resources = asyncio.run(obtener_herramientas())

agente = Agente(tools=tools)
asyncio.run(hablarConChat(agente))