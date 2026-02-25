# FinBen FINER-ORD NER Task (v0)

Task module for token-level NER tagging (BIO format) on `finben_finer_ord_v0`.

## Task ID
`TA_NER_FINER_ORD_FINBEN_v0`

## Dataset module
- Dataset ID: `finben_finer_ord_v0`
- Train: `data/finer_ord/processed/finben_finer_ord_train.jsonl`
- Test: `data/finer_ord/processed/finben_finer_ord_test.jsonl`

## Labels
- `O`
- `B-PER`, `I-PER`
- `B-LOC`, `I-LOC`
- `B-ORG`, `I-ORG`

## Output schema (strict)
Return ONLY:
```json
{"tags": ["O", "B-ORG", "I-ORG"]}
```

Rules:
- Exactly one key: `tags`
- `tags` must be a JSON array of strings
- Length must match number of input tokens
- Every tag must be one of the allowed BIO labels
- No extra keys
- No extra text

<!-- REWARD_SECTION_START -->
## Reward function (shaped, v1)

This task uses a **strict-format + shaped-correctness** reward.

### Total reward
`total_reward = format_reward + correctness_reward_industry`

- `format_reward` ∈ {0, 1}
  - 1 only if output is valid JSON with exactly one key (`"tags"`), all tags valid, and length matches input tokens
- `correctness_reward_industry` ∈ [0, 1]
  - `0.50 * entity_span_f1`
  - `0.40 * token_accuracy`
  - `0.10 * exact_sequence_match`

So the total reward is in **[0, 2]**.

This design is stricter than free-form outputs but more informative than all-or-nothing correctness, and is better suited to RL/GRPO-style optimization.
<!-- REWARD_SECTION_END -->

