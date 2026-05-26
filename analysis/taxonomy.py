"""Failure category taxonomy for manual review."""

CATEGORIES = [
    "hallucinated_tactic",
    "hallucinated_lemma",
    "wrong_strategy",
    "correct_strategy_wrong_lemma",
    "type_mismatch",
    "unsolved_subgoal",
    "incomplete",
    "other",
]

DESCRIPTIONS = {
    "hallucinated_tactic": "Model used a tactic that does not exist in Lean 4 / Mathlib",
    "hallucinated_lemma": "Model referenced a lemma or theorem that does not exist",
    "wrong_strategy": "Proof approach is fundamentally wrong for this goal",
    "correct_strategy_wrong_lemma": "Right idea but applied the wrong lemma or wrong arguments",
    "type_mismatch": "Terms have incompatible types",
    "unsolved_subgoal": "Proof leaves subgoals open",
    "incomplete": "Proof is cut off or clearly unfinished",
    "other": "Does not fit any category above",
}
