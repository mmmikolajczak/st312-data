# flare_ma_deal_completeness_v0

Eval-only binary classification task over `flare_ma_public_test_v0`.

## Formal task id
`TA_MA_COMPLETENESS_FLARE_v0`

## Input
- `data.text`

## Output
Return ONLY a JSON object with exactly one key:
- `label`

Allowed label values:
- `rumour`
- `complete`

## Evaluation
The evaluator reports:
- accuracy
- macro F1
- binary F1 with `complete` as positive
- MCC
- format-valid rate

## Reward stance
This task follows the standard simple-classification reward shape:
- 1 point for valid schema / valid label
- 1 point for exact label correctness

The evaluator remains the source of truth.
