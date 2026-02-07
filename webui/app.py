"""FastAPI application for the web UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .database import get_unique_senders, get_messages_by_senders, close_pool
from .llm import chat_with_context, get_available_models

import logging
import os
from pathlib import Path

logger = logging.getLogger("webui")
logging.basicConfig(level=logging.INFO)

# Persistent selected sender IDs (module-level state)
selected_ids: list[str] = []

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield
    # Cleanup on shutdown
    await close_pool()


app = FastAPI(
    title="TG-Parsing Web UI",
    description="Chat interface for analyzing Telegram channel messages",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Request/Response models
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


# Request model for selected IDs
class SelectedIdsRequest(BaseModel):
    sender_ids: list[str] = []


# API Routes
@app.get("/")
async def root():
    """Serve the main chat interface."""
    return FileResponse(STATIC_DIR / "index.html")


@app.put("/api/selected-ids")
async def update_selected_ids(request: SelectedIdsRequest):
    """Update the selected sender IDs list and log to console."""
    global selected_ids
    selected_ids = request.sender_ids
    print(f"[webui] selected_ids updated: {selected_ids}")
    logger.info(f"selected_ids updated: {selected_ids}")
    return {"selected_ids": selected_ids}


@app.get("/api/selected-ids")
async def get_selected_ids():
    """Return the current selected sender IDs."""
    return {"selected_ids": selected_ids}


@app.get("/api/senders", response_model=list[SenderInfo])
async def list_senders():
    """Get list of unique senders from the database."""
    try:
        senders = await get_unique_senders()
        return senders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/models", response_model=list[ModelInfo])
async def list_models():
    """Get list of available LLM models."""
    return get_available_models()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get a response."""
    try:
        # Get context messages if senders are selected
        context_messages = []
        if request.sender_ids:
            context_messages = await get_messages_by_senders(
                request.sender_ids, 
                limit=request.message_limit
            )
        
        # Get response from LLM
        response = await chat_with_context(
            user_message=request.message,
            context_messages=context_messages,
            model_id=request.model_id,
        )
        
        return ChatResponse(
            response=response,
            context_message_count=len(context_messages),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
