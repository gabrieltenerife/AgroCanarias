from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import sys
from dotenv import load_dotenv

NPX = "npx.cmd" if sys.platform == "win32" else "npx"
DOCUMENTS_PATH = "C:\\Users\\gamba\\Documents" if sys.platform == "win32" else "/home/inta/Documentos"

load_dotenv()
_api = os.getenv('Aemet_apiKey')
_api_tavily = os.getenv('Tavily_apiKey')

_mcp_client = None
_mcp_tools = None


def _build_mcp_config():
    return {
        "aemet-mcp": {
            "transport": "stdio",
            "command": "docker",
            "args": [
                "run", "--rm", "-i",
                "-e", f"AEMET_API_KEY={_api}",
                "aemet-mcp"
            ]
        },
        "tavily-mcp": {
            "transport": "stdio",
            "command": NPX,
            "args": ["-y", "tavily-mcp@latest"],
            "env": {
                "TAVILY_API_KEY": _api_tavily,
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


async def obtener_herramientas():
    global _mcp_client, _mcp_tools

    if _mcp_tools is not None:
        return _mcp_tools, [], []

    _mcp_client = MultiServerMCPClient(_build_mcp_config())
    _mcp_tools = await _mcp_client.get_tools()

    prompts = []
    resources = []
    try:
        prompts = await _mcp_client.get_prompt("weather", "nombrePrompt1")
    except Exception:
        pass
    try:
        resources = await _mcp_client.get_resources()
    except Exception:
        pass

    return _mcp_tools, prompts, resources


async def cerrar_mcp():
    global _mcp_client, _mcp_tools
    _mcp_client = None
    _mcp_tools = None