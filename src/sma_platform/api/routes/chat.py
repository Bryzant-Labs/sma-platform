"""Conversational AI chat — multi-turn RAG over SMA evidence base."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...reasoning.research_assistant import chat

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_HISTORY = 10


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    conversation_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=MAX_HISTORY)


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Multi-turn conversational research assistant.

    Send a message with optional conversation history. The server is stateless —
    conversation context is maintained by the client sending previous exchanges.
    """
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
