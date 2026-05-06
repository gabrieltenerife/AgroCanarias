from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    thread_id: str


class MessageInput(BaseModel):
    role: str
    content: str


class ConversationHistoryResponse(BaseModel):
    thread_id: str
    messages: list[dict]


class HealthResponse(BaseModel):
    status: str
    model: str = "gemma4:26b"