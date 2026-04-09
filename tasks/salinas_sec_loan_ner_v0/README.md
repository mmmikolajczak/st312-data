# Salinas SEC Loan Agreements NER Task (v0)

Task module for strict-JSON BIO2 token tagging on `salinas_sec_loan_ner_v0`.

## Task ID

`TA_NER_SEC_LOAN_SALINAS_v0`

## Dataset module

- Dataset ID: `salinas_sec_loan_ner_v0`
- Train: `data/salinas_sec_loan_ner/processed/salinas_sec_loan_ner_train.jsonl`
- Test: `data/salinas_sec_loan_ner/processed/salinas_sec_loan_ner_test.jsonl`

## Labels

- `O`
- `B-PER`, `I-PER`
- `B-LOC`, `I-LOC`
- `B-ORG`, `I-ORG`
- `B-MISC`, `I-MISC`

## Output schema (strict)

Return ONLY:

    {"tags": ["O", "B-ORG", "I-ORG"]}

Rules:
- Exactly one key: `tags`
- `tags` must be a JSON array of strings
- Length must match number of input tokens
- Every tag must be one of the allowed BIO2 labels
- No extra keys
- No extra text

## Reward function

`total_reward = format_reward + correctness_reward_industry`

- `format_reward` in `{0, 1}`
- `correctness_reward_industry` in `[0, 1]`
  - `0.50 * entity_span_f1`
  - `0.40 * token_accuracy`
  - `0.10 * exact_sequence_match`

Total reward range: `[0, 2]`
