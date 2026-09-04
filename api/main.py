"""FastAPI entry point for the I/O Operations Orchestrator.

Launch from the project root:

    uvicorn api.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.orchestrator import IOOperationsOrchestrator

# Resolve the web directory relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"


app = FastAPI(
    title="I/O Operations Orchestrator API",
    description="API wrapper around the IOOperationsOrchestrator pipeline.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str


@app.get("/")
def index():
    """Serve the web frontend (index.html)."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    """Run the orchestrator pipeline for the user's question.

    Returns the orchestrator result dict unchanged.
    """
    result = IOOperationsOrchestrator().run(request.message)
    return result


@app.get("/styles.css")
def styles_css():
    """Serve the stylesheet."""
    return FileResponse(WEB_DIR / "styles.css")


@app.get("/app.js")
def app_js():
    """Serve the frontend JavaScript."""
    return FileResponse(WEB_DIR / "app.js")
