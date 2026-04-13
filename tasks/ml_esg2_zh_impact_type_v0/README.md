# ml_esg2_zh_impact_type_v0

Chinese single-label ESG impact type classification task over `ml_esg2_zh_official_v0`.

## Formal task id
`TA_MLCLS_ML_ESG2_ZH_v0`

## Input
- `text`
- canonical input text is the released headline only

## Output
Return ONLY a JSON object with exactly one key:
- `impact_type`

The value must be exactly one official impact type label.

Allowed label inventory:
`CannotDistinguish, NotRelatedtoCompany, NotRelatedtoESGTopic, Opportunity, Risk`

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
- 1 point for valid JSON with an accepted impact type label
- 1 point for exact-label correctness

This module is headline-only and task-specific. The evaluator remains the source of truth.
