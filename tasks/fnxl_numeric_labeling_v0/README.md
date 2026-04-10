# FNXL Numeric Labelling Task (v0)

Task module for sparse numeric token labelling on the canonical clean FNXL split.

## Task ID

`TA_IE_NUMERIC_LABEL_FNXL_v0`

## Canonical split

- Train: `data/fnxl_sharma2023/processed/fnxl_clean_company_split_train.jsonl`
- Test: `data/fnxl_sharma2023/processed/fnxl_clean_company_split_test.jsonl`

## Output schema (strict)

Return ONLY:

    {"mentions": [{"token_index": 26, "label_id": 1}]}

Rules:
- Exactly one key: `mentions`
- `mentions` must be a JSON array
- Each item must have exactly keys `token_index` and `label_id`
- `token_index` must be a non-negative integer
- `label_id` must be an integer in the observed used FNXL ID range `[1, 2799]`
- Output only positively labeled numeric mentions
- If none are present, return `{"mentions": []}`
- One token may receive at most one label
- No extra text

## Evaluation

Cached evaluation reports:
- micro precision / recall / F1
- macro precision / recall / F1
- exact-set accuracy

## Label ontology note

The canonical prediction target is `label_id`, not label strings, because label IDs map cleanly across the full used space while a small label-name discrepancy exists between `labels.json` and the authoritative `allLabelCount.csv`.
