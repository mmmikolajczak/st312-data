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

This repository is the **code + metadata control plane** for the Risko-1 style dataset/task pipeline:
- dataset ingestion, cleaning, normalisation, and split scripts
- task specs, prompt templates, reward parsers, and cached evaluators
- dataset/task registries and manifest snapshots for reproducibility
- publish records and checksums for GitHub/Hugging Face bookkeeping

Large data artifacts are **not** tracked in GitHub. Canonical processed artifacts are published to the private Hugging Face dataset repo:
- `mmmikolajczak/st312-data`

## Repository architecture

### `datasets/`
Dataset modules (metadata only):
- dataset README
- dataset spec
- checksums for canonical processed artifacts
- dataset registry: `datasets/dataset_registry.json`

### `tasks/`
Task modules (metadata only):
- task README
- task spec
- task registry: `tasks/task_registry.json`

### `scripts/datasets/<dataset>/`
Dataset-level pipeline scripts:
- ingestion
- cleaning / normalization
- splitting (if needed)

### `scripts/tasks/<task_module>/`
Task-level scripts:
- reward parser
- prompt renderer
- request builder
- cached evaluator

### `manifests/`
Snapshot + bookkeeping layer:
- `manifests/datasets/...` — dataset spec snapshots + checksums
- `manifests/tasks/...` — task spec snapshots
- `manifests/publish/...` — publish records with GitHub / HF commit history
- `manifests/hf_repo/README.md` — source-of-truth text for HF repo-facing README updates

### `data/`
Local-only working artifacts (ignored by Git):
- raw downloads
- processed JSONL files
- generated request files
- previews / dummy completions

### `reports/`
Evaluation outputs (JSON reports, cached eval summaries, etc.)

## Reproducibility conventions

GitHub tracks **metadata, manifests, and checksums**.  
Hugging Face stores the **canonical processed artifacts and request files**.

Every published dataset/task module should have:
- dataset/task README
- dataset/task spec
- manifest snapshot(s)
- checksums
- publish record with HF commit hashes
- registry entries marked consistently
- successful validation via:
  - `python scripts/utils/check_publish_records.py`

## Standard workflow for a new dataset

1. Add dataset ingestion/cleaning scripts under `scripts/datasets/<dataset>/`
2. Produce local processed artifacts under `data/<dataset>/processed/`
3. Add dataset module under `datasets/<dataset_module>/`
4. Add task module under `tasks/<task_module>/`
5. Add task scripts under `scripts/tasks/<task_module>/`
6. Build request files
7. Snapshot manifests + checksums
8. Upload canonical artifacts to HF
9. Add publish record
10. Push GitHub metadata/manifests
11. Validate with `python scripts/utils/check_publish_records.py`

## Published dataset/task modules

This is the **single canonical index** of published modules in the repository.  
When a new module is published, append it here and keep the same pattern.

<!-- ST312_PUBLISHED_MODULES_START -->

Canonical HF dataset repo: `mmmikolajczak/st312-data`

### 1) Financial PhraseBank (all-agree) v0
- **Dataset ID:** `fpb_allagree_v0`
- **Task ID:** `TA_SENT_FPB_v0`
- **Task type:** 3-way sentiment classification
- **HF dataset path:** `datasets/fpb/allagree/v0/`
- **HF task path:** `tasks/fpb_sentiment_v0/`
- **Publish record:** `manifests/publish/fpb_allagree_v0_publish_record.json`

### 2) FiQA-SA (HF default split) v0
- **Dataset ID:** `fiqasa_hf_default_v0`
- **Task ID:** `TA_SENT_FIQASA_v0`
- **Task type:** 3-way sentiment classification
- **HF dataset path:** `datasets/fiqasa/default/v0/`
- **HF task path:** `tasks/fiqasa_sentiment_v0/`
- **Publish record:** `manifests/publish/fiqasa_hf_default_v0_publish_record.json`
- **Labeling note:** discretised from continuous sentiment score using:
  - `score <= -0.1` → `negative`
  - `score >= 0.1` → `positive`
  - otherwise → `neutral`

### 3) FinBen FOMC v0
- **Dataset ID:** `finben_fomc_v0`
- **Task ID:** `TA_STANCE_FOMC_FINBEN_v0`
- **Task type:** 3-way monetary-policy stance classification
- **HF dataset path:** `datasets/fomc/finben/v0/`
- **HF task path:** `tasks/finben_fomc_stance_v0/`
- **Publish record:** `manifests/publish/finben_fomc_v0_publish_record.json`

### 4) FinBen FINER-ORD v0
- **Dataset ID:** `finben_finer_ord_v0`
- **Task ID:** `TA_NER_FINER_ORD_FINBEN_v0`
- **Task type:** BIO-format token classification (NER)
- **HF dataset path:** `datasets/finer_ord/finben/v0/`
- **HF task path:** `tasks/finben_finer_ord_ner_v0/`
- **Publish record:** `manifests/publish/finben_finer_ord_v0_publish_record.json`

### 5) MultiFin high-level v0
- **Dataset ID:** `multifin_highlevel_v0`
- **Task ID:** `TA_TOPIC_MULTIFIN_HIGHLEVEL_v0`
- **Task type:** 6-class topic classification
- **HF dataset path:** `datasets/multifin/highlevel/v0/`
- **HF task path:** `tasks/multifin_highlevel_topic_v0/`
- **Publish record:** `manifests/publish/multifin_highlevel_v0_publish_record.json`

<!-- ST312_PUBLISHED_MODULES_END -->

### 6) Salinas SEC loan-agreement NER v0
- **Dataset ID:** `salinas_sec_loan_ner_v0`
- **Task ID:** `TA_NER_SEC_LOAN_SALINAS_v0`
- **Task type:** BIO2 token classification (NER)
- **HF dataset path:** `datasets/sec_loan_ner/salinas/v0/`
- **HF task path:** `tasks/salinas_sec_loan_ner_v0/`
- **Publish record:** `manifests/publish/salinas_sec_loan_ner_v0_publish_record.json`
- **Labeling note:** original author split preserved (`FIN5` train / `FIN3` test); entity set retains `PER`, `LOC`, `ORG`, `MISC`, and preserves the corpus-specific `lender`/`borrower` -> `PER` convention.

### 7) FinRED official v0
- **Dataset ID:** `finred_official_v0`
- **Task ID:** `TA_RE_FINRED_v0`
- **Task type:** joint relation / triplet extraction
- **HF dataset path:** `datasets/finred/official/v0/`
- **HF task path:** `tasks/finred_re_v0/`
- **Publish record:** `manifests/publish/finred_official_v0_publish_record.json`
- **Labeling note:** author `train/dev/test` split preserved; `train/dev` are weakly supervised via distant supervision, while `test` is the higher-trust manual evaluation split. Relation inventory contains 29 relations.

### 8) FinCausal 2020 official v0
- **Dataset ID:** `fincausal2020_official_v0`
- **Task IDs:** `TA_CAUSAL_CLASSIFY_FINCAUSAL2020_v0`, `TA_CAUSE_EFFECT_FINCAUSAL2020_v0`
- **Task types:** binary causal classification; cause/effect span extraction
- **HF dataset path:** `datasets/fincausal2020/official/v0/`
- **HF task paths:** `tasks/fincausal2020_task1_sc_v0/`, `tasks/fincausal2020_task2_ce_v0/`
- **Publish record:** `manifests/publish/fincausal2020_official_v0_publish_record.json`
- **Labeling note:** official `trial / practice / evaluation` structure preserved; Task 1 blank-text rows removed during ingestion; Task 2 stored row-wise as cause/effect-pair extraction; evaluation is blind for both tasks.

### 9) FNXL Sharma 2023 v0
- **Dataset ID:** `fnxl_sharma2023_v0`
- **Task ID:** `TA_IE_NUMERIC_LABEL_FNXL_v0`
- **Task type:** numeric labelling / extreme token classification
- **HF dataset path:** `datasets/fnxl/sharma2023/v0/`
- **HF task path:** `tasks/fnxl_numeric_labeling_v0/`
- **Publish record:** `manifests/publish/fnxl_sharma2023_v0_publish_record.json`
- **Labeling note:** raw release preserved; original release split archived for provenance only because it leaks across companies and filing paths; canonical split rebuilt as clean grouped 80/20 company/file-disjoint train/test; task predicts sparse `(token_index, label_id)` pairs over the observed used FNXL ID space.

### 10) Gold Commodity News Kaggle Default v0
- **Dataset ID:** `gold_commodity_news_kaggle_default_v0`
- **Task ID:** `TA_MLC_GOLD_COMMODITY_NEWS_v0`
- **Task type:** 9-way binary multi-label headline classification
- **HF dataset path:** `datasets/gold_commodity_news/kaggle_default/v0/`
- **HF task path:** `tasks/gold_commodity_news_multilabel_v0/`
- **Publish record:** `manifests/publish/gold_commodity_news_kaggle_default_v0_publish_record.json`
- **Labeling note:** canonical source is the `daittan` Kaggle posting matching the paper-era row count and schema; exact duplicate rows were removed; dates were deterministically normalized (`0200→2000`, `0201→2001`); canonical split is grouped 80/20 over connected components of normalized URL and normalized headline; derivative `ankurzing` file is provenance-only.

### 11) Lamm 2018 TAP v0
- **Dataset ID:** `lamm2018_tap_v0`
- **Task ID:** `TA_GRAPH_TAP_LAMM2018_v0`
- **Task type:** structured graph prediction / textual analogy parsing
- **HF dataset path:** `datasets/tap/lamm2018/v0/`
- **HF task path:** `tasks/lamm2018_tap_graph_v0/`
- **Publish record:** `manifests/publish/lamm2018_tap_v0_publish_record.json`
- **Labeling note:** author split preserved as released (`train=1000`, `test=97` in the public repo snapshot); benchmark target uses the reduced active graph label inventory from the author code path; public redistribution approval remains pending.

### 11) Lamm 2018 TAP v0
- **Dataset ID:** `lamm2018_tap_v0`
- **Task ID:** `TA_GRAPH_TAP_LAMM2018_v0`
- **Task type:** structured graph prediction / textual analogy parsing
- **HF dataset path:** `datasets/tap/lamm2018/v0/`
- **HF task path:** `tasks/lamm2018_tap_graph_v0/`
- **Publish record:** `manifests/publish/lamm2018_tap_v0_publish_record.json`
- **Labeling note:** author split preserved as released (`train=1000`, `test=97` in the public repo snapshot); benchmark target uses the reduced active graph label inventory from the author code path; public redistribution approval remains pending.

### 11) Lamm 2018 TAP v0
- **Dataset ID:** `lamm2018_tap_v0`
- **Task ID:** `TA_GRAPH_TAP_LAMM2018_v0`
- **Task type:** structured graph prediction / textual analogy parsing
- **HF dataset path:** `datasets/tap/lamm2018/v0/`
- **HF task path:** `tasks/lamm2018_tap_graph_v0/`
- **Publish record:** `manifests/publish/lamm2018_tap_v0_publish_record.json`
- **Labeling note:** author split preserved as released (`train=1000`, `test=97` in the public repo snapshot); benchmark target uses the reduced active graph label inventory from the author code path; public redistribution approval remains pending.

## Validation

Use:
`python scripts/utils/check_publish_records.py`

Target status convention:
- registry status: `published`
- dataset spec status: `"published_to_hf": true`

## Notes

This repository is designed so that new datasets/tasks can be added with the same structure and minimal ambiguity. The published-modules section above should remain the only top-level module index, to avoid drift and duplication.

