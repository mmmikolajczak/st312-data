---
pretty_name: "ST312 FinLLM Data Artifact Store"
viewer: false
license: "other"
tags:
- finance
- llm
- benchmark
- artifact-store
- heterogeneous
---

# ST312 FinLLM Data Artifact Store

Artifact repository for the ST312 Applied Statistics project (FinLLM pipeline).

This Hugging Face dataset repo stores canonical processed datasets, task request files, manifest snapshots, checksums, and publication bookkeeping artifacts.

This is a heterogeneous multi-module artifact store, not a single ordinary dataset repository.
The published contents index below is the source of truth for available modules and artifact paths.

## Structure

- `datasets/` — canonical processed dataset artifacts
- `tasks/` — task request JSONL files and task README snapshots
- `manifests/` — dataset/task specs, checksums, and publication bookkeeping
- `runs/` — reserved for completions / eval outputs (future)

## Viewer note

This repo is a multi-module artifact store rather than a single homogeneous dataset.
The default dataset viewer may be unavailable or misleading because the repository mixes many artifact types rather than one viewer-friendly dataset schema.
If the Hub page still shows a generic viewer pane or generic task tags, treat those as stale platform-level UI artifacts rather than the repository contract.
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

### 7) FinRED official v0

Dataset artifacts:
- `datasets/finred/official/v0/finred_official_all_clean.jsonl`
- `datasets/finred/official/v0/finred_official_train.jsonl`
- `datasets/finred/official/v0/finred_official_dev.jsonl`
- `datasets/finred/official/v0/finred_official_test.jsonl`
- `datasets/finred/official/v0/finred_official_clean_meta.json`
- `datasets/finred/official/v0/finred_official_split_meta.json`

Task requests:
- `tasks/finred_re_v0/finred_official_train_requests.jsonl`
- `tasks/finred_re_v0/finred_official_dev_requests.jsonl`
- `tasks/finred_re_v0/finred_official_test_requests.jsonl`

Task README snapshot:
- `tasks/finred_re_v0/README.md`

Publish bookkeeping:
- `manifests/publish/finred_official_v0_publish_record.json`

### 8) FinCausal 2020 official v0

Dataset artifacts:
- `datasets/fincausal2020/official/v0/fincausal2020_clean_meta.json`
- `datasets/fincausal2020/official/v0/fincausal2020_split_meta.json`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_all_clean.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_trial.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_practice.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_evaluation.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_all_clean.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_trial.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_practice.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_evaluation.jsonl`

Task requests:
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_trial_requests.jsonl`
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_practice_requests.jsonl`
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_evaluation_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_trial_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_practice_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_evaluation_requests.jsonl`

Task README snapshots:
- `tasks/fincausal2020_task1_sc_v0/README.md`
- `tasks/fincausal2020_task2_ce_v0/README.md`

Publish bookkeeping:
- `manifests/publish/fincausal2020_official_v0_publish_record.json`

### 9) FNXL Sharma 2023 v0

Dataset artifacts:
- `datasets/fnxl/sharma2023/v0/fnxl_release_raw_aggregate.jsonl`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_meta.json`
- `datasets/fnxl/sharma2023/v0/fnxl_label_inventory.json`
- `datasets/fnxl/sharma2023/v0/fnxl_label_id_mapping.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train.jsonl`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test.jsonl`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_manifest.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train_companies.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test_companies.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train_files.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test_files.json`

Task requests:
- `tasks/fnxl_numeric_labeling_v0/fnxl_train_requests.jsonl`
- `tasks/fnxl_numeric_labeling_v0/fnxl_test_requests.jsonl`

Task README snapshot:
- `tasks/fnxl_numeric_labeling_v0/README.md`

Publish bookkeeping:
- `manifests/publish/fnxl_sharma2023_v0_publish_record.json`

### 10) Gold Commodity News Kaggle Default v0

Dataset artifacts:
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean.csv`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean_meta.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_split_manifest.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train_urls.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test_urls.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train_headlines.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test_headlines.json`

Task requests:
- `tasks/gold_commodity_news_multilabel_v0/gold_commodity_news_train_requests.jsonl`
- `tasks/gold_commodity_news_multilabel_v0/gold_commodity_news_test_requests.jsonl`

Task README snapshot:
- `tasks/gold_commodity_news_multilabel_v0/README.md`

Auxiliary provenance report:
- `reports/gold_commodity_news/raw_audit_summary.json`

Publish bookkeeping:
- `manifests/publish/gold_commodity_news_kaggle_default_v0_publish_record.json`

### 11) Lamm 2018 TAP v0

Dataset artifacts:
- `datasets/tap/lamm2018/v0/all.jsonl`
- `datasets/tap/lamm2018/v0/train.jsonl`
- `datasets/tap/lamm2018/v0/test.jsonl`
- `datasets/tap/lamm2018/v0/split_meta.json`

Task requests:
- `tasks/lamm2018_tap_graph_v0/requests/train_requests.jsonl`
- `tasks/lamm2018_tap_graph_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/lamm2018_tap_graph_v0/README.md`

Publish bookkeeping:
- `manifests/publish/lamm2018_tap_v0_publish_record.json`


### 12) FLARE-MA Public Test v0

Dataset artifacts:
- `datasets/flare_ma/public_test/v0/test.jsonl`
- `datasets/flare_ma/public_test/v0/ingest_meta.json`

Task requests:
- `tasks/flare_ma_deal_completeness_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/flare_ma_deal_completeness_v0/README.md`

Publish bookkeeping:
- `manifests/publish/flare_ma_public_test_v0_publish_record.json`

### 13) FLARE-MLESG English Public Test v0

Dataset artifacts:
- `datasets/flare_mlesg/en_public_test/v0/test.jsonl`
- `datasets/flare_mlesg/en_public_test/v0/ingest_meta.json`

Task requests:
- `tasks/flare_mlesg_en_issue_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/flare_mlesg_en_issue_v0/README.md`

Publish bookkeeping:
- `manifests/publish/flare_mlesg_en_public_test_v0_publish_record.json`

### 14) DynamicESG ML-ESG-1 Chinese Official v0

Dataset artifacts:
- `datasets/ml_esg1/zh_official/v0/train.jsonl`
- `datasets/ml_esg1/zh_official/v0/dev.jsonl`
- `datasets/ml_esg1/zh_official/v0/test.jsonl`
- `datasets/ml_esg1/zh_official/v0/label_inventory.json`
- `datasets/ml_esg1/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg1/zh_official/v0/download_meta.json`

Task requests:
- `tasks/ml_esg1_zh_issue_v0/requests/train_requests.jsonl`
- `tasks/ml_esg1_zh_issue_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg1_zh_issue_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/ml_esg1_zh_issue_v0/README.md`

Auxiliary provenance report:
- `reports/ml_esg1_zh_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/ml_esg1_zh_official_v0_publish_record.json`

### 15) DynamicESG ML-ESG-2 Chinese Official v0

Dataset artifacts:
- `datasets/ml_esg2/zh_official/v0/train.jsonl`
- `datasets/ml_esg2/zh_official/v0/dev.jsonl`
- `datasets/ml_esg2/zh_official/v0/test.jsonl`
- `datasets/ml_esg2/zh_official/v0/label_inventory.json`
- `datasets/ml_esg2/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg2/zh_official/v0/download_meta.json`

Task requests:
- `tasks/ml_esg2_zh_impact_type_v0/requests/train_requests.jsonl`
- `tasks/ml_esg2_zh_impact_type_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg2_zh_impact_type_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/ml_esg2_zh_impact_type_v0/README.md`

Auxiliary provenance report:
- `reports/ml_esg2_zh_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/ml_esg2_zh_official_v0_publish_record.json`

### 16) DynamicESG ML-ESG-3 Chinese Official v0

Dataset artifacts:
- `datasets/ml_esg3/zh_official/v0/train.jsonl`
- `datasets/ml_esg3/zh_official/v0/dev.jsonl`
- `datasets/ml_esg3/zh_official/v0/test.jsonl`
- `datasets/ml_esg3/zh_official/v0/label_inventory.json`
- `datasets/ml_esg3/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg3/zh_official/v0/download_meta.json`

Task requests:
- `tasks/ml_esg3_zh_impact_duration_v0/requests/train_requests.jsonl`
- `tasks/ml_esg3_zh_impact_duration_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg3_zh_impact_duration_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/ml_esg3_zh_impact_duration_v0/README.md`

Auxiliary provenance report:
- `reports/ml_esg3_zh_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/ml_esg3_zh_official_v0_publish_record.json`

### 17) FinQA Official v0

Dataset artifacts:
- `datasets/finqa/official/v0/train.jsonl`
- `datasets/finqa/official/v0/dev.jsonl`
- `datasets/finqa/official/v0/test.jsonl`
- `datasets/finqa/official/v0/label_inventory.json`
- `datasets/finqa/official/v0/ingest_summary.json`
- `datasets/finqa/official/v0/download_meta.json`
- `datasets/finqa/official/v0/private_test_summary.json`

Task requests:
- `tasks/finqa_program_generation_v0/requests/train_requests.jsonl`
- `tasks/finqa_program_generation_v0/requests/dev_requests.jsonl`
- `tasks/finqa_program_generation_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/finqa_program_generation_v0/README.md`

Publish bookkeeping:
- `manifests/publish/finqa_official_v0_publish_record.json`

### 18) TAT-QA Official v0

Dataset artifacts:
- `datasets/tatqa/official/v0/train.jsonl`
- `datasets/tatqa/official/v0/dev.jsonl`
- `datasets/tatqa/official/v0/test.jsonl`
- `datasets/tatqa/official/v0/label_inventory.json`
- `datasets/tatqa/official/v0/ingest_summary.json`
- `datasets/tatqa/official/v0/download_meta.json`
- `datasets/tatqa/official/v0/original_test_summary.json`

Task requests:
- `tasks/tatqa_hybrid_qa_structured_v0/requests/train_requests.jsonl`
- `tasks/tatqa_hybrid_qa_structured_v0/requests/dev_requests.jsonl`
- `tasks/tatqa_hybrid_qa_structured_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/tatqa_hybrid_qa_structured_v0/README.md`

Auxiliary provenance report:
- `reports/tatqa_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/tatqa_official_v0_publish_record.json`

### 19) ConvFinQA Official v0

Dataset artifacts:
- `datasets/convfinqa/official/v0/train.jsonl`
- `datasets/convfinqa/official/v0/dev.jsonl`
- `datasets/convfinqa/official/v0/label_inventory.json`
- `datasets/convfinqa/official/v0/ingest_summary.json`
- `datasets/convfinqa/official/v0/download_meta.json`
- `datasets/convfinqa/official/v0/test_release_summary.json`

Task requests:
- `tasks/convfinqa_program_generation_v0/requests/train_requests.jsonl`
- `tasks/convfinqa_program_generation_v0/requests/dev_requests.jsonl`

Task README snapshot:
- `tasks/convfinqa_program_generation_v0/README.md`

Auxiliary provenance report:
- `reports/convfinqa_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/convfinqa_official_v0_publish_record.json`

### 20) FinBen Regulations Public Test v0

Dataset artifacts:
- `datasets/regulations/public_test/v0/test.jsonl`
- `datasets/regulations/public_test/v0/ingest_summary.json`
- `datasets/regulations/public_test/v0/download_meta.json`

Task requests:
- `tasks/regulations_longform_qa_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/regulations_longform_qa_v0/README.md`

Auxiliary provenance report:
- `reports/regulations_public_test/raw_schema_summary.json`

Publish bookkeeping:
- `manifests/publish/regulations_public_test_v0_publish_record.json`

### 21) ECTSum Official v0

Dataset artifacts:
- `datasets/ectsum/official/v0/train.jsonl`
- `datasets/ectsum/official/v0/val.jsonl`
- `datasets/ectsum/official/v0/test.jsonl`
- `datasets/ectsum/official/v0/ingest_summary.json`
- `datasets/ectsum/official/v0/download_meta.json`

Task requests:
- `tasks/ectsum_bullet_summarization_v0/requests/train_requests.jsonl`
- `tasks/ectsum_bullet_summarization_v0/requests/val_requests.jsonl`
- `tasks/ectsum_bullet_summarization_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/ectsum_bullet_summarization_v0/README.md`

Auxiliary provenance report:
- `reports/ectsum_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/ectsum_official_v0_publish_record.json`

### 22) FLARE-EDTSUM Public Test v0

Dataset artifacts:
- `datasets/flare_edtsum/public_test/v0/test.jsonl`
- `datasets/flare_edtsum/public_test/v0/ingest_summary.json`
- `datasets/flare_edtsum/public_test/v0/download_meta.json`

Task requests:
- `tasks/flare_edtsum_headline_generation_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/flare_edtsum_headline_generation_v0/README.md`

Auxiliary provenance report:
- `reports/flare_edtsum_public_test/raw_schema_summary.json`

Publish bookkeeping:
- `manifests/publish/flare_edtsum_public_test_v0_publish_record.json`

### 23) BigData22 Official v0

Dataset artifacts:
- `datasets/bigdata22/official/v0/train.jsonl`
- `datasets/bigdata22/official/v0/valid.jsonl`
- `datasets/bigdata22/official/v0/test.jsonl`
- `datasets/bigdata22/official/v0/label_inventory.json`
- `datasets/bigdata22/official/v0/ingest_summary.json`
- `datasets/bigdata22/official/v0/download_meta.json`

Task requests:
- `tasks/bigdata22_stock_movement_v0/requests/train_requests.jsonl`
- `tasks/bigdata22_stock_movement_v0/requests/valid_requests.jsonl`
- `tasks/bigdata22_stock_movement_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/bigdata22_stock_movement_v0/README.md`

Auxiliary provenance reports:
- `reports/bigdata22_official/raw_schema_summary.json`
- `reports/bigdata22_official/ingest_audit.json`

Publish bookkeeping:
- `manifests/publish/bigdata22_official_v0_publish_record.json`

Rights note:
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

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

### FinRED official

- Original author split preserved: `train/dev/test`
- Train/dev are weakly supervised via distant supervision
- Test is the higher-trust manual evaluation split
- Relation inventory contains 29 canonical relations

### FinCausal 2020 official

- Original `trial / practice / evaluation` structure preserved
- Task 1 blank-text rows removed during ingestion
- Task 2 stored row-wise as cause/effect-pair extraction
- Evaluation is blind for both tasks
- Official scorer scripts define evaluation semantics

### FNXL Sharma 2023

- Raw release preserved in full for provenance
- Original released train/dev/test split archived but not used as canonical evaluation because it leaks across companies and filing paths
- Canonical split rebuilt as grouped 80/20 company/file-disjoint train/test
- `allLabelCount.csv` treated as authoritative label inventory
- Canonical prediction target is sparse `(token_index, label_id)` over observed used FNXL label IDs

### Gold Commodity News Kaggle Default

- Canonical source is the `daittan` Kaggle posting, chosen because it matches the paper-era row count and original 9-label schema
- `ankurzing` posting is retained only as a later derivative provenance reference
- Exact duplicate rows removed in the cleaned layer; duplicate headlines and URLs retained for grouped leakage control
- Dates repaired deterministically with `0200→2000` and `0201→2001`, yielding full parse success
- Canonical split rebuilt as grouped 80/20 over connected components of normalized URL and normalized headline
- Task is strict 9-way binary multi-label headline classification with `price_or_not_norm` as a derived normalized parent label

### Lamm 2018 TAP

- Author split preserved from the released repo snapshot: `train=1000`, `test=97`
- Canonical benchmark target is the reduced active graph label inventory from the author code path
- Canonical processed artifacts are published in this HF repo under the normal pipeline schema
- Approval for public redistribution remains pending


### FLARE-MA Public Test

- Canonical artifact is the already-public `TheFinAI/flare-ma` wrapper
- Only the public 500-example `test` split is onboarded
- This module is eval-only and does not imply source clearance for the full original Zephyr-derived corpus
- Canonical evaluation metrics are accuracy, macro F1, and MCC

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

### DynamicESG ML-ESG-2 Chinese Official

- Canonical source is the official `ymntseng/DynamicESG` ML-ESG-2 Chinese shared-task release pinned to the same family commit as ML-ESG-1
- Official `train / dev / test` split is preserved exactly
- Canonical text is headline only; no crawler enrichment or article-body recovery is included
- The official label space is preserved exactly as a 5-way single-label task: `Opportunity`, `Risk`, `CannotDistinguish`, `NotRelatedtoCompany`, `NotRelatedtoESGTopic`
- Upstream `Impact_Type` is stored as a singleton list and is normalized to a scalar canonical label while preserving the raw list in metadata
- Family-stable `article_id` supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules

### DynamicESG ML-ESG-3 Chinese Official

- Canonical source is the official `ymntseng/DynamicESG` ML-ESG-3 Chinese shared-task release pinned to the same family commit as ML-ESG-1 and ML-ESG-2
- Official `train / dev / test` split is preserved exactly
- Canonical text is headline only; no crawler enrichment or article-body recovery is included
- The released label space is preserved exactly as a 5-way single-label task: `<2`, `2~5`, `>5`, `NotRelatedtoCompany`, `NotRelatedtoESGTopic`
- Upstream `Impact_Duration` is stored as a singleton list and is normalized to a scalar canonical label while preserving the raw list in metadata
- The pinned released JSON is treated as canonical even though workshop materials present a narrower 3-duration-label framing

### FinQA Official

- Canonical source is the official `czyssrs/FinQA` GitHub repo pinned to a concrete commit because the repo has no tagged releases
- The pinned source commit is chosen from a repo state that includes the documented 2022 reproducibility bugfix notes from the official README
- Canonical public supervised splits are `train / dev / test`
- `private_test.json` is kept raw for provenance only and is excluded from the supervised canonical publication because it has no references; only a tiny non-sensitive `private_test_summary.json` provenance artifact is published
- Canonical target is executable program generation in the FinQA DSL, not answer-only QA
- Canonical evaluation prioritizes execution accuracy, with program accuracy as the secondary metric
- The official repo is MIT-licensed; the Hugging Face mirror metadata differs and is not treated as canonical

### TAT-QA Official

- Canonical source is the official `NExTplusplus/TAT-QA` GitHub repo pinned to commit `644770eb2a66dddc24b92303bd2acbad84cd2b9f`
- Canonical processed `train / dev / test` preserves the official hybrid-context split, with `test.jsonl` derived from `tatqa_dataset_test_gold.json`
- The original unlabeled `tatqa_dataset_test.json` is retained raw-only for provenance and summarized separately as `original_test_summary.json`
- Hybrid context is preserved per question as the raw table plus ordered paragraphs, with deterministic prompt serializations
- Rich supervision fields are preserved in processed rows, but the canonical benchmark contract remains official answer+scale scoring with `exact_match`, `f1`, and `scale_score`
- The dataset content is CC BY 4.0, while the repository code and official scorer scripts are MIT-licensed

### ConvFinQA Official

- Canonical source is the official `czyssrs/ConvFinQA` GitHub repo pinned to commit `cf3eed2d5984960bf06bb8145bcea5e80b0222a6`
- ConvFinQA is a FinQA-family conversational derivative, so training on FinQA plus ConvFinQA does not add fully independent source evidence
- Canonical processed rows are turn-level and preserve dialogue history, `pre_text`, raw table, and `post_text`
- Canonical public supervised splits are `train / dev`; the pinned release exposes only unlabeled private test files, which are retained raw-only and summarized separately as `test_release_summary.json`
- Canonical target is executable program generation in the FinQA DSL, not answer-only conversational QA
- Canonical evaluation prioritizes execution accuracy, with program accuracy as the secondary metric

### FinBen Regulations Public Test

- Canonical source is the gated `TheFinAI/regulations` Hugging Face dataset pinned to revision `918111376d5be0f97306f1e0b821529b4021da0b`
- Authenticated inspection exposed only `README.md` and `test_regulations.json`; no public `train / dev` release was found
- Canonical publication is eval-only `test` only, with no fabricated supervised training split
- The wrapper exposes only `id`, `query`, `answer`, and `text`; canonical `question` uses `text`, while prompt-prefixed `query` is preserved as `source_query`
- No explicit context, jurisdiction, regulation document, or source section fields are present in the released wrapper
- Canonical evaluation is best-faith paper-aligned long-form QA scoring with ROUGE and BERTScore

### ECTSum Official

- Canonical source is the official `rajdeep345/ECTSum` GitHub repo pinned to commit `6909f1fc543104c1c60cf9de63e799f6620d1b0a`
- Official `train / val / test` prepared-remarks transcript-summary pairs are preserved exactly, with observed counts `1681 / 249 / 495`
- Canonical task is original-paper bullet-style summarization; the default evaluator is original ECTSum and the FinBen-style summarization evaluator is optional
- Source chain involves Motley Fool transcripts and Reuters summaries
- Publication is carried in the normal artifact layout as a public artifact with an upstream licensing and redistribution caution

### FLARE-EDTSUM Public Test

- Canonical source is the gated `TheFinAI/flare-edtsum` Hugging Face dataset pinned to revision `e37154379a3162faf9d7b7a9cd1d582f2ae19adb`
- Authenticated inspection exposed only a single `test` split with `2000` rows and fields `id`, `query`, `answer`, and `text`
- Canonical task framing is financial news headline generation, or headline-style abstractive summarization, rather than generic paragraph summarization
- Canonical processed rows preserve the wrapper fields and add `article_text` plus `reference_headline`
- Stable default evaluation uses ROUGE plus BERTScore; the FinBen-paper-aligned view adds best-effort BARTScore
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

### BigData22 Official

- Canonical source is the official `deeptrade-public/slot` GitHub repo pinned to commit `1c1a25671d4c81f5fcd45607447225862c308dd5`
- The bundled `data.zip` archive contains `bigdata22`, `acl18`, and `cikm18`; only `bigdata22` is onboarded as the canonical module in this turn
- Canonical paper-window scope is `2019-07-05` through `2020-06-30`, which matches the paper's reported `272,762` tweet lines and 362-day calendar span
- Canonical labels are taken directly from the release: `1 -> Rise`, `-1 -> Fall`, and the neutral band `0` is excluded from the binary task
- The official archive does not ship split files or cut dates, so ST312 reconstructs a documented chronological `70 / 10 / 20` `train / valid / test` partition over the paper window, yielding `5624 / 1117 / 2063` examples
- Canonical evaluation uses `mcc` as the primary metric and `accuracy` as the secondary metric
- The public FinBen/OpenFinLLM-style wrapper is treated as a derived comparison surface rather than the source of truth because its counts and date range differ from the official paper-window release
- Publication is public but carries an upstream rights caution because the repo surface does not expose a clear redistribution license for the tweets and market data

## Licensing

Licensing metadata is recorded in each dataset manifest under:
- `manifests/datasets/<dataset_id>/dataset_spec.json`

Please consult upstream licenses before any public redistribution or commercial use.
