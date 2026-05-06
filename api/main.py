from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.messages import HumanMessage

from api.models import ChatRequest, ChatResponse, ConversationHistoryResponse, HealthResponse
from api.dependencies import get_agent_and_conn, close_agent_conn


app = FastAPI(
    title="AgroCanarias IA API",
    description="API para el asistente técnico agrícola de Canarias",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", model="gemma4:26b")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    conn = None
    try:
        agente, conn = await get_agent_and_conn(request.thread_id)
        
        config = {"configurable": {"thread_id": request.thread_id}}
        response_text = ""
        
        async for paso in agente.astream(
            {"messages": [HumanMessage(request.message)]},
            config=config,
            stream_mode="values"
        ):
            ultimo = paso["messages"][-1]
            response_text = ultimo.content
        
        return ChatResponse(message=response_text, thread_id=request.thread_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        await close_agent_conn(conn)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        conn = None
        try:
            agente, conn = await get_agent_and_conn(request.thread_id)
            config = {"configurable": {"thread_id": request.thread_id}}
            
            async for paso in agente.astream(
                {"messages": [HumanMessage(request.message)]},
                config=config,
                stream_mode="values"
            ):
                ultimo = paso["messages"][-1]
                content = ultimo.content if hasattr(ultimo, "content") else ""
                reasoning = ultimo.additional_kwargs.get("reasoning_content", "") if hasattr(ultimo, "additional_kwargs") else ""
                
                if reasoning:
                    f"data: {json.dumps({'type': 'reasoning', 'content': reasoning})}\n\n"
                
                yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        finally:
            await close_agent_conn(conn)
    
    import json
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/conversations/{thread_id}", response_model=ConversationHistoryResponse)
async def get_conversation(thread_id: str):
    from Agent.Agent import SQLITE_PATH
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    
    try:
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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    from Agent.Agent import SQLITE_PATH
    import aiosqlite
    
    conn = await aiosqlite.connect(SQLITE_PATH)
    await conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    await conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    await conn.commit()
    await conn.close()
    
    return {"status": "deleted", "thread_id": thread_id}