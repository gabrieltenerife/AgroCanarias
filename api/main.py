import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage

from .models import ChatRequest, ConversationHistoryResponse, ConversationMeta, ConversationListResponse, CreateConversationResponse
from .dependencies import get_agent_and_conn, close_agent_conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    from Integrations.Mpcs import obtener_herramientas
    await obtener_herramientas()
    print("MCP tools inicializadas")
    yield
    from Integrations.Mpcs import cerrar_mcp
    await cerrar_mcp()
    print("MCP tools cerradas")


app = FastAPI(
    title="AgroCanarias IA API",
    description="API para el asistente tecnico agricola de Canarias",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Envia mensaje al agente y devuelve la respuesta en streaming."""

    async def generate_response():
        conn = None
        try:
            agent, conn = await get_agent_and_conn(request.thread_id)
            config = {"configurable": {"thread_id": request.thread_id}}

            async for event in agent.astream(
                {"messages": [HumanMessage(request.message)]},
                config=config,
                stream_mode="messages"
            ):
                message = event[0]
                if hasattr(message, "content") and message.content:
                    content = message.content
                    yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        finally:
            await close_agent_conn(conn)

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Obtiene el historial de mensajes de una conversacion."""
    from Agent.Agent import SQLITE_PATH
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    conn = await aiosqlite.connect(SQLITE_PATH)
    checkpointer = AsyncSqliteSaver(conn)
    config = {"configurable": {"thread_id": thread_id}}
    checkpoint = await checkpointer.aget(config)

    messages = []
    if checkpoint and 'channel_values' in checkpoint:
        cv = checkpoint.get('channel_values', {})
        if 'messages' in cv:
            for msg in cv['messages']:
                messages.append({
                    "type": type(msg).__name__,
                    "content": msg.content if hasattr(msg, "content") else str(msg)
                })

    await conn.close()
    return ConversationHistoryResponse(thread_id=thread_id, messages=messages)


@app.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    """Elimina una conversacion y su historial."""
    from Agent.Agent import SQLITE_PATH
    import aiosqlite

    conn = await aiosqlite.connect(SQLITE_PATH)
    await conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    await conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    await conn.commit()
    await conn.close()

    return {"status": "deleted", "thread_id": thread_id}


@app.get("/conversations", response_model=ConversationListResponse)
async def list_conversations():
    """Lista todas las conversaciones con su metadata."""
    from Agent.Agent import SQLITE_PATH
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    conn = await aiosqlite.connect(SQLITE_PATH)
    checkpointer = AsyncSqliteSaver(conn)

    cursor = await conn.execute("""
        SELECT thread_id, COUNT(*) as total
        FROM checkpoints
        GROUP BY thread_id
        ORDER BY MAX(checkpoint_id) DESC
    """)
    rows = await cursor.fetchall()

    conversations = []
    for row in rows:
        thread_id = row[0]
        total = row[1]
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint = await checkpointer.aget(config)

        preview = ""
        title = ""
        if checkpoint and 'channel_values' in checkpoint:
            cv = checkpoint.get('channel_values', {})
            if 'messages' in cv:
                msgs = cv['messages']
                if msgs and len(msgs) > 0:
                    first_msg = msgs[0]
                    content = first_msg.content if hasattr(first_msg, "content") else str(first_msg)
                    if content:
                        preview = content[:60] + ("..." if len(content) > 60 else "")
                        title = content[:40] + ("..." if len(content) > 40 else "")

        conversations.append(ConversationMeta(
            thread_id=thread_id,
            title=title or f"Conversacion {thread_id[:8]}",
            preview=preview or "Sin mensajes",
            message_count=total
        ))

    await conn.close()
    return ConversationListResponse(conversations=conversations)


@app.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation():
    """Crea una nueva conversacion y devuelve el thread_id."""
    import uuid
    thread_id = f"thread-{uuid.uuid4().hex[:12]}"
    return CreateConversationResponse(thread_id=thread_id)