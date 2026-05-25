"""DeepSeek-Prover V2 on Fireworks AI (OpenAI-compatible)."""

from __future__ import annotations

import os
import time

import openai
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from harness.providers import ProviderResponse
from harness.providers.rate_limit import RateLimiter

load_dotenv()

_client: openai.OpenAI | None = None
_limiter = RateLimiter(min_interval=0.0)

_BASE_URL = "https://api.fireworks.ai/inference/v1"
DEFAULT_MODEL = "accounts/fireworks/models/deepseek-v4-pro"


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("FIREWORKS_API_KEY")
        if not api_key:
            raise RuntimeError("FIREWORKS_API_KEY not set")
        _client = openai.OpenAI(api_key=api_key, base_url=_BASE_URL)
    return _client


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
        return True
    if isinstance(exc, openai.InternalServerError):
        return True
    if isinstance(exc, openai.RateLimitError):
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
        return ProviderResponse(
            text="",
            raw={},
            model=model,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            error=str(exc),
        )


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
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.monotonic()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    usage = response.usage
    return ProviderResponse(
        text=response.choices[0].message.content or "",
        raw=response.model_dump(),
        model=model,
        latency_ms=latency_ms,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )
