from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    sender_ids: list[str] = []
    model_id: str = "gemini-2.0-flash"
    message_limit: int = 100


class ChatResponse(BaseModel):
    response: str
    context_message_count: int


class SenderInfo(BaseModel):
    sender_id: str
    message_count: int


class ModelInfo(BaseModel):
    id: str
    name: str


class SelectedIdsRequest(BaseModel):
    sender_ids: list[str] = []
