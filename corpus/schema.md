# Obligation Schema

One JSON file per obligation under `corpus/*.json`. Each obligation describes a single Lean theorem the model must prove.

## Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique identifier, kebab-case. Used as the filename stem and as the Lean module name suffix (e.g. `nat-add-zero` → `BenchmarkVerify.NatAddZero`). |
| `source` | string | yes | Where the obligation came from (textbook, problem set, hand-written, etc.). Free-form. |
| `difficulty` | string | yes | One of `"easy"`, `"medium"`, `"hard"`. Author's subjective estimate. |
| `tags` | string[] | yes | Topic tags, e.g. `["nat", "arithmetic"]`. May be empty. |
| `description` | string | yes | Natural-language description shown to the model in the prompt. Should be self-contained. |
| `imports` | string[] | yes | Lean `import` lines required, without the `import` keyword (e.g. `"Mathlib"`, `"Mathlib.Data.Nat.Basic"`). |
| `open_namespaces` | string[] | no | Namespaces to `open` before the theorem. Defaults to `[]`. |
| `preamble` | string | no | Arbitrary Lean code inserted after imports/opens and before the theorem (defs, `variable` declarations, helper lemmas). Defaults to `""`. |
| `statement` | string | yes | The full theorem signature including the name, binders, and goal type, ending right before `:=`. E.g. `theorem foo (a : Nat) : a + 0 = a`. The harness appends `:= by\n  <model output>`. |
| `oracle_premises` | string[] | no | Lemma names supplied as hints under the `oracle` prompt condition. Defaults to `[]`. |
| `notes` | string | no | Author notes; ignored by the harness. Defaults to `""`. |

## Conventions

- Filename must equal `<id>.json`.
- `statement` must not include `:= by sorry` or any proof body — the harness assembles the file as:
  ```
  <imports>
  <open_namespaces>
  <preamble>
  <statement> := by
    <model output>
  ```
- Use `Mathlib` as a single import unless you need to keep build times small for a particular obligation.
- All Lean code in JSON strings must be valid Lean 4 syntax. Escape backslashes and quotes as required by JSON.

## Example

`corpus/nat-add-zero.json`:

```json
{
  "id": "nat-add-zero",
  "source": "hand-written smoke test",
  "difficulty": "easy",
  "tags": ["nat", "arithmetic", "simp"],
  "description": "Prove that for any natural number a, a + 0 = a.",
  "imports": ["Mathlib"],
  "open_namespaces": [],
  "preamble": "",
  "statement": "theorem foo (a : Nat) : a + 0 = a",
  "notes": "Closeable by `simp` or `rfl`. Used as a toolchain smoke test."
}
```

Assembled Lean file the harness would produce (with a model proof of `simp`):

```lean
import Mathlib

theorem foo (a : Nat) : a + 0 = a := by
  simp
```
