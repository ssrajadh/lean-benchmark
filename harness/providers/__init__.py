"""LLM provider dispatch."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProviderResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    raw: dict[str, Any]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    error: str | None = None


def generate(
    model: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    seed: int | None = None,
) -> ProviderResponse:
    if model.startswith("gemini-"):
        from harness.providers.gemini import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    elif model.startswith("gpt-"):
        from harness.providers.openai import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    elif model.startswith("deepseek-ai/"):
        from harness.providers.deepseek import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    else:
        raise ValueError(
            f"Unknown model prefix: {model!r}. "
            "Expected gemini-*, gpt-*, or deepseek-ai/*."
        )
