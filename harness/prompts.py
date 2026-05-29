"""Prompt construction for proof generation."""

from __future__ import annotations

from harness.corpus import Obligation

_SYSTEM = (
    "You are a Lean 4 proof assistant. Given a theorem statement and its context, "
    "produce a tactic proof that closes the goal. Return only the proof body "
    "(the tactics after `:= by`) inside a single fenced code block. "
    "Do not include the theorem signature, imports, or any commentary."
)


def _format_context(ob: Obligation) -> str:
    parts: list[str] = []

    imports_block = "\n".join(f"import {i}" for i in ob.imports)
    parts.append(f"Imports:\n```lean\n{imports_block}\n```")

    if ob.open_namespaces:
        opens = "\n".join(f"open {ns}" for ns in ob.open_namespaces)
        parts.append(f"Open namespaces:\n```lean\n{opens}\n```")

    if ob.preamble.strip():
        parts.append(f"Preamble definitions:\n```lean\n{ob.preamble}\n```")

    parts.append(f"Theorem to prove:\n```lean\n{ob.statement} := by\n  sorry\n```")

    return "\n\n".join(parts)


def baseline_prompt(ob: Obligation) -> tuple[str, str]:
    user = (
        f"{_format_context(ob)}\n\n"
        "Replace `sorry` with a valid tactic proof. "
        "Respond with only the proof body in a fenced code block."
    )
    return _SYSTEM, user


def oracle_prompt(ob: Obligation) -> tuple[str, str]:
    user = f"{_format_context(ob)}\n\n"

    if ob.oracle_premises:
        lemmas = "\n".join(f"- `{p}`" for p in ob.oracle_premises)
        user += f"Relevant lemmas:\n{lemmas}\n\n"

    user += (
        "Replace `sorry` with a valid tactic proof. "
        "Respond with only the proof body in a fenced code block."
    )
    return _SYSTEM, user
