# finqa_program_generation_v0

Canonical FinQA program-generation task over `finqa_official_v0`.

## Formal task id
`TA_PROGGEN_FINQA_v0`

## Task definition
- canonical task is program generation in the FinQA DSL
- input evidence is the question, pre-table text, the serialized table, and post-table text
- output is JSON with exactly one key: `program_tokens`
- the final answer is derived by executing the predicted program
- answer-only QA is out of scope for this canonical module

## Metrics
- primary metric: execution accuracy
- secondary metric: program accuracy
- additional diagnostics: format-valid rate, DSL-valid rate, execution accuracy on valid programs, program exact match, coverage

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "program_tokens": ["divide(", "9413", "20.01", ")", "EOF"]
}
```

## Reward stance
- `format_reward`: valid JSON with exactly one key and a token list ending in `EOF`
- `dsl_validity_reward`: program parses under the allowed FinQA DSL grammar
- `execution_reward`: predicted program executes to the gold execution answer
- `program_match_reward`: predicted program is symbolically equivalent to the gold program under the official evaluator logic
