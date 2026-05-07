import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage

from .models import ChatRequest, ConversationHistoryResponse
from .dependencies import get_agent_and_conn, close_agent_conn


app = FastAPI(
    title="AgroCanarias IA API",
    description="API para el asistente técnico agrícola de Canarias",
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
    """Envía mensaje al agente y devuelve la respuesta en streaming."""

    async def generate_response():
        conn = None
        try:
            agent, conn = await get_agent_and_conn(request.thread_id)
            config = {"configurable": {"thread_id": request.thread_id}}

            async for event in agent.astream(
                {"messages": [HumanMessage(request.message)]},
                config=config,
                stream_mode="values"
            ):
                message = event["messages"][-1]
                content = message.content if hasattr(message, "content") else ""
                yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        finally:
            await close_agent_conn(conn)

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Obtiene el historial de mensajes de una conversación."""
    
    from Agent.Agent import SQLITE_PATH
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    conn = await aiosqlite.connect(SQLITE_PATH)
    checkpointer = AsyncSqliteSaver(conn)

    config = {"configurable": {"thread_id": thread_id}}
    checkpoint = await checkpointer.aget_tuple(config)

    messages = []
    if checkpoint:
        for msg in checkpoint.messages:
            messages.append({
                "type": type(msg).__name__,
                "content": msg.content if hasattr(msg, "content") else str(msg)
            })

    await conn.close()
    return ConversationHistoryResponse(thread_id=thread_id, messages=messages)


@app.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    """Elimina una conversación y su historial."""
    
    from Agent.Agent import SQLITE_PATH
    import aiosqlite

    conn = await aiosqlite.connect(SQLITE_PATH)
    await conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    await conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    await conn.commit()
    await conn.close()

    return {"status": "deleted", "thread_id": thread_id}