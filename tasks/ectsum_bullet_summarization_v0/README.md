# ectsum_bullet_summarization_v0

Canonical original-paper ECTSum summarization task over `ectsum_official_v0`.

## Formal task id
`TA_SUM_ECTSUM_v0`

## Task definition
- canonical output is JSON with exactly one key: `summary`
- canonical task is bullet-style summarization of earnings-call Prepared Remarks
- default evaluation variant is `ectsum_original`
- optional evaluation variant is `finben_summary`

## Default evaluation variant: original ECTSum
- ROUGE via `rouge-score==0.1.2`
- BERTScore via `bert-score==0.3.13`
- BERTScore model: `microsoft/deberta-xlarge-mnli`
- SummaCConv via `summac==0.0.4`
- SummaC model: `vitc`
- Num-Prec: transparent local implementation of numeric precision against source transcript or reference summary values

## Optional evaluation variant: FinBen-compatible
- ROUGE via `rouge-score==0.1.2`
- BERTScore via `bert-score==0.3.13`
- BERTScore model: `microsoft/deberta-xlarge-mnli`
- BARTScore-style similarity using `facebook/bart-large-cnn` through `transformers==4.24.0`

## Publication note
- this module is fully integrated into the normal ST312 pipeline and artifact layout
- the artifact is publicly published with an upstream licensing / redistribution caution
- the module should not be described as publicly redistribution-cleared

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "summary": "..."
}
```
