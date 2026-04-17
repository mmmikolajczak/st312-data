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
This Hugging Face dataset repo stores canonical processed datasets, task request files,
manifest snapshots, checksums, and publication bookkeeping artifacts.

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

### 1) Financial PhraseBank (all-agree) v0

- Dataset ID: `fpb_allagree_v0`
- Task ID: `TA_SENT_FPB_v0`
- Publish record: `manifests/publish/fpb_allagree_v0_publish_record.json`
- Notes: FPB all-agree v0 bootstrap completed; upstream license metadata set to CC BY-NC-SA 3.0.

Dataset artifacts:
- `datasets/fpb/allagree/v0/train.jsonl`
- `datasets/fpb/allagree/v0/test.jsonl`
- `datasets/fpb/allagree/v0/split_meta.json`

Task artifacts:
- `tasks/fpb_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fpb_sentiment_v0/requests/test_requests.jsonl`
- `tasks/fpb_sentiment_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/fpb_allagree_v0/dataset_spec.json`
- `manifests/tasks/fpb_sentiment_v0/task_spec.json`

### 2) FiQA-SA (HF default split) v0

- Dataset ID: `fiqasa_hf_default_v0`
- Task ID: `TA_SENT_FIQASA_v0`
- Publish record: `manifests/publish/fiqasa_hf_default_v0_publish_record.json`
- Notes: FiQA-SA v0 pipeline completed with upstream split preserved and 3-way discretised labels.

Dataset artifacts:
- `datasets/fiqasa/default/v0/train.jsonl`
- `datasets/fiqasa/default/v0/valid.jsonl`
- `datasets/fiqasa/default/v0/test.jsonl`
- `datasets/fiqasa/default/v0/clean_meta.json`

Task artifacts:
- `tasks/fiqasa_sentiment_v0/requests/train_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/valid_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/requests/test_requests.jsonl`
- `tasks/fiqasa_sentiment_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/fiqasa_hf_default_v0/dataset_spec.json`
- `manifests/datasets/fiqasa_hf_default_v0/checksums.sha256`
- `manifests/tasks/fiqasa_sentiment_v0/task_spec.json`

### 3) FinBen FOMC

- Dataset ID: `finben_fomc_v0`
- Task ID: `TA_STANCE_FOMC_FINBEN_v0`
- Publish record: `manifests/publish/finben_fomc_v0_publish_record.json`
- Notes: FinBen FOMC v0 pipeline completed with local stratified 80/20 train/test split (seed=42).

Dataset artifacts:
- `datasets/fomc/finben/v0/all_clean.jsonl`
- `datasets/fomc/finben/v0/train.jsonl`
- `datasets/fomc/finben/v0/test.jsonl`
- `datasets/fomc/finben/v0/clean_meta.json`
- `datasets/fomc/finben/v0/split_meta.json`

Task artifacts:
- `tasks/finben_fomc_stance_v0/requests/train_requests.jsonl`
- `tasks/finben_fomc_stance_v0/requests/test_requests.jsonl`
- `tasks/finben_fomc_stance_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finben_fomc_v0/dataset_spec.json`
- `manifests/datasets/finben_fomc_v0/checksums.sha256`
- `manifests/tasks/finben_fomc_stance_v0/task_spec.json`

### 4) FinBen FINER-ORD

- Dataset ID: `finben_finer_ord_v0`
- Task ID: `TA_NER_FINER_ORD_FINBEN_v0`
- Publish record: `manifests/publish/finben_finer_ord_v0_publish_record.json`
- Notes: FINER-ORD v0 pipeline completed with local stratified 80/20 split (seed=42, stratify_on=meta.label_signature). NER reward upgraded to shaped span-F1 + token-acc + exact-match bonus.

Dataset artifacts:
- `datasets/finer_ord/finben/v0/all_clean.jsonl`
- `datasets/finer_ord/finben/v0/train.jsonl`
- `datasets/finer_ord/finben/v0/test.jsonl`
- `datasets/finer_ord/finben/v0/clean_meta.json`
- `datasets/finer_ord/finben/v0/split_meta.json`

Task artifacts:
- `tasks/finben_finer_ord_ner_v0/requests/train_requests.jsonl`
- `tasks/finben_finer_ord_ner_v0/requests/test_requests.jsonl`
- `tasks/finben_finer_ord_ner_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finben_finer_ord_v0/dataset_spec.json`
- `manifests/datasets/finben_finer_ord_v0/checksums.sha256`
- `manifests/tasks/finben_finer_ord_ner_v0/task_spec.json`

### 5) MultiFin High-Level Topic Classification

- Dataset ID: `multifin_highlevel_v0`
- Task ID: `TA_TOPIC_MULTIFIN_HIGHLEVEL_v0`
- Publish record: `manifests/publish/multifin_highlevel_v0_publish_record.json`
- Notes: MultiFin high-level v0 pipeline completed with upstream train/validation/test split preserved.

Dataset artifacts:
- `datasets/multifin/highlevel/v0/train.jsonl`
- `datasets/multifin/highlevel/v0/validation.jsonl`
- `datasets/multifin/highlevel/v0/test.jsonl`
- `datasets/multifin/highlevel/v0/clean_meta.json`

Task artifacts:
- `tasks/multifin_highlevel_topic_v0/requests/train_requests.jsonl`
- `tasks/multifin_highlevel_topic_v0/requests/validation_requests.jsonl`
- `tasks/multifin_highlevel_topic_v0/requests/test_requests.jsonl`
- `tasks/multifin_highlevel_topic_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/multifin_highlevel_v0/dataset_spec.json`
- `manifests/datasets/multifin_highlevel_v0/checksums.sha256`
- `manifests/tasks/multifin_highlevel_topic_v0/task_spec.json`

### 6) Salinas et al. SEC Loan Agreements NER

- Dataset ID: `salinas_sec_loan_ner_v0`
- Task ID: `TA_NER_SEC_LOAN_SALINAS_v0`
- Publish record: `manifests/publish/salinas_sec_loan_ner_v0_publish_record.json`
- Notes: Salinas SEC loan-agreement NER v0 published using the original author split (FIN5 train / FIN3 test). Raw files were retrieved from the preserved tner/fin mirror, with canonical provenance to Salinas Alvarado, Verspoor, and Baldwin (2015).

Dataset artifacts:
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_all_clean.jsonl`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_clean_meta.json`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_split_meta.json`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_test.jsonl`
- `datasets/sec_loan_ner/salinas/v0/salinas_sec_loan_ner_train.jsonl`

Task artifacts:
- `tasks/salinas_sec_loan_ner_v0/salinas_sec_loan_ner_test_requests.jsonl`
- `tasks/salinas_sec_loan_ner_v0/salinas_sec_loan_ner_train_requests.jsonl`
- `tasks/salinas_sec_loan_ner_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/salinas_sec_loan_ner_v0/checksums.sha256`
- `manifests/datasets/salinas_sec_loan_ner_v0/dataset_spec.json`
- `manifests/tasks/salinas_sec_loan_ner_v0/task_spec.json`
- `manifests/publish/salinas_sec_loan_ner_v0_publish_record.json`

### 7) FinRED Official Release

- Dataset ID: `finred_official_v0`
- Task ID: `TA_RE_FINRED_v0`
- Publish record: `manifests/publish/finred_official_v0_publish_record.json`
- Notes: FinRED official release v0 published using author-provided train/dev/test splits. Train/dev are weakly supervised via distant supervision; test is the higher-trust manual evaluation split. Bootstrap upload was performed with hf upload-large-folder after a standard hf upload timed out.

Dataset artifacts:
- `datasets/finred/official/v0/finred_official_all_clean.jsonl`
- `datasets/finred/official/v0/finred_official_clean_meta.json`
- `datasets/finred/official/v0/finred_official_dev.jsonl`
- `datasets/finred/official/v0/finred_official_split_meta.json`
- `datasets/finred/official/v0/finred_official_test.jsonl`
- `datasets/finred/official/v0/finred_official_train.jsonl`

Task artifacts:
- `tasks/finred_re_v0/README.md`
- `tasks/finred_re_v0/finred_official_dev_requests.jsonl`
- `tasks/finred_re_v0/finred_official_test_requests.jsonl`
- `tasks/finred_re_v0/finred_official_train_requests.jsonl`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finred_official_v0/checksums.sha256`
- `manifests/datasets/finred_official_v0/dataset_spec.json`
- `manifests/tasks/finred_re_v0/task_spec.json`

### 8) FinCausal 2020 Official Release

- Dataset ID: `fincausal2020_official_v0`
- Task ID: `TA_CAUSAL_CLASSIFY_FINCAUSAL2020_v0`
- Publish record: `manifests/publish/fincausal2020_official_v0_publish_record.json`
- Notes: FinCausal 2020 official release published using preserved trial/practice/evaluation structure. Task 1 blank-text rows were removed during ingestion. Task 2 is stored row-wise as cause/effect pair extraction, and evaluation is blind for both tasks. Bootstrap upload was performed with hf upload-large-folder.

Dataset artifacts:
- `datasets/fincausal2020/official/v0/fincausal2020_clean_meta.json`
- `datasets/fincausal2020/official/v0/fincausal2020_split_meta.json`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_all_clean.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_evaluation.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_practice.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task1_trial.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_all_clean.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_evaluation.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_practice.jsonl`
- `datasets/fincausal2020/official/v0/fincausal2020_task2_trial.jsonl`

Task artifacts:
- `tasks/fincausal2020_task1_sc_v0/README.md`
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_evaluation_requests.jsonl`
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_practice_requests.jsonl`
- `tasks/fincausal2020_task1_sc_v0/fincausal2020_task1_trial_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/README.md`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_evaluation_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_practice_requests.jsonl`
- `tasks/fincausal2020_task2_ce_v0/fincausal2020_task2_trial_requests.jsonl`

Manifest / bookkeeping artifacts:
- `manifests/datasets/fincausal2020_official_v0/checksums.sha256`
- `manifests/datasets/fincausal2020_official_v0/dataset_spec.json`
- `manifests/tasks/fincausal2020_task1_sc_v0/task_spec.json`
- `manifests/tasks/fincausal2020_task2_ce_v0/task_spec.json`

### 9) FNXL Sharma 2023 Numeric Labelling

- Dataset ID: `fnxl_sharma2023_v0`
- Task ID: `TA_IE_NUMERIC_LABEL_FNXL_v0`
- Publish record: `manifests/publish/fnxl_sharma2023_v0_publish_record.json`
- Notes: FNXL Sharma 2023 integrated with raw release preserved and original release split archived for provenance only. Canonical split is a clean grouped 80/20 company/file-disjoint split. Task uses sparse (token_index, label_id) prediction over observed used FNXL label IDs. Bootstrap upload was performed with hf upload-large-folder.

Dataset artifacts:
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_manifest.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test.jsonl`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test_companies.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_test_files.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train.jsonl`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train_companies.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_company_split_train_files.json`
- `datasets/fnxl/sharma2023/v0/fnxl_clean_meta.json`
- `datasets/fnxl/sharma2023/v0/fnxl_label_id_mapping.json`
- `datasets/fnxl/sharma2023/v0/fnxl_label_inventory.json`
- `datasets/fnxl/sharma2023/v0/fnxl_release_raw_aggregate.jsonl`

Task artifacts:
- `tasks/fnxl_numeric_labeling_v0/README.md`
- `tasks/fnxl_numeric_labeling_v0/fnxl_test_requests.jsonl`
- `tasks/fnxl_numeric_labeling_v0/fnxl_train_requests.jsonl`

Manifest / bookkeeping artifacts:
- `manifests/datasets/fnxl_sharma2023_v0/checksums.sha256`
- `manifests/datasets/fnxl_sharma2023_v0/dataset_spec.json`
- `manifests/tasks/fnxl_numeric_labeling_v0/task_spec.json`

### 10) Gold Commodity News Headline Multi-label Classification

- Dataset ID: `gold_commodity_news_kaggle_default_v0`
- Task ID: `TA_MLC_GOLD_COMMODITY_NEWS_v0`
- Publish record: `manifests/publish/gold_commodity_news_kaggle_default_v0_publish_record.json`
- Notes: Gold commodity news headline classification integrated from the canonical daittan Kaggle posting. Exact duplicate rows removed in cleaning; deterministic date repair fixes 0200->2000 and 0201->2001. Canonical split is grouped 80/20 over connected components of normalized URL and normalized headline. The ankurzing Kaggle file is retained as derivative provenance only.

Dataset artifacts:
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean.csv`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_clean_meta.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_split_manifest.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test_headlines.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_test_urls.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train.jsonl`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train_headlines.json`
- `datasets/gold_commodity_news/kaggle_default/v0/gold_commodity_news_train_urls.json`

Task artifacts:
- `tasks/gold_commodity_news_multilabel_v0/README.md`
- `tasks/gold_commodity_news_multilabel_v0/gold_commodity_news_test_requests.jsonl`
- `tasks/gold_commodity_news_multilabel_v0/gold_commodity_news_train_requests.jsonl`

Reports:
- `reports/gold_commodity_news/raw_audit_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/gold_commodity_news_kaggle_default_v0/checksums.sha256`
- `manifests/datasets/gold_commodity_news_kaggle_default_v0/dataset_spec.json`
- `manifests/tasks/gold_commodity_news_multilabel_v0/task_spec.json`

### 11) Lamm et al. 2018 Textual Analogy Parsing

- Dataset ID: `lamm2018_tap_v0`
- Task ID: `TA_GRAPH_TAP_LAMM2018_v0`
- Publish record: `manifests/publish/lamm2018_tap_v0_publish_record.json`
- Notes: Published to the HF dataset repo under the standard pipeline publishing schema. Public redistribution approval for this module remains pending.

Dataset artifacts:
- `datasets/tap/lamm2018/v0/all.jsonl`
- `datasets/tap/lamm2018/v0/train.jsonl`
- `datasets/tap/lamm2018/v0/test.jsonl`
- `datasets/tap/lamm2018/v0/split_meta.json`

Task artifacts:
- `tasks/lamm2018_tap_graph_v0/requests/train_requests.jsonl`
- `tasks/lamm2018_tap_graph_v0/requests/test_requests.jsonl`
- `tasks/lamm2018_tap_graph_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/lamm2018_tap_v0/dataset_spec.json`
- `manifests/datasets/lamm2018_tap_v0/checksums.sha256`
- `manifests/tasks/lamm2018_tap_graph_v0/task_spec.json`
- `manifests/publish/lamm2018_tap_v0_publish_record.json`

### 12) FLARE-MA Public Test Benchmark

- Dataset ID: `flare_ma_public_test_v0`
- Task ID: `TA_MA_COMPLETENESS_FLARE_v0`
- Publish record: `manifests/publish/flare_ma_public_test_v0_publish_record.json`
- Notes: Published as an eval-only module using the already-public TheFinAI/flare-ma wrapper. This does not imply source clearance for the full original Zephyr-derived Yang et al. corpus.

Dataset artifacts:
- `datasets/flare_ma/public_test/v0/test.jsonl`
- `datasets/flare_ma/public_test/v0/ingest_meta.json`

Task artifacts:
- `tasks/flare_ma_deal_completeness_v0/requests/test_requests.jsonl`
- `tasks/flare_ma_deal_completeness_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/flare_ma_public_test_v0/dataset_spec.json`
- `manifests/datasets/flare_ma_public_test_v0/checksums.sha256`
- `manifests/tasks/flare_ma_deal_completeness_v0/task_spec.json`
- `manifests/publish/flare_ma_public_test_v0_publish_record.json`

### 13) FLARE-MLESG English Public Test Benchmark

- Dataset ID: `flare_mlesg_en_public_test_v0`
- Task ID: `TA_ESG_ISSUE_MLESG_EN_FLARE_v0`
- Publish record: `manifests/publish/flare_mlesg_en_public_test_v0_publish_record.json`
- Notes: Published in the narrow wrapper-only sense: this module republishes the already-public TheFinAI/flare-mlesg eval artifact only. It does not onboard or imply redistribution clearance for the full original ML-ESG-1 English corpus.

Dataset artifacts:
- `datasets/flare_mlesg/en_public_test/v0/test.jsonl`
- `datasets/flare_mlesg/en_public_test/v0/ingest_meta.json`

Task artifacts:
- `tasks/flare_mlesg_en_issue_v0/requests/test_requests.jsonl`
- `tasks/flare_mlesg_en_issue_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/flare_mlesg_en_public_test_v0/dataset_spec.json`
- `manifests/datasets/flare_mlesg_en_public_test_v0/checksums.sha256`
- `manifests/tasks/flare_mlesg_en_issue_v0/task_spec.json`
- `manifests/publish/flare_mlesg_en_public_test_v0_publish_record.json`

### 14) DynamicESG ML-ESG-1 Chinese Official Split Release

- Dataset ID: `ml_esg1_zh_official_v0`
- Task ID: `TA_MLCLS_ML_ESG1_ZH_v0`
- Publish record: `manifests/publish/ml_esg1_zh_official_v0_publish_record.json`
- Notes: Published official Chinese ML-ESG-1 shared-task split release from DynamicESG commit 4f1bd162504c35df17100ff708ebdf04c68e2b10. Canonical text is headline only, no crawler enrichment is included, and family-stable article_id supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules.

Dataset artifacts:
- `datasets/ml_esg1/zh_official/v0/train.jsonl`
- `datasets/ml_esg1/zh_official/v0/dev.jsonl`
- `datasets/ml_esg1/zh_official/v0/test.jsonl`
- `datasets/ml_esg1/zh_official/v0/label_inventory.json`
- `datasets/ml_esg1/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg1/zh_official/v0/download_meta.json`

Task artifacts:
- `tasks/ml_esg1_zh_issue_v0/requests/train_requests.jsonl`
- `tasks/ml_esg1_zh_issue_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg1_zh_issue_v0/requests/test_requests.jsonl`
- `tasks/ml_esg1_zh_issue_v0/README.md`

Reports:
- `reports/ml_esg1_zh_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/ml_esg1_zh_official_v0/dataset_spec.json`
- `manifests/datasets/ml_esg1_zh_official_v0/checksums.sha256`
- `manifests/tasks/ml_esg1_zh_issue_v0/task_spec.json`
- `manifests/publish/ml_esg1_zh_official_v0_publish_record.json`

### 15) DynamicESG ML-ESG-2 Chinese Official Split Release

- Dataset ID: `ml_esg2_zh_official_v0`
- Task ID: `TA_MLCLS_ML_ESG2_ZH_v0`
- Publish record: `manifests/publish/ml_esg2_zh_official_v0_publish_record.json`
- Notes: Published official Chinese ML-ESG-2 shared-task split release from DynamicESG commit 4f1bd162504c35df17100ff708ebdf04c68e2b10. Canonical text is headline only, the official 5-way impact type label space is preserved exactly, and family-stable article_id supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules.

Dataset artifacts:
- `datasets/ml_esg2/zh_official/v0/train.jsonl`
- `datasets/ml_esg2/zh_official/v0/dev.jsonl`
- `datasets/ml_esg2/zh_official/v0/test.jsonl`
- `datasets/ml_esg2/zh_official/v0/label_inventory.json`
- `datasets/ml_esg2/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg2/zh_official/v0/download_meta.json`

Task artifacts:
- `tasks/ml_esg2_zh_impact_type_v0/requests/train_requests.jsonl`
- `tasks/ml_esg2_zh_impact_type_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg2_zh_impact_type_v0/requests/test_requests.jsonl`
- `tasks/ml_esg2_zh_impact_type_v0/README.md`

Reports:
- `reports/ml_esg2_zh_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/ml_esg2_zh_official_v0/dataset_spec.json`
- `manifests/datasets/ml_esg2_zh_official_v0/checksums.sha256`
- `manifests/tasks/ml_esg2_zh_impact_type_v0/task_spec.json`
- `manifests/publish/ml_esg2_zh_official_v0_publish_record.json`

### 16) DynamicESG ML-ESG-3 Chinese Official Split Release

- Dataset ID: `ml_esg3_zh_official_v0`
- Task ID: `TA_MLCLS_ML_ESG3_ZH_v0`
- Publish record: `manifests/publish/ml_esg3_zh_official_v0_publish_record.json`
- Notes: Published official Chinese ML-ESG-3 shared-task split release from DynamicESG commit 4f1bd162504c35df17100ff708ebdf04c68e2b10. Canonical text is headline only, the released 5-label impact duration label space is preserved exactly, and the released JSON is treated as canonical even though workshop materials present a narrower 3-duration-label framing.

Dataset artifacts:
- `datasets/ml_esg3/zh_official/v0/train.jsonl`
- `datasets/ml_esg3/zh_official/v0/dev.jsonl`
- `datasets/ml_esg3/zh_official/v0/test.jsonl`
- `datasets/ml_esg3/zh_official/v0/label_inventory.json`
- `datasets/ml_esg3/zh_official/v0/ingest_summary.json`
- `datasets/ml_esg3/zh_official/v0/download_meta.json`

Task artifacts:
- `tasks/ml_esg3_zh_impact_duration_v0/requests/train_requests.jsonl`
- `tasks/ml_esg3_zh_impact_duration_v0/requests/dev_requests.jsonl`
- `tasks/ml_esg3_zh_impact_duration_v0/requests/test_requests.jsonl`
- `tasks/ml_esg3_zh_impact_duration_v0/README.md`

Reports:
- `reports/ml_esg3_zh_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/ml_esg3_zh_official_v0/dataset_spec.json`
- `manifests/datasets/ml_esg3_zh_official_v0/checksums.sha256`
- `manifests/tasks/ml_esg3_zh_impact_duration_v0/task_spec.json`
- `manifests/publish/ml_esg3_zh_official_v0_publish_record.json`

### 17) FinQA Official Program-Generation Release

- Dataset ID: `finqa_official_v0`
- Task ID: `TA_PROGGEN_FINQA_v0`
- Publish record: `manifests/publish/finqa_official_v0_publish_record.json`
- Notes: Published canonical FinQA program-generation module from the official pinned GitHub repo commit 0f16e2867befa6840783e58be38c9efb9229d742. The canonical public supervised splits are train, dev, and test; private_test remains raw provenance only and is not published as a supervised split, while a tiny non-sensitive private_test_summary.json artifact documents the exclusion policy. Execution accuracy is the primary metric and program accuracy is the secondary metric.

Dataset artifacts:
- `datasets/finqa/official/v0/train.jsonl`
- `datasets/finqa/official/v0/dev.jsonl`
- `datasets/finqa/official/v0/test.jsonl`
- `datasets/finqa/official/v0/label_inventory.json`
- `datasets/finqa/official/v0/ingest_summary.json`
- `datasets/finqa/official/v0/download_meta.json`
- `datasets/finqa/official/v0/private_test_summary.json`

Task artifacts:
- `tasks/finqa_program_generation_v0/requests/train_requests.jsonl`
- `tasks/finqa_program_generation_v0/requests/dev_requests.jsonl`
- `tasks/finqa_program_generation_v0/requests/test_requests.jsonl`
- `tasks/finqa_program_generation_v0/README.md`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finqa_official_v0/dataset_spec.json`
- `manifests/datasets/finqa_official_v0/checksums.sha256`
- `manifests/tasks/finqa_program_generation_v0/task_spec.json`
- `manifests/publish/finqa_official_v0_publish_record.json`

### 18) TAT-QA Official Hybrid QA Release

- Dataset ID: `tatqa_official_v0`
- Task ID: `TA_QA_TATQA_v0`
- Publish record: `manifests/publish/tatqa_official_v0_publish_record.json`
- Notes: Published canonical TAT-QA hybrid QA module from the official pinned GitHub repo commit 644770eb2a66dddc24b92303bd2acbad84cd2b9f. Canonical processed test.jsonl is derived from tatqa_dataset_test_gold.json, while the original unlabeled tatqa_dataset_test.json is retained raw-only for provenance. Official top-line scoring uses answer+scale exact match, F1, and scale score.

Dataset artifacts:
- `datasets/tatqa/official/v0/train.jsonl`
- `datasets/tatqa/official/v0/dev.jsonl`
- `datasets/tatqa/official/v0/test.jsonl`
- `datasets/tatqa/official/v0/label_inventory.json`
- `datasets/tatqa/official/v0/ingest_summary.json`
- `datasets/tatqa/official/v0/download_meta.json`
- `datasets/tatqa/official/v0/original_test_summary.json`

Task artifacts:
- `tasks/tatqa_hybrid_qa_structured_v0/requests/train_requests.jsonl`
- `tasks/tatqa_hybrid_qa_structured_v0/requests/dev_requests.jsonl`
- `tasks/tatqa_hybrid_qa_structured_v0/requests/test_requests.jsonl`
- `tasks/tatqa_hybrid_qa_structured_v0/README.md`

Reports:
- `reports/tatqa_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/tatqa_official_v0/dataset_spec.json`
- `manifests/datasets/tatqa_official_v0/checksums.sha256`
- `manifests/tasks/tatqa_hybrid_qa_structured_v0/task_spec.json`
- `manifests/publish/tatqa_official_v0_publish_record.json`

### 19) ConvFinQA Official Turn-Level Program-Generation Release

- Dataset ID: `convfinqa_official_v0`
- Task ID: `TA_PROGGEN_CONVFINQA_v0`
- Publish record: `manifests/publish/convfinqa_official_v0_publish_record.json`
- Notes: Published canonical ConvFinQA conversational program-generation module from the official pinned GitHub repo commit cf3eed2d5984960bf06bb8145bcea5e80b0222a6. ConvFinQA is a FinQA-family conversational derivative, so training on FinQA and ConvFinQA does not add fully independent evidence sources. The pinned release exposes labeled train/dev turn files and only unlabeled private test files, so the supervised publication is train/dev only; private test remains raw provenance summarized via test_release_summary.json. Execution accuracy is the primary metric and program accuracy is the secondary metric.

Dataset artifacts:
- `datasets/convfinqa/official/v0/train.jsonl`
- `datasets/convfinqa/official/v0/dev.jsonl`
- `datasets/convfinqa/official/v0/label_inventory.json`
- `datasets/convfinqa/official/v0/ingest_summary.json`
- `datasets/convfinqa/official/v0/download_meta.json`
- `datasets/convfinqa/official/v0/test_release_summary.json`

Task artifacts:
- `tasks/convfinqa_program_generation_v0/requests/train_requests.jsonl`
- `tasks/convfinqa_program_generation_v0/requests/dev_requests.jsonl`
- `tasks/convfinqa_program_generation_v0/README.md`

Reports:
- `reports/convfinqa_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/convfinqa_official_v0/dataset_spec.json`
- `manifests/datasets/convfinqa_official_v0/checksums.sha256`
- `manifests/tasks/convfinqa_program_generation_v0/task_spec.json`
- `manifests/publish/convfinqa_official_v0_publish_record.json`

### 20) FinBen Regulations Public Test Wrapper

- Dataset ID: `regulations_public_test_v0`
- Task ID: `TA_LFQA_REGULATIONS_FINBEN_v0`
- Publish record: `manifests/publish/regulations_public_test_v0_publish_record.json`
- Notes: Published eval-only long-form QA wrapper over the gated TheFinAI/regulations dataset pinned to revision 918111376d5be0f97306f1e0b821529b4021da0b. Authenticated inspection exposed only README.md and test_regulations.json, so no public train/dev split is published. The wrapper schema contains only id/query/answer/text fields, with no explicit context document metadata. Canonical evaluation is a best-faith paper-aligned ROUGE plus BERTScore implementation rather than a hidden internal FinBen scorer replication, using rouge-score==0.1.2 and bert-score==0.3.13 with roberta-large.

Dataset artifacts:
- `datasets/regulations/public_test/v0/test.jsonl`
- `datasets/regulations/public_test/v0/ingest_summary.json`
- `datasets/regulations/public_test/v0/download_meta.json`

Task artifacts:
- `tasks/regulations_longform_qa_v0/requests/test_requests.jsonl`
- `tasks/regulations_longform_qa_v0/README.md`

Reports:
- `reports/regulations_public_test/raw_schema_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/regulations_public_test_v0/dataset_spec.json`
- `manifests/datasets/regulations_public_test_v0/checksums.sha256`
- `manifests/tasks/regulations_longform_qa_v0/task_spec.json`
- `manifests/publish/regulations_public_test_v0_publish_record.json`

### 21) ECTSum Official Bullet Summarization Release

- Dataset ID: `ectsum_official_v0`
- Task ID: `TA_SUM_ECTSUM_v0`
- Publish record: `manifests/publish/ectsum_official_v0_publish_record.json`
- Notes: Published to the HF dataset repo under the standard ST312 artifact layout as a public artifact with an upstream rights caution. Source texts derive from Motley Fool earnings-call transcripts and Reuters summaries; users should review upstream licensing and redistribution terms before reuse.

Dataset artifacts:
- `datasets/ectsum/official/v0/train.jsonl`
- `datasets/ectsum/official/v0/val.jsonl`
- `datasets/ectsum/official/v0/test.jsonl`
- `datasets/ectsum/official/v0/ingest_summary.json`
- `datasets/ectsum/official/v0/download_meta.json`

Task artifacts:
- `tasks/ectsum_bullet_summarization_v0/requests/train_requests.jsonl`
- `tasks/ectsum_bullet_summarization_v0/requests/val_requests.jsonl`
- `tasks/ectsum_bullet_summarization_v0/requests/test_requests.jsonl`
- `tasks/ectsum_bullet_summarization_v0/README.md`

Reports:
- `reports/ectsum_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/ectsum_official_v0/dataset_spec.json`
- `manifests/datasets/ectsum_official_v0/checksums.sha256`
- `manifests/tasks/ectsum_bullet_summarization_v0/task_spec.json`
- `manifests/publish/ectsum_official_v0_publish_record.json`

### 22) FLARE-EDTSUM Public Test Benchmark

- Dataset ID: `flare_edtsum_public_test_v0`
- Task ID: `TA_HEADLINE_EDTSUM_FLARE_v0`
- Publish record: `manifests/publish/flare_edtsum_public_test_v0_publish_record.json`
- Notes: This module is publicly published in the ST312 artifact store, but public_release_cleared remains false; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review. Published eval-only headline-generation wrapper over the gated TheFinAI/flare-edtsum dataset pinned to revision e37154379a3162faf9d7b7a9cd1d582f2ae19adb. The wrapper exposes only a single 2,000-example test split with id/query/answer/text fields, so the canonical processed schema preserves those fields while adding article_text and reference_headline aliases. The task is framed as financial news headline generation rather than generic long-form summarization. The April 16, 2026 governance cleanup refreshed the public download metadata to a sanitized form, added explicit rights-governance fields to the dataset spec, and hardened evaluator diagnostics for completion coverage, format validity, duplicate completions, and non-empty answers.

Dataset artifacts:
- `datasets/flare_edtsum/public_test/v0/test.jsonl`
- `datasets/flare_edtsum/public_test/v0/ingest_summary.json`
- `datasets/flare_edtsum/public_test/v0/download_meta.json`

Task artifacts:
- `tasks/flare_edtsum_headline_generation_v0/requests/test_requests.jsonl`
- `tasks/flare_edtsum_headline_generation_v0/README.md`

Reports:
- `reports/flare_edtsum_public_test/raw_schema_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/flare_edtsum_public_test_v0/dataset_spec.json`
- `manifests/datasets/flare_edtsum_public_test_v0/checksums.sha256`
- `manifests/tasks/flare_edtsum_headline_generation_v0/task_spec.json`
- `manifests/publish/flare_edtsum_public_test_v0_publish_record.json`

### 23) BigData22 Official Stock Movement Prediction Release

- Dataset ID: `bigdata22_official_v0`
- Task ID: `TA_FORECAST_BIGDATA22_v0`
- Publish record: `manifests/publish/bigdata22_official_v0_publish_record.json`
- Notes: Published to the HF dataset repo under the standard ST312 artifact layout as a public artifact with an upstream rights caution. The official slot repo is the canonical source, but the archive does not expose explicit split files or a clear redistribution license for the tweets and market data, so users should review upstream source-chain terms before reuse. The paper states only that the split is chronological, and no public first-party split files or cut dates were recoverable from the official repo, bundled archive, paper PDF, or repo git history, so ST312 keeps a documented train/valid/test reconstruction over sorted unique target trading dates inside the paper window after excluding neutral-band rows.

Dataset artifacts:
- `datasets/bigdata22/official/v0/train.jsonl`
- `datasets/bigdata22/official/v0/valid.jsonl`
- `datasets/bigdata22/official/v0/test.jsonl`
- `datasets/bigdata22/official/v0/label_inventory.json`
- `datasets/bigdata22/official/v0/ingest_summary.json`
- `datasets/bigdata22/official/v0/download_meta.json`

Task artifacts:
- `tasks/bigdata22_stock_movement_v0/requests/train_requests.jsonl`
- `tasks/bigdata22_stock_movement_v0/requests/valid_requests.jsonl`
- `tasks/bigdata22_stock_movement_v0/requests/test_requests.jsonl`
- `tasks/bigdata22_stock_movement_v0/README.md`

Reports:
- `reports/bigdata22_official/raw_schema_summary.json`
- `reports/bigdata22_official/ingest_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/bigdata22_official_v0/dataset_spec.json`
- `manifests/datasets/bigdata22_official_v0/checksums.sha256`
- `manifests/tasks/bigdata22_stock_movement_v0/task_spec.json`
- `manifests/publish/bigdata22_official_v0_publish_record.json`

### 24) StockNet ACL18 Paper-Canonical Release

- Dataset ID: `stocknet_acl18_paper_v0`
- Task ID: `FC_STOCKMOVE_STOCKNET_ACL18_v0`
- Publish record: `manifests/publish/stocknet_acl18_paper_v0_publish_record.json`
- Notes: Published to the HF dataset repo under the standard ST312 artifact layout as a public artifact with a small source-terms caution. The canonical source is the official yumoxu/stocknet-dataset repository pinned to commit 330708b5ddc359961078bef469f43f48992fd6e4, not the later FinBen / FLARE wrapper. ST312 preserves the ACL18 paper's exact 20,339 / 2,555 / 3,720 temporal split counts, 5-day trading-day alignment semantics, and asymmetric thresholds <= -0.5% -> Fall and > 0.55% -> Rise. The official release does not reproduce the paper counts under an additional hard tweet-presence filter, so that discrepancy is documented in the reconstruction audit rather than silently changing the canonical benchmark. Original source repository is MIT-licensed. The released corpus includes tweet-derived content collected under Twitter's official license and price data sourced from Yahoo Finance; downstream users should review applicable platform/source terms before reuse.

Dataset artifacts:
- `datasets/stocknet/acl18_paper/v0/train.jsonl`
- `datasets/stocknet/acl18_paper/v0/dev.jsonl`
- `datasets/stocknet/acl18_paper/v0/test.jsonl`
- `datasets/stocknet/acl18_paper/v0/ingest_summary.json`
- `datasets/stocknet/acl18_paper/v0/download_meta.json`

Task artifacts:
- `tasks/stocknet_acl18_stockmove_v0/requests/train_requests.jsonl`
- `tasks/stocknet_acl18_stockmove_v0/requests/dev_requests.jsonl`
- `tasks/stocknet_acl18_stockmove_v0/requests/test_requests.jsonl`
- `tasks/stocknet_acl18_stockmove_v0/README.md`

Reports:
- `reports/stocknet_acl18_paper/raw_schema_summary.json`
- `reports/stocknet_acl18_paper/reconstruction_audit.json`
- `reports/stocknet_acl18_paper/finben_wrapper_audit.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/stocknet_acl18_paper_v0/dataset_spec.json`
- `manifests/datasets/stocknet_acl18_paper_v0/checksums.sha256`
- `manifests/tasks/stocknet_acl18_stockmove_v0/task_spec.json`
- `manifests/publish/stocknet_acl18_paper_v0_publish_record.json`

### 25) FinArg ECC Argument Unit Classification

- Dataset ID: `finarg_auc_ecc_official_v0`
- Task ID: `TA_AUC_FINARG_ECC_v0`
- Publish record: `manifests/publish/finarg_auc_ecc_official_v0_publish_record.json`
- Notes: FinArg ECC AUC module published from the official preserved train/dev/test split. Label mapping inferred from official class totals: 0->premise, 1->claim. One exact sentence overlap across train/dev is preserved and documented as a release issue.

Dataset artifacts:
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_all_clean.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_clean_meta.json`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_train.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_dev.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_test.jsonl`
- `datasets/finarg_auc/ecc/official/v0/finarg_auc_ecc_split_meta.json`

Task artifacts:
- `tasks/finarg_auc_ecc_v0/README.md`
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_train_requests.jsonl`
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_dev_requests.jsonl`
- `tasks/finarg_auc_ecc_v0/finarg_auc_ecc_test_requests.jsonl`

Reports:
- `reports/finarg_auc_ecc_official/raw_audit_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finarg_auc_ecc_official_v0/checksums.sha256`
- `manifests/datasets/finarg_auc_ecc_official_v0/dataset_spec.json`
- `manifests/tasks/finarg_auc_ecc_v0/task_spec.json`

### 26) FinArg ECC Argument Relation Classification

- Dataset ID: `finarg_arc_ecc_official_v0`
- Task ID: `TA_ARC_FINARG_ECC_v0`
- Publish record: `manifests/publish/finarg_arc_ecc_official_v0_publish_record.json`
- Notes: FinArg ECC ARC module published from the official preserved train/dev/test split. Label mapping inferred from official class totals: 0->other, 1->support, 2->attack. ARC is highly imbalanced, especially for attack, and macro-aware evaluation is used.

Dataset artifacts:
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_all_clean.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_clean_meta.json`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_train.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_dev.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_test.jsonl`
- `datasets/finarg_arc/ecc/official/v0/finarg_arc_ecc_split_meta.json`

Task artifacts:
- `tasks/finarg_arc_ecc_v0/README.md`
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_train_requests.jsonl`
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_dev_requests.jsonl`
- `tasks/finarg_arc_ecc_v0/finarg_arc_ecc_test_requests.jsonl`

Reports:
- `reports/finarg_arc_ecc_official/raw_audit_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/finarg_arc_ecc_official_v0/checksums.sha256`
- `manifests/datasets/finarg_arc_ecc_official_v0/dataset_spec.json`
- `manifests/tasks/finarg_arc_ecc_v0/task_spec.json`

### 27) UCI Statlog German Credit v0

Dataset artifacts:
- `datasets/german_credit/uci_statlog/v0/train.jsonl`
- `datasets/german_credit/uci_statlog/v0/valid.jsonl`
- `datasets/german_credit/uci_statlog/v0/test.jsonl`
- `datasets/german_credit/uci_statlog/v0/ingest_summary.json`
- `datasets/german_credit/uci_statlog/v0/download_meta.json`

Task requests:
- `tasks/german_credit_risk_v0/requests/train_requests.jsonl`
- `tasks/german_credit_risk_v0/requests/valid_requests.jsonl`
- `tasks/german_credit_risk_v0/requests/test_requests.jsonl`

Task README snapshot:
- `tasks/german_credit_risk_v0/README.md`

Auxiliary provenance reports:
- `reports/statlog_german_credit_uci/raw_schema_summary.json`
- `reports/statlog_german_credit_uci/split_replication_audit.json`
- `reports/statlog_german_credit_uci/wrapper_alignment_audit.json`

Publish bookkeeping:
- `manifests/datasets/statlog_german_credit_uci_v0/dataset_spec.json`
- `manifests/datasets/statlog_german_credit_uci_v0/checksums.sha256`
- `manifests/tasks/german_credit_risk_v0/task_spec.json`
- `manifests/publish/statlog_german_credit_uci_v0_publish_record.json`

Rights note:
- UCI publishes this historical benchmark under CC BY 4.0. The dataset includes sensitive demographic-style variables and should not be interpreted as a deployment recommendation.

### UCI Statlog (Australian Credit Approval)

Dataset artifacts:
- `datasets/australian_credit/uci_statlog/v0/australian_credit_all_clean.jsonl`
- `datasets/australian_credit/uci_statlog/v0/australian_credit_clean_meta.json`
- `datasets/australian_credit/uci_statlog/v0/australian_credit_train.jsonl`
- `datasets/australian_credit/uci_statlog/v0/australian_credit_valid.jsonl`
- `datasets/australian_credit/uci_statlog/v0/australian_credit_test.jsonl`
- `datasets/australian_credit/uci_statlog/v0/australian_credit_split_manifest.json`

Task artifacts:
- `tasks/australian_credit_mc_v0/README.md`
- `tasks/australian_credit_mc_v0/australian_credit_train_requests.jsonl`
- `tasks/australian_credit_mc_v0/australian_credit_valid_requests.jsonl`
- `tasks/australian_credit_mc_v0/australian_credit_test_requests.jsonl`

Reports:
- `reports/australian_credit_uci_statlog/raw_audit_summary.json`

Manifest / bookkeeping artifacts:
- `manifests/datasets/australian_credit_uci_statlog_v0/checksums.sha256`
- `manifests/datasets/australian_credit_uci_statlog_v0/dataset_spec.json`
- `manifests/tasks/australian_credit_mc_v0/task_spec.json`
- `manifests/publish/australian_credit_uci_statlog_v0_publish_record.json`

## Labeling / split notes

### FinArg ECC

- AUC uses the preserved official ECC split with labels inferred from official totals as `0 -> premise`, `1 -> claim`
- ARC uses the preserved official ECC split with labels inferred from official totals as `0 -> other`, `1 -> support`, `2 -> attack`
- One exact AUC sentence overlap exists across train/dev and is preserved as a documented release issue
- ARC shows no cross-split exact-pair overlap in the local ECC release
- ARC is strongly class-imbalanced, especially for the `attack` class, so macro-aware evaluation is emphasized

### UCI Statlog German Credit

- Canonical source is the UCI Statlog (German Credit Data) archive, DOI `10.24432/C5NC77`
- Canonical preserved source surface is the original symbolic `german.data` file; `german.data-numeric` is retained raw-only as an auxiliary artifact
- ST312 preserves original `Attribute1..Attribute20` and `Class`, plus original row order via `uci_row_index`
- The public `TheFinAI/german-credit-benchmark` wrapper is used only to replicate the `700 / 100 / 200` split after exact row-level matching against all 1,000 UCI rows
- Canonical default evaluation is cost-sensitive because UCI explicitly requires the asymmetric matrix `[[0,1],[5,0]]` for `1 = Good` and `2 = Bad`
- The optional compatibility view reports macro F1 and MCC, but it is not the canonical source-task scorer
- This historical benchmark includes sensitive demographic-style variables such as personal status and sex, age, and foreign-worker status, and should not be interpreted as a deployment template

### Australian Credit UCI Statlog

- Canonical source is the UCI Statlog (Australian Credit Approval) dataset, not the FLARE wrapper
- Raw UCI files `australian.dat` and `australian.doc` are preserved unchanged
- Raw downloaded file uses binary labels `0/1`, normalized canonically as `Reject=0`, `Approve=1`
- Exact FLARE row alignment was attempted but not verified
- Canonical split is therefore a fixed-seed count-matched reconstruction with counts `482 / 69 / 139`
- UCI documentation around missing values is ambiguous; that ambiguity is preserved in metadata

## Licensing

- `fpb_allagree_v0` — Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
- `fiqasa_hf_default_v0` — MIT License
- `finben_fomc_v0` — Creative Commons Attribution-NonCommercial 4.0 International
- `finben_finer_ord_v0` — Creative Commons Attribution-NonCommercial 4.0 International
- `multifin_highlevel_v0` — Creative Commons Attribution Share Alike 4.0 International
- `salinas_sec_loan_ner_v0` — Unspecified; paper states dataset available for research purposes
- `finred_official_v0` — Unspecified in official repo README; treat conservatively until independently confirmed
- `fincausal2020_official_v0` — Unspecified in repo pages inspected; verify before redistribution beyond current workflow
- `fnxl_sharma2023_v0` — Unspecified from local handoff; verify independently before redistribution beyond current workflow
- `gold_commodity_news_kaggle_default_v0` — Check Kaggle terms and dataset-level permission before redistribution beyond current workflow
- `lamm2018_tap_v0` — license_sensitive_ldc_derivative_pending_review
- `flare_ma_public_test_v0` — public_wrapper_only_full_source_commercial_uncleared
- `flare_mlesg_en_public_test_v0` — public_wrapper_only_benchmark_claim_cc_by_nc_nd_full_source_uncleared
- `ml_esg1_zh_official_v0` — Creative Commons Attribution-ShareAlike 4.0 International
- `ml_esg2_zh_official_v0` — Creative Commons Attribution-ShareAlike 4.0 International
- `ml_esg3_zh_official_v0` — Creative Commons Attribution-ShareAlike 4.0 International
- `finqa_official_v0` — MIT License
- `tatqa_official_v0` — Creative Commons Attribution 4.0 International
- `convfinqa_official_v0` — MIT License
- `regulations_public_test_v0` — mit
- `ectsum_official_v0` — gpl-3.0-only_code_text_redistribution_pending_review
- `flare_edtsum_public_test_v0` — license_sensitive_research_access_gated_upstream
- `bigdata22_official_v0` — license_not_explicit_tweets_and_market_data_publication_with_caution
- `stocknet_acl18_paper_v0` — mit_with_twitter_yahoo_source_terms_caution
- `finarg_auc_ecc_official_v0` — GPL-3.0 (inferred from public FinArg repo; local release lacks embedded license)
- `finarg_arc_ecc_official_v0` — GPL-3.0 (inferred from public FinArg repo; local release lacks embedded license)
