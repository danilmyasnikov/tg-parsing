"""FastAPI application for the web UI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .startup import lifespan
from .api import router

STATIC_DIR = Path(__file__).parent / "static"


app = FastAPI(
    title="TG-Parsing Web UI",
    description="Chat interface for analyzing Telegram channel messages",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files and include API router
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)


@app.get("/")
async def root():
    """Serve the main chat interface."""
    return FileResponse(STATIC_DIR / "index.html")
