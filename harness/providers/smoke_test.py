"""Smoke test: hit each provider once with a trivial prompt."""

from rich.console import Console

from harness.providers import generate
from harness.providers.openai import DEFAULT_MODEL as OPENAI_MODEL
from harness.providers.nim import DEFAULT_MODEL as NIM_MODEL
from harness.providers.fireworks import DEFAULT_MODEL as FIREWORKS_MODEL

console = Console()

MODELS = [OPENAI_MODEL, NIM_MODEL, FIREWORKS_MODEL]
PROMPT = "What is 2+2? Respond with only a single number."

for model in MODELS:
    console.rule(model)
    resp = generate(model=model, prompt=PROMPT)
    if resp.error:
        console.print(f"[red]ERROR:[/red] {resp.error}")
    else:
        console.print(f"[green]text:[/green] {resp.text.strip()}")
        console.print(
            f"tokens: in={resp.input_tokens} out={resp.output_tokens}  "
            f"latency={resp.latency_ms}ms"
        )
