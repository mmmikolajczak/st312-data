# german_credit_risk_v0

Canonical credit-risk classification task over `statlog_german_credit_uci_v0`.

## Formal task id
`RM_CREDIT_GERMAN_UCI_v0`

## Task definition
- canonical labels are lower-case `good` and `bad`
- source labels are `1 = good` and `2 = bad`
- canonical prompt surface preserves original UCI attribute ids while also rendering decoded feature names and decoded categorical values

## Evaluation variants
- `uci_cost_sensitive_default`: canonical UCI cost-sensitive evaluation with mean cost, total cost, normalized cost score, accuracy, and confusion counts
- `finben_optional_f1_mcc`: optional compatibility view with macro F1 and MCC

## Reward note
- reward utilities are training-oriented rather than benchmark-authoritative
- the dominant semantic term is dense and cost-aware: `1 - cost/5`, where the UCI cost matrix penalizes `actual bad -> predicted good` much more strongly than `actual good -> predicted bad`
- reward helpers are intended for local LoRA + GRPO experimentation, not as a replacement for the canonical evaluator

## Sensitive-feature note
- this historical benchmark includes demographic-style variables such as personal status and sex, age, and foreign-worker status
- ST312 treats the module as a benchmark artifact and does not present it as a deployment recommendation

