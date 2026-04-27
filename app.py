from langchain.messages import HumanMessage
import asyncio

from Agent.Agent import Agente
from Integrations.Mpcs import obtener_herramientas

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



tools, _, resources = asyncio.run(obtener_herramientas())
agente = Agente(tools=tools)

asyncio.run(hablarConChat(agente))