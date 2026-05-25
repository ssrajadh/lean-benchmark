"""Google Gemini provider via google-genai SDK (AI Studio free tier)."""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from harness.providers import ProviderResponse
from harness.providers.rate_limit import RateLimiter

load_dotenv()

_client: genai.Client | None = None
_limiter = RateLimiter(min_interval=8.0)

DEFAULT_MODEL = "gemini-3.5-flash"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _is_daily_limit(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "resource_exhausted" in msg and ("per day" in msg or "daily" in msg)


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, ClientError):
        if _is_daily_limit(exc):
            return False
        if "429" in str(exc) or "rate" in str(exc).lower():
            return True
    return False


def _generate(
    model: str,
    prompt: str,
    system: str | None,
    max_tokens: int,
    temperature: float,
    seed: int | None,
) -> ProviderResponse:
    _limiter.acquire()

    try:
        return _call_api(model, prompt, system, max_tokens, temperature, seed)
    except Exception as exc:
        if _is_daily_limit(exc):
            return ProviderResponse(
                text="",
                raw={},
                model=model,
                latency_ms=0,
                input_tokens=0,
                output_tokens=0,
                error="daily_limit_exhausted",
            )
        raise


@retry(
    retry=retry_if_exception(_should_retry),
    wait=wait_exponential(multiplier=1, min=30, max=300),
    stop=stop_after_attempt(6),
    reraise=True,
)
def _call_api(
    model: str,
    prompt: str,
    system: str | None,
    max_tokens: int,
    temperature: float,
    seed: int | None,
) -> ProviderResponse:
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        seed=seed,
        system_instruction=system,
    )

    t0 = time.monotonic()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    usage = response.usage_metadata
    return ProviderResponse(
        text=response.text or "",
        raw=response.model_dump(),
        model=model,
        latency_ms=latency_ms,
        input_tokens=usage.prompt_token_count or 0 if usage else 0,
        output_tokens=usage.candidates_token_count or 0 if usage else 0,
    )
