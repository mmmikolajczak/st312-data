# FPB Allagree Dataset (v0)

This folder contains the **dataset definition** (not the data itself) for the Financial PhraseBank `allagree` subset used in the ST312 FinLLM pipeline.

## What lives here
- `dataset_spec.json` — machine-readable dataset blueprint
- (optional later) `schema.json` — formal processed row schema
- this README

## What does NOT live here
No actual dataset files are stored in GitHub.

Canonical dataset artifacts live in:
- local development cache: `data/fpb/...` (gitignored)
- Hugging Face private dataset repo (to be configured)

## Current processed artifacts (local)
- `data/fpb/processed/fpb_allagree_train.jsonl`
- `data/fpb/processed/fpb_allagree_test.jsonl`
- `data/fpb/processed/fpb_allagree_split_meta.json`
