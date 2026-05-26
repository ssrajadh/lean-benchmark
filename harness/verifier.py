"""Lean 4 proof verification via subprocess."""

from __future__ import annotations

import hashlib
import re
import subprocess
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from harness.corpus import Obligation

Outcome = Literal[
    "pass",
    "compile_error",
    "unsolved_goals",
    "timeout",
    "unknown_identifier",
    "type_mismatch",
    "contains_sorry",
    "other_failure",
]


class VerificationResult(BaseModel):
    outcome: Outcome
    raw_stderr: str
    raw_stdout: str
    duration_ms: int
    lean_file_path: str


def _classify_outcome(stdout: str, stderr: str, returncode: int) -> Outcome:
    combined = stdout + stderr
    if re.search(r"declaration uses .sorry.", combined):
        return "contains_sorry"
    if returncode == 0 and "error" not in combined.lower():
        return "pass"

    if re.search(r"unsolved goals", combined):
        return "unsolved_goals"
    if re.search(r"unknown identifier", combined):
        return "unknown_identifier"
    if re.search(r"type mismatch", combined):
        return "type_mismatch"
    if re.search(r"(unknown command|expected|unexpected token|expected token)", combined):
        return "compile_error"

    return "other_failure"


def _build_lean_source(ob: Obligation, candidate_proof: str) -> str:
    lines: list[str] = []
    for imp in ob.imports:
        lines.append(f"import {imp}")
    lines.append("")

    for ns in ob.open_namespaces:
        lines.append(f"open {ns}")
    if ob.open_namespaces:
        lines.append("")

    lines.append(f"namespace BenchmarkVerify.{ob.id.replace('-', '_')}")
    lines.append("")

    if ob.preamble.strip():
        lines.append(ob.preamble)
        lines.append("")

    lines.append(f"{ob.statement} := by")
    for proof_line in candidate_proof.splitlines():
        lines.append(f"  {proof_line}")
    lines.append("")
    lines.append(f"end BenchmarkVerify.{ob.id.replace('-', '_')}")
    lines.append("")

    return "\n".join(lines)


def verify(
    obligation: Obligation,
    candidate_proof: str,
    lean_project_root: Path,
    timeout: int = 60,
) -> VerificationResult:
    lean_project_root = lean_project_root.resolve()
    short_hash = hashlib.sha256(candidate_proof.encode()).hexdigest()[:8]
    filename = f"{obligation.id}_{short_hash}.lean"
    verify_dir = lean_project_root / "BenchmarkVerify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    lean_file = verify_dir / filename

    source = _build_lean_source(obligation, candidate_proof)
    lean_file.write_text(source)

    t0 = time.monotonic()
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(lean_file.relative_to(lean_project_root))],
            cwd=str(lean_project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        outcome = _classify_outcome(result.stdout, result.stderr, result.returncode)
        return VerificationResult(
            outcome=outcome,
            raw_stderr=result.stderr,
            raw_stdout=result.stdout,
            duration_ms=duration_ms,
            lean_file_path=str(lean_file),
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - t0) * 1000)
        return VerificationResult(
            outcome="timeout",
            raw_stderr="",
            raw_stdout="",
            duration_ms=duration_ms,
            lean_file_path=str(lean_file),
        )
