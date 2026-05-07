from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    stream: bool = False

class MessageInput(BaseModel):
    role: str
    content: str


class ConversationHistoryResponse(BaseModel):
    thread_id: str
    messages: list[dict]


class ConversationMeta(BaseModel):
    thread_id: str
    title: str
    preview: str
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationMeta]


class CreateConversationResponse(BaseModel):
    thread_id: str

