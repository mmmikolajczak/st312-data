# FinBen FINER-ORD Dataset (v0)

Dataset module for token-level NER tagging (BIO format) from the FinBen FINER-ORD dataset.

## Dataset ID
`finben_finer_ord_v0`

## Upstream source
- Current source used: `TheFinAI/finben-finer-ord` (FinBen mirror)
- Note: we may later compare/rebuild from the original larger source (`gtfintechlab/finer-ord`)

## Canonical processed files
- `data/finer_ord/processed/finben_finer_ord_all_clean.jsonl`
- `data/finer_ord/processed/finben_finer_ord_train.jsonl`
- `data/finer_ord/processed/finben_finer_ord_test.jsonl`

## Labels (BIO)
- `O`
- `B-PER`, `I-PER`
- `B-LOC`, `I-LOC`
- `B-ORG`, `I-ORG`

## Split policy
Local stratified 80/20 train/test split (seed=42), stratified on sentence-level entity signature (`meta.label_signature`).

## Meta files
- `data/finer_ord/processed/finben_finer_ord_clean_meta.json`
- `data/finer_ord/processed/finben_finer_ord_split_meta.json`
