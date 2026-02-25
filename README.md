---
license: other
pretty_name: ST312 Data Pipeline Artifacts
task_categories:
- text-classification
tags:
- finance
- sentiment-analysis
- benchmark
- llm
---

# ST312 Data

Repository for the ST312 Applied Statistics project data/task pipeline (FinLLM benchmark preparation).

This repo is the code + metadata control plane:
- dataset ingestion / cleaning / normalisation scripts
- task specs, prompts, reward parsers, evaluators
- registries and manifests for reproducibility
- publish records and checksums

Large data artifacts are not tracked in GitHub. They are published to the private Hugging Face dataset repo:
- `mmmikolajczak/st312-data`

## Repository architecture

### `datasets/`
Dataset modules (metadata only):
- dataset README
- dataset spec
- checksums for canonical processed artifacts
- dataset registry (`datasets/dataset_registry.json`)

### `tasks/`
Task modules (metadata only):
- task README
- task spec
- task registry (`tasks/task_registry.json`)

### `scripts/datasets/<dataset>/`
Dataset-level pipeline scripts:
- ingestion
- cleaning
- splitting / normalisation

### `scripts/tasks/<task_id>/`
Task-level scripts:
- reward parser
- prompt renderer
- request builder
- cached evaluator

### `manifests/`
Immutable-ish snapshots and bookkeeping:
- `manifests/datasets/...` dataset spec snapshots + checksums
- `manifests/tasks/...` task spec snapshots
- `manifests/publish/...` publish records (GitHub/HF commit history)
- `manifests/hf_repo/README.md` source-of-truth for HF dataset repo README

### `data/`
Local-only working artifacts (ignored by Git):
- raw downloads
- processed JSONL files
- generated request files
- temporary previews / dummy completions

### `reports/`
Evaluation outputs (JSON reports etc.)

## Current dataset modules

### 1) FPB all-agree v0
- Dataset ID: `fpb_allagree_v0`
- Task ID: `TA_SENT_FPB_v0`
- Status: published to HF
- Label space: `negative`, `neutral`, `positive`

### 2) FiQA-SA HF default v0
- Dataset ID: `fiqasa_hf_default_v0`
- Task ID: `TA_SENT_FIQASA_v0`
- Status: published to HF
- Labeling: 3-way discretisation from continuous sentiment score
  - `score <= -0.1` -> `negative`
  - `score >=  0.1` -> `positive`
  - otherwise -> `neutral`

## Current task modules

### FPB sentiment
- `tasks/fpb_sentiment_v0/`
- `scripts/tasks/fpb_sentiment_v0/`

### FiQA-SA sentiment
- `tasks/fiqasa_sentiment_v0/`
- `scripts/tasks/fiqasa_sentiment_v0/`

## Reproducibility conventions

- Canonical processed artifacts live in local `data/...` and are published to HF.
- GitHub tracks metadata/manifests/checksums, not the full datasets.
- Every published dataset/task should have:
  - dataset/task module README
  - dataset/task spec
  - manifest snapshots
  - checksums
  - publish record with HF commit hashes

## Quick workflow for a new dataset

1. Add dataset ingestion + cleaning scripts under `scripts/datasets/<dataset>/`
2. Produce local processed JSONL artifacts in `data/<dataset>/processed/`
3. Add dataset module under `datasets/<dataset_module>/`
4. Add task module under `tasks/<task_module>/`
5. Add task scripts under `scripts/tasks/<task_module>/`
6. Build request files
7. Snapshot manifests + checksums
8. Upload artifacts to HF
9. Add publish record
10. Push GitHub metadata/manifests

## Notes

This repo is designed so new datasets/tasks can be added with the same pattern and minimal ambiguity.

<!-- ST312_PUBLISHED_MODULES_START -->
## Published dataset/task modules (HF-ready)

This repository tracks dataset and task modules for the ST312/Risko-1 pipeline.
Canonical HF dataset repo: `mmmikolajczak/st312-data`

### Published modules

#### 1) Financial PhraseBank (all-agree) v0
- **Dataset ID:** `fpb_allagree_v0`
- **Task ID:** `TA_SENT_FPB_v0`
- **HF dataset path:** `datasets/fpb/allagree/v0/`
- **HF task path:** `tasks/fpb_sentiment_v0/`
- **Publish record:** `manifests/publish/fpb_allagree_v0_publish_record.json`

#### 2) FiQA-SA (HF default split) v0
- **Dataset ID:** `fiqasa_hf_default_v0`
- **Task ID:** `TA_SENT_FIQASA_v0`
- **HF dataset path:** `datasets/fiqasa/default/v0/`
- **HF task path:** `tasks/fiqasa_sentiment_v0/`
- **Publish record:** `manifests/publish/fiqasa_hf_default_v0_publish_record.json`

#### 3) FinBen FOMC v0
- **Dataset ID:** `finben_fomc_v0`
- **Task ID:** `TA_STANCE_FOMC_FINBEN_v0`
- **HF dataset path:** `datasets/fomc/finben/v0/`
- **HF task path:** `tasks/finben_fomc_stance_v0/`
- **Publish record:** `manifests/publish/finben_fomc_v0_publish_record.json`

#### 4) FinBen FINER-ORD v0
- **Dataset ID:** `finben_finer_ord_v0`
- **Task ID:** `TA_NER_FINER_ORD_FINBEN_v0`
- **HF dataset path:** `datasets/finer_ord/finben/v0/`
- **HF task path:** `tasks/finben_finer_ord_ner_v0/`
- **Publish record:** `manifests/publish/finben_finer_ord_v0_publish_record.json`

### Validation
Use:
`python scripts/utils/check_publish_records.py`

Current status target convention:
- registry status: `published`
- dataset spec status: `"published_to_hf": true`
<!-- ST312_PUBLISHED_MODULES_END -->


