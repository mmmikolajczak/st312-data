# FinBen FOMC Stance Task (v0)

Task module for classifying monetary policy stance in FOMC-style text.

## Task ID
`TA_STANCE_FOMC_FINBEN_v0`

## Dataset module
- Dataset ID: `finben_fomc_v0`
- Train: `data/fomc/processed/finben_fomc_train.jsonl`
- Test: `data/fomc/processed/finben_fomc_test.jsonl`

## Labels
- `dovish`
- `hawkish`
- `neutral`

## Output schema
Return ONLY:
{"stance":"dovish" | "hawkish" | "neutral"}

No extra keys. No extra text.

## Scripts
- Reward parser: `scripts/tasks/finben_fomc_stance_v0/reward_fomc_stance.py`

Next scripts to add:
- prompt renderer
- request builder
- cached evaluator
