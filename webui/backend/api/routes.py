from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
import logging
import os

import collector
from analyzer.context_loader import MessageRow, format_messages
from analyzer.llm_client import analyze_text
from analyzer.prompts import TOPIC_EXTRACTION_PROMPT, STYLE_ANALYSIS_PROMPT

from ..database import DEFAULT_PG_DSN, get_unique_senders_conn, get_messages_by_senders_conn
from collector.storage.postgres_store import get_conn
from ..llm import chat_with_context, get_available_models
from .schemas import (
    ChatRequest,
    ChatResponse,
    SenderInfo,
    ModelInfo,
    SelectedIdsRequest,
    DBStatusResponse,
    DBClearResponse,
    CollectorFetchRequest,
    CollectorFetchResponse,
    CollectorFetchDetail,
    AnalyzerRunRequest,
    AnalyzerRunResponse,
)

logger = logging.getLogger("webui")

router = APIRouter()

# Persistent selected sender IDs (module-level state inside routes)
selected_ids: list[str] = []


async def _load_recent_messages_from_conn(
    conn,
    *,
    sender_ids: list[str] | None,
    days_back: int,
    limit: int,
) -> str:
    """Load recent messages using an existing DB connection and format them."""
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    params: list[object] = [since]

    query = "SELECT sender_id, id, date, text FROM messages WHERE date >= $1 "
    if sender_ids:
        query += "AND sender_id = ANY($2) "
        params.append(sender_ids)
        limit_param = "$3"
    else:
        limit_param = "$2"

    query += f"ORDER BY date DESC LIMIT {limit_param}"
    params.append(limit)

    rows = await conn.fetch(query, *params)
    if not rows:
        rows = await conn.fetch(
            "SELECT sender_id, id, date, text FROM messages ORDER BY date DESC LIMIT $1",
            limit,
        )

    message_rows = [
        MessageRow(
            sender_id=str(r["sender_id"]),
            message_id=int(r["id"]),
            date=r["date"],
            text=r["text"],
        )
        for r in rows
    ]
    message_rows.reverse()
    return format_messages(message_rows)


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


@router.get("/api/db/status", response_model=DBStatusResponse)
async def db_status(conn=Depends(get_conn)):
    """Return basic database stats for UI status indicators."""
    try:
        exists = await conn.fetchval(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'messages'
            """
        )
        if not exists:
            return DBStatusResponse(message_count=0, sender_count=0, latest_message_at=None)

        message_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        sender_count = await conn.fetchval("SELECT COUNT(DISTINCT sender_id) FROM messages")
        latest = await conn.fetchval("SELECT MAX(date) FROM messages")
        latest_iso = latest.isoformat() if latest else None
        return DBStatusResponse(
            message_count=int(message_count or 0),
            sender_count=int(sender_count or 0),
            latest_message_at=latest_iso,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/api/db/clear", response_model=DBClearResponse)
async def clear_db(conn=Depends(get_conn)):
    """Drop and recreate the messages table."""
    try:
        await conn.execute("DROP TABLE IF EXISTS messages;")
        await conn.execute(
            """
            CREATE TABLE messages (
                sender_id TEXT,
                id BIGINT,
                date TIMESTAMP WITH TIME ZONE,
                text TEXT,
                has_media BOOLEAN,
                PRIMARY KEY (sender_id, id)
            )
            """
        )
        row_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        if row_count != 0:
            raise HTTPException(
                status_code=500,
                detail=f"messages table not empty after reset (row_count={row_count})",
            )
        return DBClearResponse(ok=True, message="Messages table reset.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/api/collector/fetch", response_model=CollectorFetchResponse)
async def collector_fetch(request: CollectorFetchRequest):
    """Fetch messages from Telegram and store them in Postgres."""
    targets = [t.strip() for t in request.targets if t and t.strip()]
    if not targets:
        raise HTTPException(status_code=400, detail="targets cannot be empty")

    limit = max(1, int(request.limit or 1))
    try:
        api_id, api_hash = collector.get_api_credentials()
        session_name = os.getenv("SESSION_NAME", "session")
        pg_dsn = os.getenv("PG_DSN", DEFAULT_PG_DSN)
        await collector.init_pg_pool(pg_dsn)

        details: list[CollectorFetchDetail] = []
        total = 0

        async with collector.create_client(session_name, api_id, api_hash) as client:
            for target in targets:
                try:
                    entity = await collector.resolve(client, target)
                    if entity is None:
                        details.append(
                            CollectorFetchDetail(
                                target=target,
                                processed=0,
                                error="Failed to resolve target",
                            )
                        )
                        continue

                    count = await collector.consume_messages(
                        client,
                        entity,
                        store_func=collector.postgres_store,
                        limit=limit,
                    )
                    total += count
                    details.append(CollectorFetchDetail(target=target, processed=count))
                except Exception as e:
                    details.append(
                        CollectorFetchDetail(
                            target=target,
                            processed=0,
                            error=str(e),
                        )
                    )

        return CollectorFetchResponse(ok=True, processed=total, details=details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collector error: {str(e)}")


@router.post("/api/analyzer/run", response_model=AnalyzerRunResponse)
async def analyzer_run(request: AnalyzerRunRequest, conn=Depends(get_conn)):
    """Run analyzer jobs over recent messages."""
    job = request.job
    days_back = max(1, int(request.days_back or 1))
    limit = max(1, int(request.limit or 1))
    sender_ids = [s for s in request.sender_ids if s]

    if job == "topics":
        prompt = TOPIC_EXTRACTION_PROMPT
    elif job == "style":
        prompt = STYLE_ANALYSIS_PROMPT
    else:
        prompt = (
            "You are an assistant. OUTPUT ONLY valid JSON (no commentary). "
            "Return an object with keys: \"overall\" and \"messages\". "
            "\"overall\" must be an object: { \"label\": \"positive\"|\"neutral\"|\"negative\", "
            "\"score\": 0.0-1.0 }. "
            "\"messages\" must be an array of objects each with: "
            "{ \"id\": int, \"sender_id\": str, \"snippet\": str, "
            "\"sentiment\": \"positive\"|\"neutral\"|\"negative\", \"score\": 0.0-1.0 }. "
            "Analyze the DATA below and provide sentiment per message (use snippets up to 200 chars). "
            "If there is no data, return {\"overall\": {\"label\": \"neutral\", \"score\": 0.0}, "
            "\"messages\": []}."
        )

    try:
        context = await _load_recent_messages_from_conn(
            conn,
            sender_ids=sender_ids if sender_ids else None,
            days_back=days_back,
            limit=limit,
        )
        output = await analyze_text(prompt, context)
        return AnalyzerRunResponse(ok=True, output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyzer error: {str(e)}")


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
