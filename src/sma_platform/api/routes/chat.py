"""Conversational AI chat — multi-turn RAG over SMA evidence base."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...reasoning.research_assistant import chat

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_HISTORY = 10

# ---------------------------------------------------------------------------
# In-memory rate limiter for chat endpoint
# ---------------------------------------------------------------------------
_chat_rate: dict[str, list[float]] = defaultdict(list)
CHAT_RATE_LIMIT = 10  # max requests per minute per IP
_CHAT_RATE_WINDOW = 60  # seconds


async def _check_chat_rate(request: Request) -> None:
    """Raise 429 if the client exceeds the chat rate limit."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _chat_rate[ip] = [t for t in _chat_rate[ip] if now - t < _CHAT_RATE_WINDOW]
    if len(_chat_rate[ip]) >= CHAT_RATE_LIMIT:
        raise HTTPException(429, "Rate limit exceeded")
    _chat_rate[ip].append(now)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    conversation_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=MAX_HISTORY)


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, request: Request):
    """Multi-turn conversational research assistant.

    Send a message with optional conversation history. The server is stateless —
    conversation context is maintained by the client sending previous exchanges.
    """
    await _check_chat_rate(request)

    history = req.history[-MAX_HISTORY:] if req.history else []
    conversation_id = req.conversation_id or str(uuid.uuid4())

    try:
        result = await chat(
            message=req.message,
            history=[{"role": m.role, "content": m.content} for m in history],
        )
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(500, detail="Chat temporarily unavailable")

    return {
        **result,
        "conversation_id": conversation_id,
    }
