---
pretty_name: "ST312 FinLLM Data (Private)"
tags:
- finance
- llm
- private-dataset
- text-classification
- token-classification
---

# ST312 FinLLM Data (Private)

Private artifact repository for the ST312 Applied Statistics project (FinLLM pipeline).
This Hugging Face dataset repo stores canonical processed datasets, task request files,
manifest snapshots, checksums, and publication bookkeeping artifacts.

## Structure

- `datasets/` — canonical processed dataset artifacts
- `tasks/` — task request JSONL files and task README snapshots
- `manifests/` — dataset/task specs, checksums, and publication bookkeeping
- `runs/` — reserved for completions / eval outputs (future)

## Viewer note

This repo is a multi-module artifact store rather than a single homogeneous dataset.
Per-module file paths below are the reliable index of published contents.

## Published contents

### 10) FinArg ECC AUC v0

Dataset artifacts:
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_all_clean.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_clean_meta.json`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_train.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_dev.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_test.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_split_meta.json`

Task requests:
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_train_requests.jsonl`
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_dev_requests.jsonl`
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_test_requests.jsonl`

Task README snapshot:
- `tasks/finarg_auc_ecc_v0/README.md`

Auxiliary provenance report:
- `reports/finarg_auc_ecc_official/raw_audit_summary.json`

Publish bookkeeping:
- `manifests/publish/finarg_auc_ecc_official_v0_publish_record.json`

### 11) FinArg ECC ARC v0

Dataset artifacts:
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_all_clean.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_clean_meta.json`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_train.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_dev.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_test.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_split_meta.json`

Task requests:
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_train_requests.jsonl`
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_dev_requests.jsonl`
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_test_requests.jsonl`

Task README snapshot:
- `tasks/finarg_arc_ecc_v0/README.md`

Auxiliary provenance report:
- `reports/finarg_arc_ecc_official/raw_audit_summary.json`

Publish bookkeeping:
- `manifests/publish/finarg_arc_ecc_official_v0_publish_record.json`

## Labeling / split notes

### FinArg ECC

- AUC uses the preserved official ECC split with labels inferred from official totals as `0 -> premise`, `1 -> claim`
- ARC uses the preserved official ECC split with labels inferred from official totals as `0 -> other`, `1 -> support`, `2 -> attack`
- One exact AUC sentence overlap exists across train/dev and is preserved as a documented release issue
- ARC shows no cross-split exact-pair overlap in the local ECC release
- ARC is strongly class-imbalanced, especially for the `attack` class, so macro-aware evaluation is emphasized

## Licensing

- FinArg ECC artifacts are tracked with `GPL-3.0_inferred_from_public_finarg_repo`
- Local release copy used for ingestion contained no embedded README or LICENSE
- Treat redistribution posture with caution unless shared-task release terms are independently confirmed
