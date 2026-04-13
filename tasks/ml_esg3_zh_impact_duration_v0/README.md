# ml_esg3_zh_impact_duration_v0

Chinese single-label ESG impact duration classification task over `ml_esg3_zh_official_v0`.

## Formal task id
`TA_MLCLS_ML_ESG3_ZH_v0`

## Input
- `text`
- canonical input text is the released headline only

## Output
Return ONLY a JSON object with exactly one key:
- `impact_duration`

The value must be exactly one official impact duration label.

Allowed label inventory:
`<2, 2~5, >5, NotRelatedtoCompany, NotRelatedtoESGTopic`

## Evaluation
The evaluator reports:
- accuracy
- macro F1
- weighted F1
- format-valid rate
- per-class precision / recall / F1
- confusion counts

## Reward stance
This task uses a structured single-label reward:
- 1 point for valid JSON with an accepted impact duration label
- 1 point for exact-label correctness

This module is headline-only and task-specific. The evaluator remains the source of truth.
