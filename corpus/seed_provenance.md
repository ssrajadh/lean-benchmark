# Seed Corpus Provenance

## Candidates

| ID | Source Repo | File Path | Lines | Summary |
|---|---|---|---|---|
| `fpil_helper_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 475-480 | If n ≤ m then n ≤ m + 1 (induction on Nat.le) |
| `fpil_bounds_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 887-893 | Array index step: i < a implies a - (i+1) < a - i |
| `fpil_bounds_02` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 830-836 | Subtraction is bounded: n - k ≤ n |
| `fpil_termination_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 563-567 | splitList produces halves no longer than the input (termination obligation for mergeSort) |
| `love_helper_01` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 316-322 | Mapping identity over a list returns the list unchanged |
| `love_helper_02` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 440-445 | Mirroring a binary tree twice yields the original tree |
| `love_spec_01` | logical_verification_2025 | `lean/LoVe/LoVe09_OperationalSemantics_Demo.lean` | 333-343 | Big-step inversion: skip leaves state unchanged (iff) |
| `love_spec_02` | logical_verification_2025 | `lean/LoVe/LoVe09_OperationalSemantics_Demo.lean` | 344-353 | Big-step inversion: assignment updates exactly the target variable (iff) |

## Category Distribution

- **helper_lemma** (3): fpil_helper_01, love_helper_01, love_helper_02
- **bounds** (2): fpil_bounds_01, fpil_bounds_02
- **termination** (1): fpil_termination_01
- **specification_equivalence** (2): love_spec_01, love_spec_02

## Notes

- The LoVe operational semantics obligations (love_spec_01, love_spec_02) require substantial preamble: State type, State.update, Stmt inductive, BigStep inductive, and associated notation. All preamble is copied verbatim from `LoVelib.lean` (lines 325-332) and `LoVe09_OperationalSemantics_Demo.lean` (lines 134-141, 239-260).

- The LoVe functional programming helpers (love_helper_01, love_helper_02) use custom `map` and `mirror` definitions rather than Mathlib's built-ins, since the source file defines these locally. The `Tree` type is from LoVelib but is identical to Lean's standard `Tree α`.

- `fpil_termination_01` uses `fun_induction` in its ground-truth proof, which is a relatively new tactic. Models may find alternative proofs via structural induction.

- The fp-lean source file (Inequalities.lean) contains many `discarding`/`stop discarding` blocks showing intermediate proof states for pedagogical purposes. Only the final complete proofs (without `skip` or `sorry`) were extracted.

- No interlude obligations were included from fp-lean because the interludes in this edition primarily discuss concepts rather than proving standalone theorems that fit our criteria.
