#!/usr/bin/env python3
"""
Check whether each oracle/extracted premise literally appears in the
ground-truth proof for every obligation in corpus/.

Ground truth proof = contents of proofs_explained/<id>.lean (the corpus
JSONs themselves do not carry a ground_truth_proof field).

For each premise, we report:
  - full_match:      the full dotted name appears with word-boundary
  - shortname_match: only the final dotted component appears
  - verdict:         present | absent | shortname_only

Word-boundary handling: dotted identifiers like ``Nat.add_succ`` are
matched with custom boundaries that treat ``.`` and ``\\w`` as identifier
characters, so ``Foo.Nat.add_succ`` or ``Nat.add_succ_lt`` will not be
mistaken for ``Nat.add_succ``.

This script is read-only: it never modifies any file.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(ROOT, "corpus")
PROOFS_DIR = os.path.join(ROOT, "proofs_explained")


# An "identifier character" for Lean-ish dotted names: word chars or '.'.
# A match must be preceded and followed by something that is *not* such a
# character (or by start/end of string).
_LEFT_BOUNDARY = r"(?<![\w.])"
_RIGHT_BOUNDARY_FULL = r"(?![\w])"   # trailing '.' is OK (projection / field access)
_RIGHT_BOUNDARY_SHORT = r"(?![\w.])" # short name must not be followed by another dotted part


def find_full(premise: str, text: str) -> bool:
    pat = _LEFT_BOUNDARY + re.escape(premise) + _RIGHT_BOUNDARY_FULL
    return re.search(pat, text) is not None


def find_shortname(short: str, text: str) -> bool:
    pat = _LEFT_BOUNDARY + re.escape(short) + _RIGHT_BOUNDARY_SHORT
    return re.search(pat, text) is not None


def short_of(premise: str) -> str:
    return premise.rsplit(".", 1)[-1]


@dataclass
class Row:
    premise: str
    full: bool
    short: bool

    @property
    def verdict(self) -> str:
        if self.full:
            return "present"
        if self.short:
            return "shortname_only"
        return "absent"


@dataclass
class ObligationReport:
    oid: str
    source: str  # "oracle_premises" | "extracted_premises" | "none"
    proof_path: str | None
    rows: list[Row]
    missing_proof: bool = False
    empty_premises: bool = False


def load_premises(oid: str) -> tuple[list[str], str]:
    """Prefer oracle_premises from the main JSON; fall back to extracted_premises
    from the oracle_draft. Returns (premises, source_label)."""
    main = os.path.join(CORPUS_DIR, f"{oid}.json")
    draft = os.path.join(CORPUS_DIR, f"{oid}.oracle_draft.json")

    if os.path.exists(main):
        with open(main) as f:
            d = json.load(f)
        op = d.get("oracle_premises") or []
        if op:
            return list(op), "oracle_premises"

    if os.path.exists(draft):
        with open(draft) as f:
            d = json.load(f)
        ep = d.get("extracted_premises") or []
        if ep:
            return list(ep), "extracted_premises"

    return [], "none"


def all_obligation_ids() -> list[str]:
    ids = set()
    for path in glob.glob(os.path.join(CORPUS_DIR, "*.json")):
        name = os.path.basename(path)
        if name.endswith(".oracle_draft.json"):
            ids.add(name[: -len(".oracle_draft.json")])
        else:
            ids.add(name[: -len(".json")])
    return sorted(ids)


def analyze(oid: str) -> ObligationReport:
    premises, source = load_premises(oid)
    proof_path = os.path.join(PROOFS_DIR, f"{oid}.lean")

    if not os.path.exists(proof_path):
        return ObligationReport(
            oid=oid, source=source, proof_path=None, rows=[],
            missing_proof=True, empty_premises=(not premises),
        )

    with open(proof_path) as f:
        text = f.read()

    rows: list[Row] = []
    for p in premises:
        full_ok = find_full(p, text)
        short = short_of(p)
        # Only meaningful if the short name differs from the full name.
        short_ok = find_shortname(short, text) if short != p else full_ok
        rows.append(Row(premise=p, full=full_ok, short=short_ok))

    return ObligationReport(
        oid=oid, source=source, proof_path=proof_path, rows=rows,
        empty_premises=(not premises),
    )


def render_table(rep: ObligationReport) -> str:
    header_premise = "premise"
    header_full = "full_match"
    header_short = "shortname_match"
    header_verdict = "verdict"

    col_p = max(len(header_premise), max((len(r.premise) for r in rep.rows), default=0))
    col_f = len(header_full)
    col_s = len(header_short)
    col_v = max(len(header_verdict), len("shortname_only"))

    def fmt_row(p: str, f: str, s: str, v: str) -> str:
        return f"  {p:<{col_p}}  {f:<{col_f}}  {s:<{col_s}}  {v:<{col_v}}"

    lines: list[str] = []
    src = rep.source if rep.source != "none" else "(no premises listed)"
    lines.append(f"=== {rep.oid}  [source: {src}]")
    if rep.missing_proof:
        lines.append(f"  (no proof file at proofs_explained/{rep.oid}.lean — skipped)")
        return "\n".join(lines)
    if rep.empty_premises:
        lines.append("  (no premises to check)")
        return "\n".join(lines)

    lines.append(fmt_row(header_premise, header_full, header_short, header_verdict))
    lines.append("  " + "-" * (col_p + col_f + col_s + col_v + 6))
    for r in rep.rows:
        lines.append(
            fmt_row(
                r.premise,
                "yes" if r.full else "no",
                "yes" if r.short else "no",
                r.verdict,
            )
        )
    return "\n".join(lines)


def main() -> int:
    ids = all_obligation_ids()
    reports = [analyze(oid) for oid in ids]

    for rep in reports:
        print(render_table(rep))
        print()

    # Flagged items for manual review.
    flagged: list[tuple[str, str, str]] = []  # (oid, premise, verdict)
    for rep in reports:
        if rep.missing_proof or rep.empty_premises:
            continue
        for r in rep.rows:
            if r.verdict in ("absent", "shortname_only"):
                flagged.append((rep.oid, r.premise, r.verdict))

    print("=" * 72)
    print("FLAGGED FOR MANUAL REVIEW")
    print("=" * 72)
    if not flagged:
        print("  (none — every listed premise appears verbatim in its proof)")
    else:
        col_oid = max(len("obligation"), max(len(o) for o, _, _ in flagged))
        col_pr = max(len("premise"), max(len(p) for _, p, _ in flagged))
        col_v = max(len("verdict"), len("shortname_only"))
        print(f"  {'obligation':<{col_oid}}  {'premise':<{col_pr}}  {'verdict':<{col_v}}")
        print("  " + "-" * (col_oid + col_pr + col_v + 4))
        for oid, p, v in flagged:
            print(f"  {oid:<{col_oid}}  {p:<{col_pr}}  {v:<{col_v}}")

    # Summary stats.
    total = sum(len(r.rows) for r in reports if not r.missing_proof)
    present = sum(1 for r in reports for row in r.rows if not r.missing_proof and row.verdict == "present")
    shortonly = sum(1 for r in reports for row in r.rows if not r.missing_proof and row.verdict == "shortname_only")
    absent = sum(1 for r in reports for row in r.rows if not r.missing_proof and row.verdict == "absent")
    missing_proofs = [r.oid for r in reports if r.missing_proof]
    empty = [r.oid for r in reports if r.empty_premises and not r.missing_proof]

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  obligations scanned:        {len(reports)}")
    print(f"  obligations w/ no premises: {len(empty)}")
    if empty:
        print(f"    {', '.join(empty)}")
    print(f"  obligations w/ no proof:    {len(missing_proofs)}")
    if missing_proofs:
        print(f"    {', '.join(missing_proofs)}")
    print(f"  total premises checked:     {total}")
    print(f"    present:                  {present}")
    print(f"    shortname_only:           {shortonly}")
    print(f"    absent:                   {absent}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
