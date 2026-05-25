"""Smoke test: hit each provider once with a trivial prompt."""

from rich.console import Console

from harness.providers import generate

console = Console()

MODELS = [
    "gemini-2.5-flash",
    "gpt-4o-mini",
    "deepseek-ai/deepseek-v4-flash",
]

PROMPT = "What is 2 + 2? Reply with just the number."

for model in MODELS:
    console.rule(model)
    try:
        resp = generate(model=model, prompt=PROMPT)
        console.print(f"[green]text:[/green] {resp.text.strip()}")
        console.print(
            f"tokens: in={resp.input_tokens} out={resp.output_tokens}  "
            f"latency={resp.latency_ms}ms"
        )
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
