# convfinqa_program_generation_v0

Canonical ConvFinQA turn-level conversational program-generation task over `convfinqa_official_v0`.

## Formal task id
`TA_PROGGEN_CONVFINQA_v0`

## Task definition
- canonical output is `program_tokens`
- input evidence is the current question, dialogue history, pre-table text, the serialized table, and post-table text
- output is JSON with exactly one key: `program_tokens`
- the final answer is derived by executing the predicted program
- primary metric is execution accuracy
- secondary metric is program accuracy
- auxiliary supervision such as supporting facts and turn type is preserved in the dataset layer, but not used for the top-line benchmark score
- the raw test release is unlabeled at the pinned commit, so this task publishes supervised `train / dev` only

## Output schema
Return ONLY a JSON object of this form:

```json
{
  "program_tokens": ["subtract(", "5829", "5735", ")", "EOF"]
}
```

For `number_turn` examples, a valid program can also be a single numeric token followed by `EOF`, for example:

```json
{
  "program_tokens": ["206588", "EOF"]
}
```

## Reward stance
- `format_reward`: valid JSON with exactly one key and a token list ending in `EOF`
- `dsl_validity_reward`: program satisfies the FinQA-family DSL structure, including single-number programs used in upstream `number_turn` supervision
- `execution_reward`: predicted program executes to the gold execution answer
- `program_match_reward`: predicted program matches the canonical gold program under the FinQA-family program matcher
