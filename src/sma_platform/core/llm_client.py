"""Multi-LLM client for claim extraction and other tasks.

Supports Groq (Llama 3.3), Gemini Flash, OpenAI GPT-4o, and Anthropic Claude.
All providers return the same format: a string of text content.

Default: Groq for bulk extraction (fast, cheap/free).
Fallback chain: Groq → Gemini → OpenAI → Anthropic.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Provider configs: (api_url, model, auth_header_builder, request_builder, response_parser)

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 4096,
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "model": "gemini-2.0-flash",
        "max_tokens": 4096,
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "max_tokens": 4096,
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
    },
}

# Fallback order when primary provider fails
FALLBACK_CHAIN = ["groq", "gemini", "openai", "anthropic"]


def _get_api_key(provider: str) -> str:
    """Get API key for a provider from settings or environment."""
    key_map = {
        "groq": settings.groq_api_key or os.environ.get("GROQ_API_KEY", ""),
        "gemini": settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", ""),
        "openai": settings.openai_api_key or os.environ.get("OPENAI_API_KEY", ""),
        "anthropic": settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    return key_map.get(provider, "")


async def _call_openai_compatible(
    url: str, model: str, api_key: str, prompt: str, max_tokens: int
) -> str | None:
    """Call OpenAI-compatible API (Groq, OpenAI) with retry on rate limit."""
    max_retries = 3
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
            )
        if resp.status_code == 429:
            # Rate limited — wait and retry
            wait = 10 * (attempt + 1)
            logger.info("Rate limited by %s, waiting %ds (attempt %d/%d)", url.split("/")[2], wait, attempt + 1, max_retries)
            await asyncio.sleep(wait)
            continue
        if resp.status_code != 200:
            logger.error("%s API error %d: %s", url, resp.status_code, resp.text[:200])
            return None
        body = resp.json()
        return body["choices"][0]["message"]["content"].strip()
    logger.warning("Rate limit retries exhausted for %s", url)
    return None


async def _call_anthropic(api_key: str, prompt: str, max_tokens: int, model: str) -> str | None:
    """Call Anthropic Messages API."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
    if resp.status_code != 200:
        logger.error("Anthropic API error %d: %s", resp.status_code, resp.text[:200])
        return None
    body = resp.json()
    return body["content"][0]["text"].strip()


async def _call_gemini(api_key: str, prompt: str, max_tokens: int, model: str) -> str | None:
    """Call Google Gemini API with retry on 429."""
    import asyncio

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    delays = [15, 30, 45, 60, 75]

    for attempt in range(len(delays) + 1):
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.1,
                    },
                },
            )
        if resp.status_code == 429 and attempt < len(delays):
            delay = delays[attempt]
            logger.warning("Gemini 429 rate limit, retry %d/%d in %ds", attempt + 1, len(delays), delay)
            await asyncio.sleep(delay)
            continue
        break

    if resp.status_code != 200:
        logger.error("Gemini API error %d: %s", resp.status_code, resp.text[:200])
        return None
    body = resp.json()
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        logger.error("Gemini unexpected response: %s", json.dumps(body)[:300])
        return None


async def call_llm(prompt: str, provider: str | None = None, max_tokens: int = 4096) -> tuple[str | None, str]:
    """Call an LLM with automatic fallback.

    Args:
        prompt: The prompt text.
        provider: Preferred provider. If None, uses settings.extraction_llm.
        max_tokens: Max output tokens.

    Returns:
        Tuple of (response_text, provider_used). response_text is None if all providers fail.
    """
    preferred = provider or settings.extraction_llm
    # Build fallback chain starting with preferred
    chain = [preferred] + [p for p in FALLBACK_CHAIN if p != preferred]

    for p in chain:
        api_key = _get_api_key(p)
        if not api_key:
            logger.debug("Skipping %s — no API key", p)
            continue

        try:
            cfg = PROVIDERS[p]
            if p == "anthropic":
                result = await _call_anthropic(api_key, prompt, max_tokens, cfg["model"])
            elif p == "gemini":
                result = await _call_gemini(api_key, prompt, max_tokens, cfg["model"])
            else:
                # OpenAI-compatible (Groq, OpenAI)
                result = await _call_openai_compatible(cfg["url"], cfg["model"], api_key, prompt, max_tokens)

            if result:
                logger.info("LLM call succeeded via %s (%s)", p, cfg["model"])
                return result, p

        except Exception as e:
            logger.warning("LLM call to %s failed: %s", p, e)
            continue

    logger.error("All LLM providers failed")
    return None, "none"
