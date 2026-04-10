# Cortis 2017 TSA Dataset (v0)

Dataset module for SemEval-2017 Task 5, Subtask 2:
target-aware fine-grained sentiment on financial news headlines / statements.

## Dataset ID
`cortis2017_tsa_v0`

## Canonical acquisition
Use the official SemEval release path only.

1. Complete the official Subtask 2 data release agreement.
2. Download the official Subtask 2 files from the official repository.
3. Request the held-out gold standard via the official form/email route.
4. Place the files in `data/cortis2017_tsa/raw/` using the exact names below.

## Raw file contract
Required:
- `Headline_Trainingdata.json`
- `Headline_Trialdata.json`
- `Headlines_Testdata.json`

Optional until organizer GS is received:
- `Headlines_Test_GS.json`

## Canonical processed outputs
- `data/cortis2017_tsa/processed/cortis2017_tsa_train.jsonl`
- `data/cortis2017_tsa/processed/cortis2017_tsa_trial.jsonl`
- `data/cortis2017_tsa/processed/cortis2017_tsa_test_inputs.jsonl`
- `data/cortis2017_tsa/processed/cortis2017_tsa_test_scored.jsonl` (only if GS is present)
- `data/cortis2017_tsa/processed/cortis2017_tsa_all_labeled.jsonl`
- `data/cortis2017_tsa/processed/cortis2017_tsa_clean_meta.json`
- `data/cortis2017_tsa/processed/cortis2017_tsa_split_meta.json`

## Canonical row shape
Each row is one `(headline, target_company)` example and keeps both raw and normalized fields:
- `example_id`
- `split`
- `source_dataset`
- `task_family`
- `data.title_raw`
- `data.title_normalized`
- `data.target_company_raw`
- `data.target_company_normalized`
- `label.sentiment_score` (for labeled splits)
- `provenance.*`

## Notes
- Preserve raw text untouched.
- Clean only into derived normalized fields.
- Do not deduplicate by title alone.
- Preserve official `train / trial / test` semantics.
- Treat redistribution rights as unresolved until explicitly verified.
