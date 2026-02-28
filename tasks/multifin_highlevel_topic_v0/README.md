# MultiFin High-Level Topic Task (v0)

Task module for 6-way topic classification on `multifin_highlevel_v0`.

## Task ID
`TA_TOPIC_MULTIFIN_HIGHLEVEL_v0`

## Dataset module
- Dataset ID: `multifin_highlevel_v0`
- Train: `data/multifin/processed/multifin_highlevel_train_clean.jsonl`
- Validation: `data/multifin/processed/multifin_highlevel_validation_clean.jsonl`
- Test: `data/multifin/processed/multifin_highlevel_test_clean.jsonl`

## Labels
- `Technology`
- `Industry`
- `Tax & Accounting`
- `Finance`
- `Government & Controls`
- `Business & Management`

## Output schema (strict)
Return ONLY:
```json
{"topic": "Finance"}
```

Rules:
- exactly one key: `topic`
- value must be one of the six allowed labels
- no extra keys
- no extra text

## Scripts
- Reward parser: `scripts/tasks/multifin_highlevel_topic_v0/reward_multifin_highlevel.py`
