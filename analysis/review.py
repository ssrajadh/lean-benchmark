"""Interactive failure review and labeling tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from analysis.taxonomy import CATEGORIES, DESCRIPTIONS

console = Console()


def _cell_key(row: dict) -> str:
    return f"{row['obligation_id']}|{row['model']}|{row['condition']}|{row['sample_idx']}"


def _load_labels(path: Path) -> dict[str, dict]:
    labels: dict[str, dict] = {}
    if not path.exists():
        return labels
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            labels[entry["cell_key"]] = entry
        except (json.JSONDecodeError, KeyError):
            continue
    return labels


def _save_labels(path: Path, labels: dict[str, dict]) -> None:
    with open(path, "w") as f:
        for entry in labels.values():
            f.write(json.dumps(entry) + "\n")


def _load_failures(results_path: Path) -> list[dict]:
    failures = []
    for line in results_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        v = row.get("verification") or {}
        if v.get("outcome") != "pass":
            failures.append(row)
    return failures


def _display_category_menu() -> None:
    table = Table(title="Failure Categories", show_header=True)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Category", style="bold")
    table.add_column("Description")
    for i, cat in enumerate(CATEGORIES, 1):
        table.add_row(str(i), cat, DESCRIPTIONS.get(cat, ""))
    console.print(table)


def _display_failure(row: dict, existing_label: dict | None) -> None:
    v = row.get("verification") or {}
    p = row.get("provider") or {}

    header = (
        f"[bold]{row['obligation_id']}[/bold] | "
        f"{row['model']} | {row['condition']} | sample={row['sample_idx']}"
    )
    console.rule(header)

    if existing_label:
        console.print(
            f"[yellow]Existing label:[/yellow] {existing_label.get('category', '?')} "
            f"— {existing_label.get('note', '')}"
        )
        console.print()

    console.print(Panel(
        Text(row.get("obligation_id", ""), style="bold"),
        title="Obligation",
    ))

    proof_text = p.get("text", "(no response)")
    console.print(Panel(proof_text, title="Model Output", border_style="green"))

    outcome = v.get("outcome", "unknown")
    lean_out = v.get("raw_stdout", "") + v.get("raw_stderr", "")
    lean_out = lean_out.strip()
    if not lean_out:
        lean_out = "(no output)"
    if len(lean_out) > 1500:
        lean_out = lean_out[:1500] + "\n... (truncated)"

    console.print(Panel(
        f"[bold red]Outcome: {outcome}[/bold red]\n\n{lean_out}",
        title="Lean Error",
        border_style="red",
    ))


def _prompt_category() -> tuple[str, str]:
    _display_category_menu()
    console.print()

    while True:
        choice = console.input("[bold cyan]Category (number, name, or 's' to skip):[/bold cyan] ").strip()
        if choice.lower() == "s":
            return "", ""
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                cat = CATEGORIES[idx]
                break
            console.print(f"[red]Invalid number. Choose 1-{len(CATEGORIES)}.[/red]")
        elif choice in CATEGORIES:
            cat = choice
            break
        else:
            console.print(f"[red]Unknown category. Enter a number or category name.[/red]")

    note = console.input("[dim]Optional note (Enter to skip):[/dim] ").strip()
    return cat, note


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive failure review")
    parser.add_argument("--results", type=Path, required=True, help="Input JSONL from runner")
    parser.add_argument("--output", type=Path, default=Path("failure_labels.jsonl"))
    parser.add_argument("--relabel", action="store_true", help="Revisit already-labeled cases")
    args = parser.parse_args()

    if not args.results.exists():
        console.print(f"[red]Results file not found: {args.results}[/red]")
        sys.exit(1)

    failures = _load_failures(args.results)
    if not failures:
        console.print("[green]No failures to review.[/green]")
        return

    labels = _load_labels(args.output)

    to_review = []
    for row in failures:
        key = _cell_key(row)
        if key in labels and not args.relabel:
            continue
        to_review.append((key, row))

    if not to_review:
        console.print(f"[green]All {len(failures)} failures already labeled. Use --relabel to revisit.[/green]")
        return

    console.print(f"\n[bold]{len(to_review)} failures to review[/bold] ({len(failures)} total failures)\n")

    for i, (key, row) in enumerate(to_review, 1):
        console.print(f"\n[dim]({i}/{len(to_review)})[/dim]")
        existing = labels.get(key)
        _display_failure(row, existing)

        cat, note = _prompt_category()
        if not cat:
            console.print("[dim]Skipped.[/dim]")
            continue

        labels[key] = {
            "cell_key": key,
            "obligation_id": row["obligation_id"],
            "model": row["model"],
            "condition": row["condition"],
            "sample_idx": row["sample_idx"],
            "outcome": (row.get("verification") or {}).get("outcome", "unknown"),
            "category": cat,
            "note": note,
        }
        _save_labels(args.output, labels)
        console.print(f"[green]Labeled: {cat}[/green]")

    console.print(f"\n[bold green]Done.[/bold green] Labels saved to {args.output}")
    console.print(f"Labeled: {sum(1 for v in labels.values() if v.get('category'))}/{len(failures)} failures")


if __name__ == "__main__":
    main()
