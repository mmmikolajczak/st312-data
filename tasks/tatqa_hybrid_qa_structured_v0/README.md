# tatqa_hybrid_qa_structured_v0

Canonical TAT-QA structured hybrid-QA task over `tatqa_official_v0`.

## Formal task id
`TA_QA_TATQA_v0`

## Task definition
- canonical task is hybrid QA over the question, serialized table, and ordered paragraphs
- output is strict JSON with `answer`, `scale`, `derivation`, `answer_type`, `answer_from`, `rel_paragraphs`, and `req_comparison`
- only `answer` and `scale` feed the official top-line benchmark score
- auxiliary fields are preserved for richer supervision, auxiliary rewards, and optional diagnostics
- derivation is preserved, but it is not the canonical benchmark target

## Metrics
- canonical official metrics: `exact_match`, `f1`, `scale_score`
- additional diagnostics: `format_valid_rate`, `completion_coverage`
- optional auxiliary diagnostics: answer-type accuracy, answer-from accuracy, paragraph-overlap F1, req-comparison accuracy, derivation accuracy on arithmetic questions

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "answer": -12.6,
  "scale": "million",
  "derivation": "44.1 - 56.7",
  "answer_type": "arithmetic",
  "answer_from": "table-text",
  "rel_paragraphs": ["2"],
  "req_comparison": false
}
```

## Reward stance
- `format_reward`: valid structured JSON with the required keys and an allowed scale
- `official_answer_reward`: official answer+scale correctness under TAT-QA EM/F1 semantics
- `scale_reward`: explicit small bonus for correct scale
- auxiliary low-weight rewards: `answer_type_reward`, `answer_from_reward`, `rel_paragraph_reward`, `req_comparison_reward`, `derivation_reward`
