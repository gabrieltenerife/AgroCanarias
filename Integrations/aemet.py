import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.tools import tool
import json
import os
from dotenv import load_dotenv

load_dotenv()

api = os.getenv('Aemet_apiKey')

print(api)
from textwrap import indent




async def obtener_herramientas():

    client = MultiServerMCPClient(
    {
        "aemet-mcp": {
            "transport": "stdio",
           "command": "docker",
            "args": [
                "run",
                "--rm",
                "-i",
                "-e", f"AEMET_API_KEY={api}",
                "aemet-mcp"
            ]
        }
    }
    )

    # Nos descargamos las herramientas
    tools = await client.get_tools()

    prompts = []
    resources = []
    try:
        prompts = await client.get_prompt("weather", "nombrePrompt1") # Ejemplo
    except Exception as e:
        print("No existe el prompt con el nombre asociado")
    
    try:
        resources = await client.get_resources()
    except Exception as e:
        print("No existen recursos en este MCP")

    return tools, prompts, resources