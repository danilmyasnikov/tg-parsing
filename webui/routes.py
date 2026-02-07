from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import logging

from .database import get_unique_senders_conn, get_messages_by_senders_conn
from collector.storage.postgres_store import get_conn
from .llm import chat_with_context, get_available_models
from .schemas import (
    ChatRequest,
    ChatResponse,
    SenderInfo,
    ModelInfo,
    SelectedIdsRequest,
)

logger = logging.getLogger("webui")

router = APIRouter()

# Persistent selected sender IDs (module-level state inside routes)
selected_ids: list[str] = []


@router.put("/api/selected-ids")
async def update_selected_ids(request: SelectedIdsRequest):
    """Update the selected sender IDs list and log to console."""
    global selected_ids
    selected_ids = request.sender_ids
    print(f"[webui] selected_ids updated: {selected_ids}")
    logger.info(f"selected_ids updated: {selected_ids}")
    return {"selected_ids": selected_ids}


@router.get("/api/selected-ids")
async def get_selected_ids():
    """Return the current selected sender IDs."""
    return {"selected_ids": selected_ids}


@router.get("/api/senders", response_model=list[SenderInfo])
async def list_senders(conn=Depends(get_conn)):
    """Get list of unique senders from the database (uses injected conn)."""
    try:
        senders = await get_unique_senders_conn(conn)
        return senders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/api/models", response_model=list[ModelInfo])
async def list_models():
    """Get list of available LLM models."""
    return get_available_models()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, conn=Depends(get_conn)):
    """Send a chat message and get a response."""
    try:
        # Get context messages if senders are selected
        context_messages = []
        if request.sender_ids:
            context_messages = await get_messages_by_senders_conn(
                conn, request.sender_ids, limit=request.message_limit
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


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
