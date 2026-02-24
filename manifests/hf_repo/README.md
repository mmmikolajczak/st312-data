---
pretty_name: "ST312 FinLLM Data (Private)"
tags:
- finance
- llm
- sentiment-analysis
- private-dataset
configs:
- config_name: fpb_allagree_v0
  data_files:
  - split: train
    path: datasets/fpb/allagree/v0/train.jsonl
  - split: test
    path: datasets/fpb/allagree/v0/test.jsonl
- config_name: fiqasa_hf_default_v0
  data_files:
  - split: train
    path: datasets/fiqasa/default/v0/train.jsonl
  - split: validation
    path: datasets/fiqasa/default/v0/valid.jsonl
  - split: test
    path: datasets/fiqasa/default/v0/test.jsonl
---

# ST312 FinLLM Data (Private)

Private artifact repository for the ST312 Applied Statistics project (FinLLM pipeline).

This Hugging Face dataset repo stores canonical processed datasets, task request files, manifest snapshots, checksums, and publish records.

## Structure

- `datasets/` — canonical processed dataset artifacts
- `tasks/` — task request JSONL files and task README snapshots
- `manifests/` — dataset/task specs, checksums, publish records
- `runs/` — reserved for completions / eval outputs (future)

## Published contents

### FPB all-agree v0
Dataset artifacts:
- `datasets/fpb/allagree/v0/train.jsonl`
- `datasets/fpb/allagree/v0/test.jsonl`
- `datasets/fpb/allagree/v0/split_meta.json`

Task requests:
- `tasks/fpb_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fpb_sentiment_v0/requests/test_requests.jsonl`

### FiQA-SA HF default v0
Dataset artifacts:
- `datasets/fiqasa/default/v0/train.jsonl`
- `datasets/fiqasa/default/v0/valid.jsonl`
- `datasets/fiqasa/default/v0/test.jsonl`
- `datasets/fiqasa/default/v0/clean_meta.json`

Task requests:
- `tasks/fiqasa_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/valid_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/test_requests.jsonl`

## Labeling notes

### FPB
3-way sentiment labels provided directly in processed task format:
- `negative`, `neutral`, `positive`

### FiQA-SA
Original upstream sentiment is continuous. We publish a 3-way discretised label using:
- `score <= -0.1` -> `negative`
- `score >=  0.1` -> `positive`
- otherwise -> `neutral`

## Licensing

Licensing metadata is recorded in each dataset manifest under:
- `manifests/datasets/<dataset_id>/dataset_spec.json`

Please consult upstream licenses before any public redistribution or commercial use.
