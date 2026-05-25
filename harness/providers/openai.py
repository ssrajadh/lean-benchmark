"""OpenAI provider via openai SDK."""

from __future__ import annotations

import os
import time

import openai
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from harness.providers import ProviderResponse

load_dotenv()

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        _client = openai.OpenAI(api_key=api_key)
    return _client


@retry(
    retry=retry_if_exception_type(
        (openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError)
    ),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _generate(
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
        seed=seed,
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
