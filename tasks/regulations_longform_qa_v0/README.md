# regulations_longform_qa_v0

Canonical FinBen Regulations long-form QA task over `regulations_public_test_v0`.

## Formal task id
`TA_LFQA_REGULATIONS_FINBEN_v0`

## Task definition
- canonical task is long-form answer generation
- this module is eval-only wrapper evaluation, not a training task
- output is JSON with exactly one key: `answer`
- only the generated `answer` string is scored
- canonical metric family is ROUGE + BERTScore
- implementation is best-faith paper-aligned because no public Regulations-specific evaluator/config was found in the searchable FinBen release surfaces

## Metric implementation
- ROUGE package: `rouge-score==0.1.2`
- BERTScore package: `bert-score==0.3.13`
- BERTScore model: `roberta-large`
- language: English

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "answer": "..."
}
```
