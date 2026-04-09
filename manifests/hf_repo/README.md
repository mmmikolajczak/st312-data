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

This Hugging Face dataset repo stores canonical processed datasets, task request files, manifest snapshots, checksums, and publication bookkeeping artifacts.

## Structure

- `datasets/` — canonical processed dataset artifacts
- `tasks/` — task request JSONL files and task README snapshots
- `manifests/` — dataset/task specs, checksums, and publication bookkeeping
- `runs/` — reserved for completions / eval outputs (future)

## Viewer note

This repo is a multi-module artifact store rather than a single homogeneous dataset.
Per-module file paths below are the reliable index of published contents.

## Published contents

### 1) FPB all-agree v0

Dataset artifacts:
- `datasets/fpb/allagree/v0/train.jsonl`
- `datasets/fpb/allagree/v0/test.jsonl`
- `datasets/fpb/allagree/v0/split_meta.json`

Task requests:
- `tasks/fpb_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fpb_sentiment_v0/requests/test_requests.jsonl`

### 2) FiQA-SA HF default v0

Dataset artifacts:
- `datasets/fiqasa/default/v0/train.jsonl`
- `datasets/fiqasa/default/v0/valid.jsonl`
- `datasets/fiqasa/default/v0/test.jsonl`
- `datasets/fiqasa/default/v0/clean_meta.json`

Task requests:
- `tasks/fiqasa_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/valid_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/test_requests.jsonl`

### 3) FinBen FOMC v0

Dataset artifacts:
- `datasets/fomc/finben/v0/all_clean.jsonl`
- `datasets/fomc/finben/v0/train.jsonl`
- `datasets/fomc/finben/v0/test.jsonl`
- `datasets/fomc/finben/v0/clean_meta.json`
- `datasets/fomc/finben/v0/split_meta.json`

Task requests:
- `tasks/finben_fomc_stance_v0/requests/train_requests.jsonl`
- `tasks/finben_fomc_stance_v0/requests/test_requests.jsonl`

### 4) FinBen FINER-ORD v0

Dataset artifacts:
- `datasets/finer_ord/finben/v0/all_clean.jsonl`
- `datasets/finer_ord/finben/v0/train.jsonl`
- `datasets/finer_ord/finben/v0/test.jsonl`
- `datasets/finer_ord/finben/v0/clean_meta.json`
- `datasets/finer_ord/finben/v0/split_meta.json`

Task requests:
- `tasks/finben_finer_ord_ner_v0/requests/train_requests.jsonl`
- `tasks/finben_finer_ord_ner_v0/requests/test_requests.jsonl`

### 5) MultiFin high-level v0

Dataset artifacts:
- `datasets/multifin/highlevel/v0/train.jsonl`
- `datasets/multifin/highlevel/v0/validation.jsonl`
- `datasets/multifin/highlevel/v0/test.jsonl`
- `datasets/multifin/highlevel/v0/clean_meta.json`

Task requests:
- `tasks/multifin_highlevel_topic_v0/requests/train_requests.jsonl`
- `tasks/multifin_highlevel_topic_v0/requests/validation_requests.jsonl`
- `tasks/multifin_highlevel_topic_v0/requests/test_requests.jsonl`

### 6) Salinas SEC loan-agreement NER v0

Dataset artifacts:
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_all_clean.jsonl`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_train.jsonl`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_test.jsonl`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_clean_meta.json`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_split_meta.json`

Task requests:
- `tasks/salinas_sec_loan_ner_v0/salinas_sec_loan_ner_train_requests.jsonl`
- `tasks/salinas_sec_loan_ner_v0/salinas_sec_loan_ner_test_requests.jsonl`

Task README snapshot:
- `tasks/salinas_sec_loan_ner_v0/README.md`

Publish bookkeeping:
- `manifests/publish/salinas_sec_loan_ner_v0_publish_record.json`

## Labeling / split notes

### FPB

3-way sentiment labels are provided directly in processed task format:
- `negative`
- `neutral`
- `positive`

### FiQA-SA

Original upstream sentiment is continuous.
We publish a 3-way discretised label using:
- `score <= -0.1` -> `negative`
- `score >= 0.1` -> `positive`
- otherwise -> `neutral`

### Salinas SEC loan-agreement NER

- Original author split preserved: `FIN5` train, `FIN3` test
- Original entity set retained: `PER`, `LOC`, `ORG`, `MISC`
- The corpus-specific `lender` / `borrower` -> `PER` annotation convention is preserved and documented

## Licensing

Licensing metadata is recorded in each dataset manifest under:
- `manifests/datasets/<dataset_id>/dataset_spec.json`

Please consult upstream licenses before any public redistribution or commercial use.
