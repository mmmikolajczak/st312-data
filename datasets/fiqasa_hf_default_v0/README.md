# FiQA-SA Dataset Module (v0)

This dataset module stores metadata for the FiQA Sentiment Analysis dataset (Hugging Face version),
using the original train/valid/test split and a 3-way sentiment label derived from the continuous score.

## Dataset ID
`fiqasa_hf_default_v0`

## Upstream source
- Hugging Face dataset: `TheFinAI/fiqa-sentiment-classification`

## Split policy
We preserve the upstream split:
- train: 822
- valid: 117
- test: 234

## Label scheme (discretised from continuous score)
We convert the original continuous sentiment score to 3 classes using:
- `score <= -0.1` -> `negative`
- `score >=  0.1` -> `positive`
- otherwise -> `neutral`

This is aligned with common FinLLM benchmark usage of FiQA-SA as a 3-way classification task.

## Local artifacts (not tracked in Git)
Raw:
- `data/fiqasa/raw/fiqasa_train_raw.jsonl`
- `data/fiqasa/raw/fiqasa_valid_raw.jsonl`
- `data/fiqasa/raw/fiqasa_test_raw.jsonl`

Processed:
- `data/fiqasa/processed/fiqasa_train_clean.jsonl`
- `data/fiqasa/processed/fiqasa_valid_clean.jsonl`
- `data/fiqasa/processed/fiqasa_test_clean.jsonl`
- `data/fiqasa/processed/fiqasa_clean_meta.json`

## Notes
This module is dataset-level only. Task-specific prompts/rewards/eval scripts will live under:
- `tasks/fiqasa_sentiment_v0/`
- `scripts/tasks/fiqasa_sentiment_v0/`
