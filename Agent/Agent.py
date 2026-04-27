from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

from Agent.Tools import obtener_info_rag

system_prompt = """ Eres un agente que responde preguntas utilizando tools y respondiendo del rag exclusivamente.
Si no sabes la respuesta, responde que no tienes la información en lugar de inventar una respuesta"""

def Agente(tools: list = []):
    modelo = ChatOllama(model="gemma4:26b", num_ctx=100000)
    agente = create_agent(
    
    model=modelo,
    tools=tools + [obtener_info_rag],
    checkpointer=InMemorySaver(),

    system_prompt = system_prompt
    )
    return agente
