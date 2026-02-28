# MultiFin High-Level Dataset Module (v0)

Canonical dataset module for the original `awinml/MultiFin` dataset using the
`all_languages_highlevel` config.

## Dataset ID
`multifin_highlevel_v0`

## Upstream source
- Hugging Face dataset: `awinml/MultiFin`
- Config: `all_languages_highlevel`

## Split policy
We preserve the original upstream split:
- train: 6430
- validation: 1608
- test: 2010

## Label space
- Technology
- Industry
- Tax & Accounting
- Finance
- Government & Controls
- Business & Management

## Local artifacts (not tracked in Git)
Raw:
- `data/multifin/raw/multifin_highlevel_train_raw.jsonl`
- `data/multifin/raw/multifin_highlevel_validation_raw.jsonl`
- `data/multifin/raw/multifin_highlevel_test_raw.jsonl`
- `data/multifin/raw/multifin_highlevel_raw_meta.json`

Processed:
- `data/multifin/processed/multifin_highlevel_train_clean.jsonl`
- `data/multifin/processed/multifin_highlevel_validation_clean.jsonl`
- `data/multifin/processed/multifin_highlevel_test_clean.jsonl`
- `data/multifin/processed/multifin_highlevel_clean_meta.json`

## Notes
This module is dataset-level only. Task-specific prompts, reward logic and evaluation
will live under:
- `tasks/multifin_highlevel_topic_v0/`
- `scripts/tasks/multifin_highlevel_topic_v0/`
