# Australian Credit MC Task v0

Derived FLARE-style promptified benchmark task built from canonical UCI Statlog raw data.

## Task ID

`TA_MC_AUSTRALIAN_CREDIT_UCI_v0`

## Output contract

Return ONLY JSON:

`{"label": "Reject"}`

or

`{"label": "Approve"}`

## Metrics

- primary: accuracy
- secondary: macro-F1
- also report: per-class F1, weighted-F1, micro-F1

## Reward shape

- valid + correct: 1.0
- valid + wrong: 0.1
- invalid / unparsable: 0.0
