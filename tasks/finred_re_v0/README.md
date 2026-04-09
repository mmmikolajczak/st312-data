# FinRED Relation Extraction Task (v0)

Task module for joint relation / triplet extraction from FinRED.

## Task ID

`TA_RE_FINRED_v0`

## Dataset module

- Dataset ID: `finred_official_v0`
- Train: `data/finred_official/processed/finred_official_train.jsonl`
- Dev: `data/finred_official/processed/finred_official_dev.jsonl`
- Test: `data/finred_official/processed/finred_official_test.jsonl`

## Output schema (strict)

Return ONLY:

    {"triplets": [{"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs"}]}

Rules:
- Exactly one key: `triplets`
- `triplets` must be a JSON array
- Each triplet must have exactly these keys: `head`, `relation`, `tail`
- Relation must be one of the allowed FinRED relations
- Use entity surface forms exactly as they appear in the sentence
- If no supported relation is present, return `{"triplets": []}`
- No extra keys
- No extra text

## Reward function

`total_reward = format_reward + correctness_reward_industry`

- `format_reward` in `{0, 1}`
- `correctness_reward_industry` in `[0, 1]`
  - `0.70 * triplet_f1`
  - `0.20 * entity_pair_f1`
  - `0.10 * exact_set_match`

Total reward range: `[0, 2]`

## Data quality note

FinRED train/dev are weakly supervised via distant supervision; the test split is the higher-trust manual evaluation split.
