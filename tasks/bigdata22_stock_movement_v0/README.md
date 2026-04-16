# bigdata22_stock_movement_v0

Canonical original-paper BigData22 stock movement prediction task over `bigdata22_official_v0`.

## Formal task id
`TA_FORECAST_BIGDATA22_v0`

## Task definition
- canonical output is JSON with exactly one key: `label`
- allowed labels are exactly `Rise` or `Fall`
- canonical task is the original-paper binary stock movement prediction problem from historical price features plus tweets
- this is the original BigData22 paper task, not the later FinBen/OpenFinLLM-style prompt wrapper

## Canonical metrics
- primary metric: `mcc`
- secondary metric: `accuracy`
- supporting run diagnostics: `format_valid_rate` and `completion_coverage`

## Split note
- the official archive does not ship split files
- ST312 uses a documented chronological reconstruction over the official paper window, with `train / valid / test` target-date ranges `2019-07-05..2020-03-13`, `2020-03-16..2020-04-17`, and `2020-04-20..2020-06-30`

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "label": "Rise"
}
```
