# A Benchmark for Frontier LLMs on Program-Verification Proof Obligations in Lean (CSE 290Q Final Project)

## What's here

| Path | Contents |
| --- | --- |
| `corpus/` | The 30 obligations, one JSON file each (validated by a Pydantic schema). |
| `harness/` | Runner, verifier, prompt builder, and provider clients (OpenAI / NVIDIA NIM / Fireworks). |
| `analysis/` | Aggregation (`aggregate.py`), failure taxonomy, and the oracle/provenance audit report. |
| `results/` | `run_clean_20260601.jsonl` — the run the paper reports (one row per cell). |

## Reproducing the results

### 1. Lean toolchain + Mathlib

Install [`elan`](https://github.com/leanprover/elan) and create a Lean project at
`lean_project/` pinned to the same toolchain the paper used. The `lean_project/`
directory is not committed (it carries a multi-GB Mathlib build); recreate it with:

```
lean_project/lean-toolchain   ->  leanprover/lean4:v4.28.0
```

and a `lean_project/lakefile.toml` that requires Mathlib at the matching tag:

```toml
name = "lean_project"
defaultTargets = ["LeanProject"]

[[require]]
name = "mathlib"
scope = "leanprover-community"
rev = "v4.28.0"

[[lean_lib]]
name = "LeanProject"
```

Then fetch the prebuilt Mathlib cache and build:

```bash
cd lean_project
lake exe cache get
lake build
cd ..
```

The harness writes each candidate proof into `lean_project/BenchmarkVerify/` and
compiles it from that directory; the folder is created automatically.

### 2. Python environment

Uses [`uv`](https://github.com/astral-sh/uv) (Python ≥ 3.11):

```bash
uv sync
```

### 3. API keys

```bash
cp .env.example .env
# fill in OPENAI_API_KEY, NVIDIA_API_KEY, FIREWORKS_API_KEY
```

### 4. Run the benchmark

```bash
uv run python -m harness.runner \
  --models gpt-5.4-mini qwen/qwen3.5-397b-a17b accounts/fireworks/models/deepseek-v4-pro \
  --conditions baseline oracle \
  --samples 3
```

This evaluates 30 obligations × 3 models × 2 conditions × 3 samples = 540 cells and
writes `results/run_<timestamp>.jsonl`. The run is **resumable** (existing cell keys
are skipped) and provider responses are cached on disk, so it can be stopped and
restarted freely. Provider is chosen from the model identifier prefix
(`gpt-*` → OpenAI, `qwen/*` → NVIDIA NIM, `accounts/fireworks/*` → Fireworks).

### 5. Aggregate

```bash
uv run python -m analysis.aggregate --results-dir results
```

This prints the per-model pass rates, the failure-category distribution, the
item-vs-model variance decomposition, and the oracle delta, and writes CSV/Markdown
tables to `analysis/output/`. Pointing it at the bundled
`results/run_clean_20260601.jsonl` reproduces the tables in the paper.
