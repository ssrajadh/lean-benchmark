"""Corpus loading and validation for Lean obligations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from rich.console import Console

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"

Difficulty = Literal["easy", "medium", "hard"]


class Obligation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    difficulty: Difficulty
    tags: list[str]
    description: str
    imports: list[str]
    open_namespaces: list[str] = Field(default_factory=list)
    preamble: str = ""
    statement: str
    expected_name: str
    notes: str = ""

    @field_validator("id")
    @classmethod
    def _id_kebab(cls, v: str) -> str:
        if not v or any(c.isspace() for c in v):
            raise ValueError("id must be non-empty and contain no whitespace")
        if v != v.lower():
            raise ValueError("id must be lowercase kebab-case")
        return v

    @field_validator("statement")
    @classmethod
    def _no_proof_body(cls, v: str) -> str:
        stripped = v.rstrip()
        if stripped.endswith(":=") or ":= by" in stripped or ":=by" in stripped:
            raise ValueError("statement must not include the proof body (`:=` ...)")
        return v


def load_obligation(path: Path) -> Obligation:
    data = json.loads(path.read_text())
    obligation = Obligation.model_validate(data)
    if obligation.id != path.stem:
        raise ValueError(
            f"id {obligation.id!r} does not match filename stem {path.stem!r}"
        )
    return obligation


def load_corpus(corpus_dir: Path = CORPUS_DIR) -> list[Obligation]:
    obligations: list[Obligation] = []
    for path in sorted(corpus_dir.glob("*.json")):
        obligations.append(load_obligation(path))
    return obligations


def _validate_cli(corpus_dir: Path = CORPUS_DIR) -> int:
    console = Console()
    paths = sorted(corpus_dir.glob("*.json"))
    if not paths:
        console.print(f"[yellow]No obligations found in {corpus_dir}[/yellow]")
        return 0

    errors = 0
    for path in paths:
        try:
            load_obligation(path)
        except ValidationError as e:
            errors += 1
            console.print(f"[red]✗ {path.name}[/red]")
            for err in e.errors():
                loc = ".".join(str(p) for p in err["loc"])
                console.print(f"    {loc}: {err['msg']}")
        except (ValueError, json.JSONDecodeError) as e:
            errors += 1
            console.print(f"[red]✗ {path.name}[/red]: {e}")
        else:
            console.print(f"[green]✓ {path.name}[/green]")

    total = len(paths)
    if errors:
        console.print(f"\n[red]{errors}/{total} failed validation[/red]")
        return 1
    console.print(f"\n[green]All {total} obligations valid[/green]")
    return 0


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] != "validate":
        print("usage: python -m harness.corpus validate", file=sys.stderr)
        sys.exit(2)
    sys.exit(_validate_cli())


if __name__ == "__main__":
    main()
