"""Main evaluation runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from harness.corpus import Obligation, load_corpus
from harness.prompts import baseline_prompt, oracle_prompt
from harness.providers import ProviderResponse, generate
from harness.verifier import VerificationResult, verify

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
LEAN_PROJECT = Path(__file__).resolve().parent.parent / "lean_project"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"

console = Console()


def _prompt_hash(system: str, user: str) -> str:
    blob = f"{system}\n---\n{user}".encode()
    return hashlib.sha256(blob).hexdigest()


def _sanitize(obj):
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _extract_proof(text: str) -> str:
    m = re.search(r"```(?:lean)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def _cache_path(model: str, ph: str) -> Path:
    safe_model = model.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe_model}_{ph[:16]}.json"


def _load_cache(model: str, ph: str) -> ProviderResponse | None:
    p = _cache_path(model, ph)
    if p.exists():
        return ProviderResponse.model_validate_json(p.read_text())
    return None


def _save_cache(model: str, ph: str, resp: ProviderResponse) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = _sanitize(resp.model_dump())
    _cache_path(model, ph).write_text(json.dumps(data))


def _cell_key(ob_id: str, model: str, condition: str, sample_idx: int) -> str:
    return f"{ob_id}|{model}|{condition}|{sample_idx}"


def _load_completed(output_path: Path) -> set[str]:
    done: set[str] = set()
    if not output_path.exists():
        return done
    for line in output_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            key = _cell_key(
                row["obligation_id"], row["model"],
                row["condition"], row["sample_idx"],
            )
            done.add(key)
        except (json.JSONDecodeError, KeyError):
            continue
    return done


def _build_cells(
    obligations: list[Obligation],
    models: list[str],
    conditions: list[str],
    samples: int,
) -> list[tuple[Obligation, str, str, int]]:
    cells = []
    for ob in obligations:
        for model in models:
            for cond in conditions:
                for s in range(samples):
                    cells.append((ob, model, cond, s))
    return cells


def _run_cell(
    ob: Obligation,
    model: str,
    condition: str,
    sample_idx: int,
    output_file,
    use_cache: bool = True,
) -> None:
    if condition == "baseline":
        system, user = baseline_prompt(ob)
    elif condition == "oracle":
        system, user = oracle_prompt(ob)
    else:
        raise ValueError(f"Unknown condition: {condition}")

    ph = _prompt_hash(system, user)

    cached = _load_cache(model, ph) if use_cache else None
    if cached is not None:
        provider_resp = cached
    else:
        temperature = 0.0 if sample_idx == 0 else 0.6
        seed = sample_idx if sample_idx == 0 else None
        provider_resp = generate(
            model=model,
            prompt=user,
            system=system,
            temperature=temperature,
            seed=seed,
        )
        if provider_resp.error is None:
            _save_cache(model, ph, provider_resp)

    if provider_resp.error:
        verif = VerificationResult(
            outcome="other_failure",
            raw_stderr=f"provider error: {provider_resp.error}",
            raw_stdout="",
            duration_ms=0,
            lean_file_path="",
        )
    else:
        proof = _extract_proof(provider_resp.text)
        verif = verify(ob, proof, LEAN_PROJECT)

    row = {
        "obligation_id": ob.id,
        "model": model,
        "condition": condition,
        "sample_idx": sample_idx,
        "prompt_hash": ph,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": _sanitize(provider_resp.model_dump()),
        "verification": verif.model_dump(),
    }
    line = json.dumps(row, default=str)
    output_file.write(line + "\n")
    output_file.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run proof generation benchmark")
    parser.add_argument(
        "--obligations", default="corpus/*.json",
        help="Glob pattern for obligation JSON files (default: corpus/*.json)",
    )
    parser.add_argument(
        "--models", nargs="+", required=True,
        help="Model identifiers to evaluate",
    )
    parser.add_argument(
        "--conditions", nargs="+", default=["baseline"],
        choices=["baseline", "oracle"],
        help="Prompt conditions (default: baseline)",
    )
    parser.add_argument(
        "--samples", type=int, default=3,
        help="Number of samples per cell (default: 3)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSONL path (default: results/run_<timestamp>.jsonl)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print cells that would run without calling APIs",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable provider response cache",
    )
    args = parser.parse_args()

    glob_pattern = args.obligations
    if "/" in glob_pattern:
        base = Path(glob_pattern).parent
        pattern = Path(glob_pattern).name
    else:
        base = CORPUS_DIR
        pattern = glob_pattern
    matched_files = sorted(base.glob(pattern))
    if not matched_files:
        console.print(f"[red]No files matching {glob_pattern}[/red]")
        sys.exit(1)
    matched_stems = {p.stem for p in matched_files}
    obligations = [ob for ob in load_corpus(CORPUS_DIR) if ob.id in matched_stems]
    if not obligations:
        console.print("[red]No valid obligations found[/red]")
        sys.exit(1)

    cells = _build_cells(obligations, args.models, args.conditions, args.samples)

    if args.output:
        output_path = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = RESULTS_DIR / f"run_{ts}.jsonl"

    if args.dry_run:
        completed = _load_completed(output_path)
        skip = 0
        run = 0
        for ob, model, cond, s in cells:
            key = _cell_key(ob.id, model, cond, s)
            if key in completed:
                skip += 1
                continue
            run += 1
            console.print(f"  {ob.id} | {model} | {cond} | sample={s}")
        console.print(f"\n[green]{run} cells to run[/green], [dim]{skip} already done[/dim]")
        return

    completed = _load_completed(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    to_run = []
    for cell in cells:
        ob, model, cond, s = cell
        if _cell_key(ob.id, model, cond, s) not in completed:
            to_run.append(cell)

    console.print(
        f"[bold]{len(to_run)} cells to run[/bold] "
        f"({len(cells) - len(to_run)} already done)"
    )

    with open(output_path, "a") as f:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Running", total=len(to_run))
            for ob, model, cond, s in to_run:
                desc = f"{ob.id} | {model} | {cond} | s={s}"
                progress.update(task, description=desc)
                try:
                    _run_cell(ob, model, cond, s, f, use_cache=not args.no_cache)
                except Exception as exc:
                    console.print(f"[red]ERROR {desc}:[/red] {exc}")
                    row = {
                        "obligation_id": ob.id,
                        "model": model,
                        "condition": cond,
                        "sample_idx": s,
                        "prompt_hash": "",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "provider": None,
                        "verification": None,
                        "error": str(exc),
                    }
                    f.write(json.dumps(row, default=str) + "\n")
                    f.flush()
                progress.advance(task)

    console.print(f"\n[green]Done.[/green] Results: {output_path}")


if __name__ == "__main__":
    main()
