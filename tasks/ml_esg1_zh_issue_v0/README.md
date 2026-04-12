# ml_esg1_zh_issue_v0

Chinese multi-label ESG issue classification task over `ml_esg1_zh_official_v0`.

## Formal task id
`TA_MLCLS_ML_ESG1_ZH_v0`

## Input
- `text`
- canonical input text is the released headline only

## Output
Return ONLY a JSON object with exactly one key:
- `esg_categories`

The value must be an array of zero or more released ESG code labels, deduplicated and sorted after normalization.

Allowed code inventory:
`E00, E01, E02, E03, E04, E05, E06, E07, E08, E09, E10, E11, E12, E13, G00, G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, NN, S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20`

## Evaluation
The evaluator reports:
- micro F1
- macro F1
- example F1 mean
- subset accuracy
- format-valid rate
- average predicted label count
- average gold label count

## Reward stance
This task uses a structured multilabel reward:
- 1 point for valid JSON with an accepted label set
- partial correctness credit via instance-level set F1
- exact-set matches receive full correctness credit

This module is headline-only and task-specific. The evaluator remains the source of truth.
