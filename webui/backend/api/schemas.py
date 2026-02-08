from __future__ import annotations

from typing import Literal, Optional

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


class DBStatusResponse(BaseModel):
    message_count: int
    sender_count: int
    latest_message_at: Optional[str] = None


class DBClearResponse(BaseModel):
    ok: bool
    message: str


class CollectorFetchRequest(BaseModel):
    targets: list[str] = []
    limit: int = 100


class CollectorFetchDetail(BaseModel):
    target: str
    processed: int
    error: Optional[str] = None


class CollectorFetchResponse(BaseModel):
    ok: bool
    processed: int
    details: list[CollectorFetchDetail] = []


class AnalyzerRunRequest(BaseModel):
    job: Literal["topics", "sentiment", "style"]
    days_back: int = 30
    limit: int = 1000
    sender_ids: list[str] = []


class AnalyzerRunResponse(BaseModel):
    ok: bool
    output: str
