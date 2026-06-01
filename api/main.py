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

            tool_call_seen = False
            final_response_sent = False

            async for event in agent.astream(
                {"messages": [HumanMessage(request.message)]},
                config=config,
                stream_mode="messages"
            ):
                message = event[0]

                if hasattr(message, "type"):
                    msg_type = message.type

                    if msg_type == "human":
                        continue

                    if msg_type == "ai":
                        if tool_call_seen and not final_response_sent:
                            yield f"data: {json.dumps({'type': 'message', 'content': message.content})}\n\n"
                            final_response_sent = True
                            break
                        elif not tool_call_seen and hasattr(message, "tool_calls") and message.tool_calls:
                            tool_call_seen = True

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        finally:
            await close_agent_conn(conn)

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Obtiene el historial de mensajes de una conversacion."""
    from api.database import get_db

    conn, checkpointer = await get_db()
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
    from api.database import get_db

    conn, checkpointer = await get_db()
    await checkpointer.adelete_thread(thread_id)
    await conn.close()

    return {"status": "deleted", "thread_id": thread_id}


@app.get("/conversations", response_model=ConversationListResponse)
async def list_conversations():
    """Lista todas las conversaciones con su metadata."""
    from api.database import get_db

    conn, checkpointer = await get_db()

    thread_ids = set()
    async for checkpoint_tuple in checkpointer.alist(config=None):
        thread_ids.add(checkpoint_tuple.config["configurable"]["thread_id"])

    conversations = []
    for thread_id in thread_ids:
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
            message_count=1
        ))

    await conn.close()
    return ConversationListResponse(conversations=conversations)


@app.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation():
    """Crea una nueva conversacion y devuelve el thread_id."""
    import uuid
    thread_id = f"thread-{uuid.uuid4().hex[:12]}"
    return CreateConversationResponse(thread_id=thread_id)