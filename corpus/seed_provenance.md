# Seed Corpus Provenance

## Candidates (29 obligations from sources + 1 hand-written)

| ID | Source Repo | File Path | Lines | Summary |
|---|---|---|---|---|
| `and-swap` | hand-written | — | — | Conjunction is commutative (smoke test) |
| `fpil_helper_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 475-480 | If n ≤ m then n ≤ m + 1 (induction on Nat.le) |
| `fpil_bounds_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 887-893 | Array index step: i < a implies a - (i+1) < a - i |
| `fpil_bounds_02` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 830-836 | Subtraction is bounded: n - k ≤ n |
| `fpil_termination_01` | fp-lean | `examples/Examples/ProgramsProofs/Inequalities.lean` | 563-567 | splitList produces halves no longer than the input |
| `fpil_plusR_01` | fp-lean | `examples/Examples/Induction.lean` | 246-247 | k = Nat.plusR 0 k for right-recursive addition |
| `fpil_list_01` | fp-lean | `examples/Examples/Induction.lean` | 305-306 | List append is associative |
| `fpil_tree_01` | fp-lean | `examples/Examples/Induction.lean` | 492-494 | Mirroring a BinTree preserves node count |
| `fpil_tree_02` | fp-lean | `examples/Examples/Induction.lean` | 530-532 | Grafting onto a BinTree sums counts |
| `love_logic_01` | logical_verification_2025 | `lean/LoVe/LoVe03_BackwardProofs_Demo.lean` | 202-210 | Disjunction is commutative: a ∨ b → b ∨ a |
| `love_logic_02` | logical_verification_2025 | `lean/LoVe/LoVe03_BackwardProofs_Demo.lean` | 219-224 | Double negation introduction: a → ¬¬a |
| `love_logic_03` | logical_verification_2025 | `lean/LoVe/LoVe03_BackwardProofs_Demo.lean` | 212-217 | Modus ponens: (a → b) → a → b |
| `love_arith_01` | logical_verification_2025 | `lean/LoVe/LoVe03_BackwardProofs_Demo.lean` | 287-289 | a + b + c = c + b + a by AC |
| `love_quant_01` | logical_verification_2025 | `lean/LoVe/LoVe04_ForwardProofs_Demo.lean` | 143-157 | One-point rule: (∀x, x = t → P x) ↔ P t |
| `love_quant_02` | logical_verification_2025 | `lean/LoVe/LoVe04_ForwardProofs_Demo.lean` | 165-187 | One-point rule: (∃x, x = t ∧ P x) ↔ P t |
| `love_list_01` | logical_verification_2025 | `lean/LoVe/LoVe04_ForwardProofs_Demo.lean` | 394-398 | reverse distributes over append |
| `love_helper_01` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 316-322 | Mapping identity over a list returns the list unchanged |
| `love_helper_02` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 440-445 | Mirroring a binary tree twice yields the original tree |
| `love_induction_01` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 68-73 | Successor of n is never equal to n |
| `love_induction_02` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 323-329 | map g ∘ map f = map (g ∘ f) |
| `love_induction_03` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 292-297 | Injectivity of list cons |
| `love_tree_01` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 463-466 | mirror t = nil ↔ t = nil |
| `love_deptype_01` | logical_verification_2025 | `lean/LoVe/LoVe05_FunctionalProgramming_Demo.lean` | 487-491 | listOfVec preserves length |
| `love_pred_01` | logical_verification_2025 | `lean/LoVe/LoVe06_InductivePredicates_Demo.lean` | 338-357 | Even n ↔ n = 0 ∨ ∃m, n = m + 2 ∧ Even m |
| `love_pred_02` | logical_verification_2025 | `lean/LoVe/LoVe06_InductivePredicates_Demo.lean` | 421-426 | [17, 13] is not sorted |
| `love_pred_03` | logical_verification_2025 | `lean/LoVe/LoVe06_InductivePredicates_Demo.lean` | 454-463 | Reverse of a palindrome is a palindrome |
| `love_pred_04` | logical_verification_2025 | `lean/LoVe/LoVe06_InductivePredicates_Demo.lean` | 485-496 | Mirroring a full binary tree yields a full tree |
| `love_spec_01` | logical_verification_2025 | `lean/LoVe/LoVe09_OperationalSemantics_Demo.lean` | 333-343 | Big-step inversion: skip leaves state unchanged (iff) |
| `love_spec_02` | logical_verification_2025 | `lean/LoVe/LoVe09_OperationalSemantics_Demo.lean` | 344-353 | Big-step inversion: assignment updates exactly the target variable (iff) |
| `love_spec_03` | logical_verification_2025 | `lean/LoVe/LoVe09_OperationalSemantics_Demo.lean` | 399-425 | Big-step inversion: while loop unfolds one iteration or terminates (iff) |

## Category Distribution

- **logic** (4): and-swap, love_logic_01, love_logic_02, love_logic_03
- **arithmetic** (1): love_arith_01
- **quantifiers** (2): love_quant_01, love_quant_02
- **nat/inequality** (3): fpil_helper_01, fpil_bounds_01, fpil_bounds_02
- **list** (5): fpil_list_01, love_helper_01, love_induction_02, love_induction_03, love_list_01
- **tree** (5): fpil_tree_01, fpil_tree_02, love_helper_02, love_tree_01, love_pred_04
- **termination** (2): fpil_termination_01, fpil_plusR_01
- **inductive_predicates** (3): love_pred_01, love_pred_02, love_pred_03
- **dependent_types** (1): love_deptype_01
- **induction_basics** (1): love_induction_01
- **specification_equivalence** (3): love_spec_01, love_spec_02, love_spec_03

## Difficulty Distribution

- **easy** (15): and-swap, fpil_helper_01, fpil_bounds_02, fpil_plusR_01, fpil_list_01, love_logic_01, love_logic_02, love_logic_03, love_arith_01, love_induction_01, love_induction_03, love_helper_01, love_helper_02, love_tree_01, love_pred_02
- **medium** (12): fpil_bounds_01, fpil_termination_01, fpil_tree_01, fpil_tree_02, love_quant_01, love_quant_02, love_induction_02, love_list_01, love_deptype_01, love_pred_01, love_pred_04, love_spec_01, love_spec_02
- **hard** (2): love_pred_03, love_spec_03

## Notes

- The LoVe operational semantics obligations (love_spec_01, love_spec_02, love_spec_03) require substantial preamble: State type, State.update, Stmt inductive, BigStep inductive, and associated notation. All preamble is copied verbatim from `LoVelib.lean` (lines 325-332) and `LoVe09_OperationalSemantics_Demo.lean` (lines 134-141, 239-260).

- The LoVe functional programming helpers (love_helper_01, love_helper_02) use custom `map` and `mirror` definitions rather than Mathlib's built-ins, since the source file defines these locally. The `Tree` type is from LoVelib but is identical to Lean's standard `Tree α`.

- `fpil_termination_01` uses `fun_induction` in its ground-truth proof, which is a relatively new tactic. Models may find alternative proofs via structural induction.

- The fp-lean source file (Inequalities.lean) contains many `discarding`/`stop discarding` blocks showing intermediate proof states for pedagogical purposes. Only the final complete proofs (without `skip` or `sorry`) were extracted.

- `love_pred_01` requires a `LoveEven` namespace wrapper because Mathlib already defines `Even`. The harness should close this namespace after the proof.

- `fpil_tree_01` and `fpil_tree_02` use a custom `BinTree` type from fp-lean (different from Lean's `Tree α`). The definitions are included as preamble.

- `love_pred_03` (Palindrome_reverse) is rated hard because it requires discovering the `reverse_append` helper lemma and induction on the `Palindrome` predicate. The helper is provided in the preamble.

- All 30 obligations (29 from sources + 1 hand-written) have been verified to typecheck against Lean 4.28.0 + Mathlib v4.28.0.
