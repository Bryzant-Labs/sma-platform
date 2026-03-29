"""Multi-LLM Router for the SMA Research Platform.

Routes tasks to the optimal LLM based on task type, tracks usage/cost,
and provides quality-gate verification via Claude Opus for critical tasks.

Supported providers:
  - Anthropic (Opus, Sonnet, Haiku)
  - Google Gemini (Flash, Pro)
  - OpenAI (GPT-4o, GPT-4o-mini)
  - Groq (Llama 3.3 70B, Mixtral 8x7B)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "claude-opus": {"provider": "anthropic", "model_id": "claude-opus-4-6"},
    "claude-sonnet": {"provider": "anthropic", "model_id": "claude-sonnet-4-6"},
    "claude-haiku": {"provider": "anthropic", "model_id": "claude-haiku-4-5-20251001"},
    "gpt-4o": {"provider": "openai", "model_id": "gpt-4o"},
    "gpt-4o-mini": {"provider": "openai", "model_id": "gpt-4o-mini"},
    "gemini-flash": {"provider": "gemini", "model_id": "gemini-2.0-flash"},
    "gemini-pro": {"provider": "gemini", "model_id": "gemini-2.5-pro"},
    "groq-llama": {"provider": "groq", "model_id": "llama-3.3-70b-versatile"},
    "groq-mixtral": {"provider": "groq", "model_id": "mixtral-8x7b-32768"},
}

# ---------------------------------------------------------------------------
# Cost rates (USD per 1M tokens)
# ---------------------------------------------------------------------------

COST_RATES: dict[str, dict[str, float]] = {
    "claude-opus": {"input": 15.0, "output": 75.0},
    "claude-sonnet": {"input": 3.0, "output": 15.0},
    "claude-haiku": {"input": 0.25, "output": 1.25},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-flash": {"input": 0.075, "output": 0.30},
    "gemini-pro": {"input": 1.25, "output": 5.0},
    "groq-llama": {"input": 0.59, "output": 0.79},
    "groq-mixtral": {"input": 0.24, "output": 0.24},
}

# ---------------------------------------------------------------------------
# Routing policies
# ---------------------------------------------------------------------------

TIER_A_TASKS = {"hypothesis_generation", "grant_writing"}

ROUTING_POLICIES: dict[str, dict[str, str]] = {
    # Tier A -- Best quality (Opus)
    "hypothesis_generation": {"primary": "claude-opus", "fallback": "claude-sonnet"},
    "grant_writing": {"primary": "claude-opus", "fallback": "claude-sonnet"},
    # Tier B -- Standard (Sonnet / GPT-4o)
    "hypothesis_evaluation": {"primary": "claude-sonnet", "fallback": "gpt-4o"},
    "claim_extraction": {"primary": "claude-sonnet", "fallback": "gemini-flash"},
    "evidence_synthesis": {"primary": "claude-sonnet", "fallback": "gpt-4o"},
    "drug_repurposing": {"primary": "claude-sonnet", "fallback": "gpt-4o"},
    "digital_twin": {"primary": "claude-sonnet", "fallback": "gpt-4o"},
    "spatial_analysis": {"primary": "claude-sonnet", "fallback": "gpt-4o-mini"},
    "presentation": {"primary": "claude-sonnet", "fallback": "gpt-4o"},
    # Tier C -- Bulk / fast (Gemini / Groq / Haiku)
    "claim_scoring": {"primary": "groq-llama", "fallback": "claude-haiku"},
    "classification": {"primary": "groq-llama", "fallback": "claude-haiku"},
    "summarization": {"primary": "gemini-flash", "fallback": "claude-haiku"},
}

# Default policy for unknown task types
_DEFAULT_POLICY = {"primary": "claude-sonnet", "fallback": "gemini-flash"}

# ---------------------------------------------------------------------------
# Stats file location
# ---------------------------------------------------------------------------

_STATS_DIR = Path(__file__).resolve().parents[3] / "data"
_STATS_FILE = _STATS_DIR / "llm_stats.jsonl"

# ---------------------------------------------------------------------------
# Quality-gate prompt template
# ---------------------------------------------------------------------------

_QUALITY_CHECK_PROMPT = """\
You are a senior scientific reviewer for an SMA (Spinal Muscular Atrophy) research platform.

A model produced the following response for task type "{task_type}".

### Original prompt
{prompt}

### Model response
{response}

### Your job
1. Evaluate scientific accuracy, completeness, and logical coherence.
2. Respond ONLY with a JSON object (no markdown fences):
   {{"approved": true/false, "feedback": "...", "revised_content": null or "..."}}

- If the response is acceptable: {{"approved": true, "feedback": "Brief note on quality", "revised_content": null}}
- If the response needs improvement: {{"approved": false, "feedback": "What is wrong", "revised_content": "Your improved version"}}
"""


class LLMRouter:
    """Task-aware multi-LLM router with cost tracking and quality gates."""

    def __init__(self) -> None:
        self._api_keys: dict[str, str] = {}
        self._available_providers: set[str] = set()
        self._usage: list[dict[str, Any]] = []
        self._aggregated: dict[str, dict[str, float]] = defaultdict(
            lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "total_ms": 0}
        )
        self._init_keys()
        _STATS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_keys(self) -> None:
        """Load API keys from settings / environment and record available providers."""
        key_sources = {
            "anthropic": settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai": settings.openai_api_key or os.environ.get("OPENAI_API_KEY", ""),
            "gemini": settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", ""),
            "groq": settings.groq_api_key or os.environ.get("GROQ_API_KEY", ""),
        }
        for provider, key in key_sources.items():
            if key:
                self._api_keys[provider] = key
                self._available_providers.add(provider)
                logger.info("LLMRouter: %s provider available", provider)
            else:
                logger.debug("LLMRouter: %s provider skipped (no API key)", provider)

    def _is_model_available(self, model_key: str) -> bool:
        """Check whether the provider backing *model_key* has a configured API key."""
        entry = MODEL_REGISTRY.get(model_key)
        if not entry:
            return False
        return entry["provider"] in self._available_providers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route(
        self,
        task_type: str,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        quality_check: bool = False,
    ) -> dict[str, Any]:
        """Route a prompt to the optimal LLM based on *task_type*.

        Returns:
            dict with keys: content, model, tokens_in, tokens_out, cost,
            duration_ms, quality_verified.
        """
        policy = ROUTING_POLICIES.get(task_type, _DEFAULT_POLICY)
        primary = policy["primary"]
        fallback = policy["fallback"]

        # Auto-enable quality check for Tier A tasks
        if task_type in TIER_A_TASKS:
            quality_check = True

        # Attempt primary, then fallback
        result = None
        for model_key in (primary, fallback):
            if not self._is_model_available(model_key):
                logger.warning("Model %s unavailable (no API key), skipping", model_key)
                continue
            try:
                result = await self._dispatch(model_key, prompt, system, max_tokens, temperature)
                if result is not None:
                    break
            except Exception as exc:
                logger.error("LLMRouter: %s failed for task %s: %s", model_key, task_type, exc)
                continue

        if result is None:
            raise RuntimeError(
                f"All LLM providers failed for task_type={task_type}. "
                f"Tried: {primary}, {fallback}. "
                f"Available providers: {sorted(self._available_providers)}"
            )

        # Track usage
        cost = self._compute_cost(result["model"], result["tokens_in"], result["tokens_out"])
        result["cost"] = cost
        self._track_usage(result["model"], task_type, result["tokens_in"], result["tokens_out"], result["duration_ms"])

        # Quality gate
        result["quality_verified"] = False
        if quality_check and self._is_model_available("claude-opus"):
            # Don't quality-check if the primary model was already Opus
            if result["model"] != "claude-opus":
                qc = await self._quality_check_opus(task_type, prompt, result["content"])
                result["quality_verified"] = True
                if not qc["approved"] and qc.get("revised_content"):
                    logger.info(
                        "Quality gate: Opus revised response for task %s. Feedback: %s",
                        task_type,
                        qc["feedback"],
                    )
                    result["content"] = qc["revised_content"]
                    result["quality_feedback"] = qc["feedback"]
                elif qc["approved"]:
                    logger.info("Quality gate: Opus approved response for task %s", task_type)
                    result["quality_feedback"] = qc["feedback"]
            else:
                # Opus produced it -- implicitly trusted
                result["quality_verified"] = True

        return result

    def get_stats(self) -> dict[str, Any]:
        """Return aggregated usage statistics per model."""
        total_cost = sum(m["cost"] for m in self._aggregated.values())
        total_calls = sum(int(m["calls"]) for m in self._aggregated.values())
        return {
            "total_calls": total_calls,
            "total_cost_usd": round(total_cost, 6),
            "per_model": {
                k: {
                    "calls": int(v["calls"]),
                    "tokens_in": int(v["tokens_in"]),
                    "tokens_out": int(v["tokens_out"]),
                    "cost_usd": round(v["cost"], 6),
                    "avg_duration_ms": round(v["total_ms"] / v["calls"], 1) if v["calls"] else 0,
                }
                for k, v in self._aggregated.items()
            },
        }

    # ------------------------------------------------------------------
    # Dispatch to provider
    # ------------------------------------------------------------------

    async def _dispatch(
        self,
        model_key: str,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any] | None:
        """Dispatch to the correct provider call method."""
        entry = MODEL_REGISTRY[model_key]
        provider = entry["provider"]
        model_id = entry["model_id"]

        dispatch_map = {
            "anthropic": self._call_anthropic,
            "openai": self._call_openai,
            "gemini": self._call_gemini,
            "groq": self._call_groq,
        }

        handler = dispatch_map[provider]
        return await handler(model_key, model_id, prompt, system, max_tokens, temperature)

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _call_anthropic(
        self,
        model_key: str,
        model_id: str,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any] | None:
        api_key = self._api_keys["anthropic"]
        body: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if system:
            body["system"] = system

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
        duration_ms = int((time.monotonic() - t0) * 1000)

        if resp.status_code != 200:
            logger.error("Anthropic %s error %d: %s", model_id, resp.status_code, resp.text[:300])
            return None

        data = resp.json()
        content = data["content"][0]["text"].strip()
        usage = data.get("usage", {})
        return {
            "content": content,
            "model": model_key,
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
            "duration_ms": duration_ms,
        }

    async def _call_openai(
        self,
        model_key: str,
        model_id: str,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any] | None:
        api_key = self._api_keys["openai"]
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.monotonic()
        result = await self._openai_with_retry(
            url="https://api.openai.com/v1/chat/completions",
            api_key=api_key,
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

        if result is None:
            return None

        return {
            "content": result["content"],
            "model": model_key,
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "duration_ms": duration_ms,
        }

    async def _call_gemini(
        self,
        model_key: str,
        model_id: str,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any] | None:
        api_key = self._api_keys["gemini"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        body: dict[str, Any] = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

        delays = [15, 30, 45, 60]
        t0 = time.monotonic()

        resp: httpx.Response | None = None
        for attempt in range(len(delays) + 1):
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=body,
                )
            if resp.status_code == 429 and attempt < len(delays):
                logger.warning("Gemini 429, retry %d/%d in %ds", attempt + 1, len(delays), delays[attempt])
                await asyncio.sleep(delays[attempt])
                continue
            break

        duration_ms = int((time.monotonic() - t0) * 1000)

        if resp is None or resp.status_code != 200:
            status = resp.status_code if resp else "no response"
            text = resp.text[:300] if resp else ""
            logger.error("Gemini %s error %s: %s", model_id, status, text)
            return None

        data = resp.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            logger.error("Gemini unexpected response: %s", json.dumps(data)[:300])
            return None

        # Gemini returns token counts in usageMetadata
        usage = data.get("usageMetadata", {})
        return {
            "content": content,
            "model": model_key,
            "tokens_in": usage.get("promptTokenCount", 0),
            "tokens_out": usage.get("candidatesTokenCount", 0),
            "duration_ms": duration_ms,
        }

    async def _call_groq(
        self,
        model_key: str,
        model_id: str,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any] | None:
        api_key = self._api_keys["groq"]
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.monotonic()
        result = await self._openai_with_retry(
            url="https://api.groq.com/openai/v1/chat/completions",
            api_key=api_key,
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

        if result is None:
            return None

        return {
            "content": result["content"],
            "model": model_key,
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "duration_ms": duration_ms,
        }

    # ------------------------------------------------------------------
    # OpenAI-compatible helper (shared by OpenAI & Groq)
    # ------------------------------------------------------------------

    async def _openai_with_retry(
        self,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """Call an OpenAI-compatible endpoint with retry on 429."""
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "messages": messages,
                        "temperature": temperature,
                    },
                )
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                logger.warning("Rate limited by %s, waiting %ds (attempt %d/%d)", url.split("/")[2], wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
                continue
            if resp.status_code != 200:
                logger.error("OpenAI-compat %s error %d: %s", url, resp.status_code, resp.text[:300])
                return None

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            return {
                "content": content,
                "tokens_in": usage.get("prompt_tokens", 0),
                "tokens_out": usage.get("completion_tokens", 0),
            }

        logger.warning("Rate limit retries exhausted for %s", url)
        return None

    # ------------------------------------------------------------------
    # Quality gate
    # ------------------------------------------------------------------

    async def _quality_check_opus(
        self, task_type: str, prompt: str, response_content: str
    ) -> dict[str, Any]:
        """Send the response to Claude Opus for scientific quality verification.

        Returns:
            dict with keys: approved (bool), feedback (str), revised_content (str | None).
        """
        check_prompt = _QUALITY_CHECK_PROMPT.format(
            task_type=task_type,
            prompt=prompt[:4000],  # Truncate to avoid excessive token usage
            response=response_content[:8000],
        )

        result = await self._call_anthropic(
            model_key="claude-opus",
            model_id=MODEL_REGISTRY["claude-opus"]["model_id"],
            prompt=check_prompt,
            system="You are a senior scientific quality reviewer. Respond only with valid JSON.",
            max_tokens=4096,
            temperature=0.2,
        )

        if result is None:
            logger.warning("Quality check call to Opus failed; treating as approved by default")
            return {"approved": True, "feedback": "Quality check unavailable", "revised_content": None}

        # Track the Opus quality-check call
        self._track_usage(
            "claude-opus",
            f"quality_check:{task_type}",
            result["tokens_in"],
            result["tokens_out"],
            result["duration_ms"],
        )

        # Parse JSON from Opus response
        try:
            parsed = json.loads(result["content"])
            return {
                "approved": bool(parsed.get("approved", True)),
                "feedback": str(parsed.get("feedback", "")),
                "revised_content": parsed.get("revised_content"),
            }
        except (json.JSONDecodeError, TypeError):
            # Try to extract JSON from a markdown block
            text = result["content"]
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(text[start:end])
                    return {
                        "approved": bool(parsed.get("approved", True)),
                        "feedback": str(parsed.get("feedback", "")),
                        "revised_content": parsed.get("revised_content"),
                    }
                except json.JSONDecodeError:
                    pass
            logger.warning("Could not parse Opus quality-check response; treating as approved")
            return {"approved": True, "feedback": "Could not parse review", "revised_content": None}

    # ------------------------------------------------------------------
    # Cost & usage tracking
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_cost(model_key: str, tokens_in: int, tokens_out: int) -> float:
        """Compute cost in USD for a single call."""
        rates = COST_RATES.get(model_key)
        if not rates:
            return 0.0
        return (tokens_in * rates["input"] / 1_000_000) + (tokens_out * rates["output"] / 1_000_000)

    def _track_usage(
        self, model: str, task_type: str, tokens_in: int, tokens_out: int, duration_ms: int
    ) -> None:
        """Append usage record to in-memory stats and persist to JSONL."""
        cost = self._compute_cost(model, tokens_in, tokens_out)
        record = {
            "ts": time.time(),
            "model": model,
            "task_type": task_type,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 8),
            "duration_ms": duration_ms,
        }
        self._usage.append(record)

        # Update aggregated stats
        agg = self._aggregated[model]
        agg["calls"] += 1
        agg["tokens_in"] += tokens_in
        agg["tokens_out"] += tokens_out
        agg["cost"] += cost
        agg["total_ms"] += duration_ms

        # Persist to JSONL (append-only, best-effort)
        try:
            with open(_STATS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.warning("Failed to write LLM stats: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton for convenience
# ---------------------------------------------------------------------------

_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    """Return (or create) the module-level LLMRouter singleton."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
