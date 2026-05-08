from Agent.Agent import Agente


async def get_agent_and_conn(thread_id: str = "default", tools: list = None):
    if tools is None:
        tools = []
    from Integrations.Mpcs import obtener_herramientas
    mcp_tools, _, _ = await obtener_herramientas()
    all_tools = tools + mcp_tools

    agente, conn = await Agente(tools=all_tools)
    return agente, conn


async def close_agent_conn(conn):
    if conn:
        await conn.close()