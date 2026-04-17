# flare_sm_cikm_stock_movement_v0

Wrapper-based accessible CIKM18-family stock movement prediction task over `flare_sm_cikm_public_v0`.

## Formal task id
`TA_FORECAST_FLARE_SM_CIKM_v0`

## Task definition
- canonical output is JSON with exactly one key: `label`
- allowed labels are exactly `Rise` or `Fall`
- this task is based on the accessible FinAI wrapper `TheFinAI/flare-sm-cikm`, not the unrecoverable original first-party CIKM18 author release
- the wrapper split is preserved exactly as observed
- original-paper conventions are preserved where still supportable:
  - binary next-day movement prediction
  - no neutral-band semantics in the canonical label interpretation
  - `accuracy` as the default original-like metric

## Evaluation variants
- `cikm18_original_like`
  - metrics: `accuracy`
  - diagnostics: `format_valid_rate`, `completion_coverage`
  - parser mode: strict JSON `{ "label": "Rise" | "Fall" }`
- `finben_compatible`
  - metrics: `accuracy`, `mcc`
  - diagnostics: `format_valid_rate`, `completion_coverage`
  - parser mode: first valid strict JSON label, then unambiguous fallback extraction of `Rise` or `Fall` from free text

## Reward paths
- default GRPO reward: `reward_cikm18_label.py`
  - strict JSON discipline
  - one-key schema enforcement
  - dense exact-label correctness
- optional FinBen-compatible reward: `reward_cikm18_finben.py`
  - lenient label extraction from JSON or unambiguous text
  - intended for benchmark-style compatibility experiments rather than the canonical strict-output path

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "label": "Rise"
}
```

## Provenance note
- this task is wrapper-based and should not be described as the original first-party CIKM18 benchmark release
- original-paper CIKM18 reported `accuracy` only; MCC is available here only as an optional FinBen-compatible comparator
- wrapper/documentation drift on counts, threshold wording, and metric wording is recorded in the dataset audit and publish metadata
