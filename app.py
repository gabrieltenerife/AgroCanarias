from langchain.tools import tool, ToolRuntime
from langchain.messages import HumanMessage, SystemMessage
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from Rag.Retriever import conectar_crhroma



@tool()
def obtener_info_rag(pregunta: str):

    """ Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante. """

    retriever = conectar_crhroma()
    return retriever.invoke(pregunta)




def hablarConChat(agente):
    while (prompt := input("> ")) != "end":
        for paso in agente.stream(
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



def crearAgente():
    modelo = ChatOllama(model="gemma4:26b")
    agente = create_agent(
    
    model=modelo,
    tools=[obtener_info_rag],
    checkpointer=InMemorySaver(),

    system_prompt = """
    Eres un agente basado en RAG (Retrieval Augmented Generation) diseñado para responder preguntas utilizando información
    relevante obtenida de una base de datos.
    Eres un cocinero experto en recetas canarias, y deves de responder de manera cercana y amigable, como si fueras un amigo que comparte sus conocimientos culinarios.
    Debes de responder a las preguntas de manera clara y sencilla, utilizando la información relevante que obtienes de la base de datos. Si no encuentras información relevante, debes responder con un mensaje claro indicando que no se encontró información relevante.""")

    return agente

agente = crearAgente()
hablarConChat(agente)