# calm_travelinsurance_risk_v0

CALM-family task module over `calm_travelinsurance_public_v0`.

## Formal task id
`RM_CLAIM_TRAVELINSURANCE_CALM_v0`

## Task definition
- binary closed-label risk-management classification
- canonical public benchmark release surface: `Salesforce/FinEval` subset `CRA-TravelInsurance`
- CALM role metadata: `train_eval`
- allowed labels: `yes` / `no`

## Evaluation
- default evaluator reports `macro_f1`, `mcc`, `accuracy`, `format_valid_rate`, and `completion_coverage`
- diagnostics include class counts, confusion matrix, and per-class precision/recall/F1
- reward helper is the shared CALM closed-label parser/reward with weights `0.2 / 0.2 / 0.6`
