# calm_ccf_risk_v0

CALM-family task module over `calm_ccf_public_v0`.

## Formal task id
`RM_FRAUD_CCF_CALM_v0`

## Task definition
- binary closed-label risk-management classification
- canonical public benchmark release surface: `Salesforce/FinEval` subset `CRA-CCF`
- CALM role metadata: `train_eval`
- allowed labels: `no` / `yes`

## Evaluation
- default evaluator reports `macro_f1`, `mcc`, `accuracy`, `format_valid_rate`, and `completion_coverage`
- diagnostics include class counts, confusion matrix, and per-class precision/recall/F1
- reward helper is the shared CALM closed-label parser/reward with weights `0.2 / 0.2 / 0.6`
