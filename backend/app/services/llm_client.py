"""Single wrapper around the Groq API (spec §8.2). Every LLM call goes through here.

Responsibilities:
- read the model name, timeout and retry settings from config (never hard-coded),
- retry temporary failures (timeouts, 5xx, 429) with exponential backoff,
- ask for JSON and retry once with a nudge if the reply is not valid JSON,
- turn failures into AppError codes the frontend understands,
- log model / latency / token usage only — never prompt or report content.
"""

import json
import logging
import time
from functools import lru_cache
from typing import Any

import groq
from groq import Groq
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.errors import AppError

logger = logging.getLogger("medbridge.llm")

JSON_NUDGE = "\n\nReturn ONLY valid JSON. No text before or after the JSON object."
MAX_BACKOFF_SECONDS = 8.0


class _InvalidJSON(Exception):
    """Internal signal: the model replied, but not with valid JSON."""


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.GROQ_MODEL
        # The SDK's own retries are turned off (max_retries=0) so that retry logic
        # lives in one visible place: _call_with_retries below.
        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
            max_retries=0,
        )

    # ------------------------------------------------------------- public API

    async def chat_json(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        json_schema: dict[str, Any] | None = None,
        schema_name: str = "response",
    ) -> dict:
        """Ask the model for a JSON object and return it parsed.

        Uses Groq JSON mode (`response_format={"type": "json_object"}`). If the
        GROQ_USE_JSON_SCHEMA flag is on and a schema is given, uses Structured Outputs
        instead. If the reply is not valid JSON, retries once with a nudge.
        """
        if self.settings.GROQ_USE_JSON_SCHEMA and json_schema is not None:
            response_format: dict[str, Any] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": json_schema},
            }
        else:
            response_format = {"type": "json_object"}

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            return await self._json_attempt(messages, response_format, max_tokens)
        except _InvalidJSON:
            logger.warning("LLM returned invalid JSON; retrying once with a nudge")
        nudged = [messages[0], {"role": "user", "content": user + JSON_NUDGE}]
        try:
            return await self._json_attempt(nudged, response_format, max_tokens)
        except _InvalidJSON as exc:
            raise AppError(
                "LLM_UPSTREAM_ERROR",
                502,
                "The AI service returned an unreadable answer. Please try again.",
            ) from exc

    async def chat_text(
        self, system: str, messages: list[dict], *, max_tokens: int | None = None
    ) -> str:
        """Plain-text chat completion (used by the RAG answerer)."""
        full = [{"role": "system", "content": system}, *messages]
        return await run_in_threadpool(self._call_with_retries, full, None, max_tokens)

    # ------------------------------------------------------------- internals

    async def _json_attempt(
        self, messages: list[dict], response_format: dict, max_tokens: int | None
    ) -> dict:
        try:
            text = await run_in_threadpool(
                self._call_with_retries, messages, response_format, max_tokens
            )
        except groq.BadRequestError as exc:
            # Groq rejects JSON-mode replies that are not valid JSON with a 400
            # "json_validate_failed" error. Treat that the same as bad JSON.
            if "json_validate_failed" in str(exc):
                raise _InvalidJSON() from exc
            raise self._to_app_error(exc) from exc
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise _InvalidJSON() from exc
        if not isinstance(parsed, dict):
            raise _InvalidJSON()
        return parsed

    def _call_with_retries(
        self, messages: list[dict], response_format: dict | None, max_tokens: int | None
    ) -> str:
        """Blocking call to Groq with retries. Runs in a worker thread."""
        attempts = self.settings.GROQ_MAX_RETRIES + 1
        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.settings.GROQ_TEMPERATURE,
                    "max_tokens": max_tokens or self.settings.GROQ_MAX_TOKENS,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                completion = self.client.chat.completions.create(**kwargs)
                usage = getattr(completion, "usage", None)
                logger.info(
                    "LLM call ok: model=%s latency_ms=%d prompt_tokens=%s completion_tokens=%s",
                    self.model,
                    (time.perf_counter() - started) * 1000,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                )
                return completion.choices[0].message.content or ""
            except groq.BadRequestError:
                raise  # not temporary; handled by the caller
            except (
                groq.APITimeoutError,
                groq.APIConnectionError,
                groq.RateLimitError,
                groq.InternalServerError,
            ) as exc:
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s", attempt, attempts, type(exc).__name__
                )
                if attempt == attempts:
                    raise self._to_app_error(exc) from exc
                time.sleep(self._backoff_seconds(exc, attempt))
            except groq.APIStatusError as exc:  # other 4xx, e.g. 401 invalid key
                if exc.status_code == 401:
                    logger.error("Groq rejected the API key (401). Check GROQ_API_KEY in .env.")
                elif exc.status_code == 404:
                    logger.error("Groq model not found (404). Check GROQ_MODEL in .env.")
                raise self._to_app_error(exc) from exc
        raise AppError("LLM_UPSTREAM_ERROR", 502, "The AI service is unavailable.")  # unreachable

    @staticmethod
    def _backoff_seconds(exc: Exception, attempt: int) -> float:
        """Exponential backoff (1s, 2s, 4s…). For 429, respect Retry-After if present."""
        if isinstance(exc, groq.RateLimitError):
            retry_after = exc.response.headers.get("retry-after") if exc.response else None
            try:
                if retry_after is not None:
                    return min(float(retry_after), MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(2 ** (attempt - 1), MAX_BACKOFF_SECONDS)

    @staticmethod
    def _to_app_error(exc: Exception) -> AppError:
        if isinstance(exc, groq.APITimeoutError):
            return AppError(
                "LLM_TIMEOUT", 504, "The AI service took too long to respond. Please try again."
            )
        if isinstance(exc, groq.RateLimitError):
            return AppError(
                "RATE_LIMITED", 429, "Too many requests right now. Please wait a moment."
            )
        return AppError(
            "LLM_UPSTREAM_ERROR",
            502,
            "The AI service is having trouble right now. Please try again.",
        )


@lru_cache
def get_llm_client() -> LLMClient:
    """One shared client for the whole app (created on first use)."""
    return LLMClient(get_settings())
