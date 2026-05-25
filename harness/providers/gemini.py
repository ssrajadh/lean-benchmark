"""Google Gemini provider via google-genai SDK."""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from harness.providers import ProviderResponse

load_dotenv()

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


@retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
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
