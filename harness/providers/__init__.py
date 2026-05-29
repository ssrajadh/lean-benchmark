"""LLM provider dispatch."""

from __future__ import annotations

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
    if model.startswith("gpt-"):
        from harness.providers.openai import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    elif model.startswith("qwen/") or model.startswith("qwen-"):
        from harness.providers.nim import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    elif model.startswith("deepseek/") or model.startswith("accounts/fireworks/"):
        from harness.providers.fireworks import _generate

        return _generate(model, prompt, system, max_tokens, temperature, seed)
    else:
        raise ValueError(
            f"Unknown model prefix: {model!r}. "
            "Supported prefixes: gpt-*, qwen/*, qwen-*, deepseek/*, accounts/fireworks/*."
        )
