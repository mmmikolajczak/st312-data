# bigdata22_stock_movement_v0

Canonical original-paper BigData22 stock movement prediction task over `bigdata22_official_v0`.

## Formal task id
`TA_FORECAST_BIGDATA22_v0`

## Task definition
- canonical output is JSON with exactly one key: `label`
- allowed labels are exactly `Rise` or `Fall`
- canonical task is the original-paper binary stock movement prediction problem from historical price features plus tweets
- this is the original BigData22 paper task, not the later FinBen/OpenFinLLM-style prompt wrapper
- canonical paper-window scope is restricted to `2019-07-05` through `2020-06-30`
- raw release labels are preserved, the task interface maps `1 -> Rise` and `-1 -> Fall`, and neutral-band `0` rows are excluded

## Canonical metrics
- primary metric: `mcc`
- secondary metric: `accuracy`
- supporting run diagnostics: `format_valid_rate` and `completion_coverage`

## Split note
- the official archive does not ship split files
- the paper states only that the split is chronological, so ST312 derives a documented reconstruction over sorted unique target trading dates inside the paper window after excluding neutral-band rows
- no public first-party split files or cut dates were recoverable from the official repo, bundled archive, paper PDF, or repo git history
- the current ST312-derived target-date ranges are `2019-07-05..2020-03-13`, `2020-03-16..2020-04-20`, and `2020-04-21..2020-06-30`

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "label": "Rise"
}
```
