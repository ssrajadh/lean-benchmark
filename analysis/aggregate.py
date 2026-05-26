"""Aggregate benchmark results into summary tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "output"


def load_results(results_dir: Path) -> pd.DataFrame:
    rows = []
    for p in sorted(results_dir.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            v = row.get("verification") or {}
            prov = row.get("provider") or {}
            rows.append({
                "obligation_id": row.get("obligation_id", ""),
                "model": row.get("model", ""),
                "condition": row.get("condition", ""),
                "sample_idx": row.get("sample_idx", 0),
                "outcome": v.get("outcome", "error"),
                "passed": v.get("outcome") == "pass",
                "latency_ms": prov.get("latency_ms", 0),
                "input_tokens": prov.get("input_tokens", 0),
                "output_tokens": prov.get("output_tokens", 0),
                "lean_duration_ms": v.get("duration_ms", 0),
                "error": row.get("error") or prov.get("error"),
            })
    if not rows:
        print("No results found.", file=sys.stderr)
        sys.exit(1)
    return pd.DataFrame(rows)


def pass_rate_by_model_condition(df: pd.DataFrame) -> pd.DataFrame:
    tbl = df.groupby(["model", "condition"]).agg(
        total=("passed", "count"),
        passed=("passed", "sum"),
    )
    tbl["pass_rate"] = (tbl["passed"] / tbl["total"]).round(3)
    return tbl.reset_index()


def pass_rate_per_obligation(df: pd.DataFrame) -> pd.DataFrame:
    tbl = df.groupby(["obligation_id", "model", "condition"]).agg(
        total=("passed", "count"),
        passed=("passed", "sum"),
    )
    tbl["pass_rate"] = (tbl["passed"] / tbl["total"]).round(3)
    pivot = tbl["pass_rate"].unstack(["model", "condition"]).fillna(0.0)
    pivot.columns = [f"{m} / {c}" for m, c in pivot.columns]
    return pivot.reset_index()


def failure_distribution(df: pd.DataFrame) -> pd.DataFrame:
    fails = df[~df["passed"]].copy()
    if fails.empty:
        return pd.DataFrame(columns=["model", "condition", "outcome", "count"])
    tbl = fails.groupby(["model", "condition", "outcome"]).size().reset_index(name="count")
    tbl = tbl.sort_values(["model", "condition", "count"], ascending=[True, True, False])
    return tbl


def retrieval_addressable(df: pd.DataFrame) -> pd.DataFrame:
    rates = df.groupby(["obligation_id", "condition"])["passed"].mean().unstack("condition")
    if "baseline" not in rates.columns or "oracle" not in rates.columns:
        return pd.DataFrame(columns=["obligation_id", "baseline_rate", "oracle_rate", "retrieval_addressable"])
    out = pd.DataFrame({
        "obligation_id": rates.index,
        "baseline_rate": rates["baseline"].round(3).values,
        "oracle_rate": rates["oracle"].round(3).values,
    })
    out["retrieval_addressable"] = out["oracle_rate"] > out["baseline_rate"]
    return out


def summary_statistics(df: pd.DataFrame) -> dict:
    by_model = df.groupby("model")["passed"].mean()
    by_cond = df.groupby("condition")["passed"].mean()
    by_item = df.groupby("obligation_id")["passed"].mean()
    distinct_failures = df[~df["passed"]]["outcome"].nunique()

    return {
        "overall_pass_rate": round(df["passed"].mean(), 3),
        "pass_rate_variance_across_models": round(by_model.var(), 4) if len(by_model) > 1 else 0.0,
        "pass_rate_variance_across_conditions": round(by_cond.var(), 4) if len(by_cond) > 1 else 0.0,
        "pass_rate_variance_across_items": round(by_item.var(), 4) if len(by_item) > 1 else 0.0,
        "distinct_failure_categories": int(distinct_failures),
        "total_cells": len(df),
        "total_passed": int(df["passed"].sum()),
        "total_failed": int((~df["passed"]).sum()),
    }


def _write(df: pd.DataFrame, name: str, out_dir: Path) -> None:
    df.to_csv(out_dir / f"{name}.csv", index=False)
    md = df.to_markdown(index=False)
    (out_dir / f"{name}.md").write_text(md + "\n")
    print(f"\n## {name}\n")
    print(md)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_results(args.results_dir)

    print(f"Loaded {len(df)} result rows")
    print(f"Models: {sorted(df['model'].unique())}")
    print(f"Conditions: {sorted(df['condition'].unique())}")
    print(f"Obligations: {sorted(df['obligation_id'].unique())}")

    _write(pass_rate_by_model_condition(df), "pass_rate_by_model_condition", args.output_dir)
    _write(pass_rate_per_obligation(df), "pass_rate_per_obligation", args.output_dir)
    _write(failure_distribution(df), "failure_distribution", args.output_dir)

    if "oracle" in df["condition"].values and "baseline" in df["condition"].values:
        _write(retrieval_addressable(df), "retrieval_addressable", args.output_dir)
    else:
        print("\n## retrieval_addressable\n\nSkipped (need both baseline and oracle conditions)")

    stats = summary_statistics(df)
    stats_df = pd.DataFrame([stats])
    _write(stats_df, "summary_statistics", args.output_dir)


if __name__ == "__main__":
    main()
