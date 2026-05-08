import os
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

SQLITE_PATH = os.path.join("Memory", "memoria_agente.sqlite")


async def get_db():
    """Create and return a database connection with checkpointer setup."""
    os.makedirs("Memory", exist_ok=True)
    conn = await aiosqlite.connect(SQLITE_PATH)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    return conn, checkpointer