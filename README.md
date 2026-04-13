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

Large data artifacts are **not** tracked in GitHub. Canonical processed artifacts are published to the Hugging Face dataset repo:
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

### 12) FLARE-MA Public Test v0
- **Dataset ID:** `flare_ma_public_test_v0`
- **Task ID:** `TA_MA_COMPLETENESS_FLARE_v0`
- **Task type:** eval-only binary deal-completeness classification
- **HF dataset path:** `datasets/flare_ma/public_test/v0/`
- **HF task path:** `tasks/flare_ma_deal_completeness_v0/`
- **Publish record:** `manifests/publish/flare_ma_public_test_v0_publish_record.json`
- **Labeling note:** canonical artifact is the already-public `TheFinAI/flare-ma` wrapper; only the public 500-example `test` split is onboarded; this module is eval-only and does not imply source clearance for the full original Zephyr-derived corpus.

### 13) FLARE-MLESG English Public Test v0
- **Dataset ID:** `flare_mlesg_en_public_test_v0`
- **Task ID:** `TA_ESG_ISSUE_MLESG_EN_FLARE_v0`
- **Task type:** eval-only multiclass ESG issue identification
- **HF dataset path:** `datasets/flare_mlesg/en_public_test/v0/`
- **HF task path:** `tasks/flare_mlesg_en_issue_v0/`
- **Publish record:** `manifests/publish/flare_mlesg_en_public_test_v0_publish_record.json`
- **Labeling note:** canonical artifact is the already-public `TheFinAI/flare-mlesg` wrapper; only the public 300-example `test` split is onboarded; the wrapper exposes 33 labels although the original ML-ESG paper describes a 35-issue task; this module is eval-only and does not imply source clearance for the full original English corpus.

### 14) DynamicESG ML-ESG-1 Chinese Official v0
- **Dataset ID:** `ml_esg1_zh_official_v0`
- **Task ID:** `TA_MLCLS_ML_ESG1_ZH_v0`
- **Task type:** Chinese headline-only multi-label ESG issue classification
- **HF dataset path:** `datasets/ml_esg1/zh_official/v0/`
- **HF task path:** `tasks/ml_esg1_zh_issue_v0/`
- **Publish record:** `manifests/publish/ml_esg1_zh_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `ymntseng/DynamicESG` ML-ESG-1 Chinese split release pinned to a concrete commit; official `train/dev/test` is preserved exactly; canonical text is the released headline only; labels are preserved as released multi-label code lists; the pinned release differs from the FinNLP 2023 workshop paper statistics and is treated as canonical with observed split counts `1058 / 118 / 131` and an observed 48-code inventory; family-stable `article_id` is included so ML-ESG-2 can later be onboarded as a separate published module.

### 15) DynamicESG ML-ESG-2 Chinese Official v0
- **Dataset ID:** `ml_esg2_zh_official_v0`
- **Task ID:** `TA_MLCLS_ML_ESG2_ZH_v0`
- **Task type:** Chinese headline-only 5-way single-label ESG impact type classification
- **HF dataset path:** `datasets/ml_esg2/zh_official/v0/`
- **HF task path:** `tasks/ml_esg2_zh_impact_type_v0/`
- **Publish record:** `manifests/publish/ml_esg2_zh_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `ymntseng/DynamicESG` ML-ESG-2 Chinese split release pinned to the same family commit as ML-ESG-1; official `train/dev/test` is preserved exactly; canonical text is the released headline only; the official 5-way impact type space is preserved exactly as `Opportunity`, `Risk`, `CannotDistinguish`, `NotRelatedtoCompany`, and `NotRelatedtoESGTopic`; `Impact_Type` is normalized from the released singleton list to a scalar canonical label while preserving the raw list in metadata.

<!-- ST312_PUBLISHED_MODULES_END -->

## Labeling / split notes

### FLARE-MLESG English Public Test

- Canonical artifact is the already-public `TheFinAI/flare-mlesg` wrapper
- Only the public 300-example `test` split is onboarded
- The wrapper shows 33 labels, although the original ML-ESG-1 paper describes a 35-issue task
- This module is eval-only and does not imply source clearance for the full original English corpus

### DynamicESG ML-ESG-1 Chinese Official

- Canonical source is the official `ymntseng/DynamicESG` ML-ESG-1 Chinese shared-task release pinned to a concrete Git commit
- Official `train / dev / test` split is preserved exactly
- Canonical text is headline only; no crawler enrichment or article-body recovery is included
- Labels are preserved exactly as released multi-label ESG code lists, including observed codes such as `NN`
- The pinned official release differs from the FinNLP 2023 workshop paper statistics; this module follows the pinned release as canonical with observed split counts `1058 / 118 / 131` and an observed 48-code inventory
- Future ML-ESG-2 onboarding is expected to remain a separate published module sharing family helpers and article_id semantics

### DynamicESG ML-ESG-2 Chinese Official

- Canonical source is the official `ymntseng/DynamicESG` ML-ESG-2 Chinese shared-task release pinned to the same family commit as ML-ESG-1
- Official `train / dev / test` split is preserved exactly
- Canonical text is headline only; no crawler enrichment or article-body recovery is included
- The official label space is preserved exactly as a 5-way single-label task: `Opportunity`, `Risk`, `CannotDistinguish`, `NotRelatedtoCompany`, `NotRelatedtoESGTopic`
- Upstream `Impact_Type` is stored as a singleton list and is normalized to a scalar canonical label while preserving the raw list in metadata
- Future ML-ESG-3 onboarding is expected to remain a separate published module sharing family helpers and article_id semantics

## Validation

Use:
`python scripts/utils/check_publish_records.py`

Target status convention:
- registry status: `published`
- dataset spec status: `"published_to_hf": true`

## Notes

This repository is designed so that new datasets/tasks can be added with the same structure and minimal ambiguity. The published-modules section above should remain the only top-level module index, to avoid drift and duplication.
