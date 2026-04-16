# stocknet_acl18_stockmove_v0

Canonical ACL18 StockNet stock movement prediction task over `stocknet_acl18_paper_v0`.

## Formal task id
`FC_STOCKMOVE_STOCKNET_ACL18_v0`

## Task definition
- canonical output is JSON with exactly one key: `label`
- allowed labels are exactly `Rise` or `Fall`
- canonical task is the paper-level binary stock movement forecasting problem from 5-day aligned tweet corpora plus historical stock prices
- this is the original ACL18 task, not a copied FLARE prompt wrapper

## Evaluation variants
- `paper_default`: canonical Accuracy + MCC evaluation over the exact paper test split
- `finben_acl18_optional`: compatibility parser/view that accepts canonical `label` outputs and optional wrapper-style `answer` outputs while still reporting Accuracy + MCC

## Canonical metrics
- benchmark metrics: `accuracy`, `mcc`
- operational diagnostics: `format_valid_rate`, `completion_coverage`, `nonempty_label_rate`

## Notes
- reward helpers are exploratory and offline-only; canonical model comparison uses the cached evaluator, not the reward totals
- the dataset README and reconstruction audit document a source inconsistency around tweet-presence filtering versus exact paper counts
- Original source repository is MIT-licensed. The released corpus includes tweet-derived content collected under Twitter's official license and price data sourced from Yahoo Finance; downstream users should review applicable platform/source terms before reuse.

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "label": "Rise"
}
```
