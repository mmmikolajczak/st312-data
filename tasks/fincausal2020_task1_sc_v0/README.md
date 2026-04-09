# FinCausal 2020 Task 1 (Sentence Classification) (v0)

Task module for binary causal classification on short financial-news sections.

## Task ID

`TA_CAUSAL_CLASSIFY_FINCAUSAL2020_v0`

## Output schema (strict)

Return ONLY:

    {"label": 0}

Rules:
- Exactly one key: `label`
- `label` must be integer `0` or `1`
- No extra keys
- No extra text

## Evaluation

The cached evaluator delegates to the official Task 1 scoring script semantics.
