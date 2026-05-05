from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from dotenv import load_dotenv

import sys
NPX = "npx.cmd" if sys.platform == "win32" else "npx"
DOCUMENTS_PATH = "C:\\Users\\gamba\\Documents" if sys.platform == "win32" else "/home/inta/Documentos"

load_dotenv()
api = os.getenv('Aemet_apiKey')
api_tavily = os.getenv('Tavily_apiKey')


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
            },

            "tavily-mcp": {
                "transport": "stdio",
                "command": NPX,
                "args": ["-y", "tavily-mcp@latest"],
                "env": {
                    "TAVILY_API_KEY": api_tavily,
                    "DEFAULT_PARAMETERS": "{\"include_images\": true, \"max_results\": 15, \"search_depth\": \"advanced\"}"
                }
            },

            "filesystem": {
                "transport": "stdio",
                "command": NPX,
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    DOCUMENTS_PATH 
                ]
            }
        }
    )

    tools = await client.get_tools()

    prompts = []
    resources = []
    try:
        prompts = await client.get_prompt("weather", "nombrePrompt1")
    except Exception as e:
        print("No existe el prompt con el nombre asociado")

    try:
        resources = await client.get_resources()
    except Exception as e:
        print("No existen recursos en este MCP")

    return tools, prompts, resources