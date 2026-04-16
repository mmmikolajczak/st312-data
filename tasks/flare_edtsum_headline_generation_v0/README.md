# flare_edtsum_headline_generation_v0

Canonical FinBen-aligned EDTSUM task over `flare_edtsum_public_test_v0`.

## Formal task id
`TA_HEADLINE_EDTSUM_FLARE_v0`

## Task definition
- canonical task is financial news headline generation from full article text
- acceptable equivalent phrasing is headline-style abstractive summarization, but the target is a short title / headline rather than a paragraph summary
- this module is eval-only benchmark evaluation, not a standard training corpus
- output is JSON with exactly one key: `answer`
- only the generated `answer` string is scored

## Evaluation variants
- `stable_default`: ROUGE + BERTScore with format-validity and coverage, designed to be robust in local evaluation
- `finben_paper_alignment`: ROUGE + BERTScore + best-effort BARTScore, matching the FinBen paper surface as closely as practical without making BARTScore the critical path

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "answer": "..."
}
```

## Notes
- prompt wording explicitly asks for a headline-style answer to avoid paragraph-like outputs
- this module is not treated as a primary GRPO training dataset because it is small, test-only, and rights-sensitive
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.
- the evaluator tracks raw completion coverage, format validity, and non-empty answer rates separately from content metrics
