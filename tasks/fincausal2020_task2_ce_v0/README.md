# FinCausal 2020 Task 2 (Cause/Effect Extraction) (v0)

Task module for cause/effect extraction on causal sections.

## Task ID

`TA_CAUSE_EFFECT_FINCAUSAL2020_v0`

## Output schema (strict)

Return ONLY:

    {"cause": "...", "effect": "..."}

Rules:
- Exactly two keys: `cause`, `effect`
- Both values must be strings
- Use substrings from the passage text
- No extra keys
- No extra text

## Evaluation

The cached evaluator delegates to the official Task 2 scoring script semantics.
