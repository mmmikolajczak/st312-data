---
license: other
pretty_name: ST312 FinLLM Data Artifact Store
viewer: false
tags:
- finance
- llm
- benchmark
- artifact-store
- heterogeneous
---

# ST312 FinLLM Data Artifact Store

Artifact repository for the ST312 Applied Statistics project (FinLLM pipeline).

This repository and its Hugging Face counterpart are a heterogeneous multi-module artifact store, not a single ordinary dataset.
The published module index below is the source of truth for what is available.

This repository is the **code + metadata control plane** for the Risko-1 style dataset/task pipeline:
- dataset ingestion, cleaning, normalisation, and split scripts
- task specs, prompt templates, reward parsers, and cached evaluators
- dataset/task registries and manifest snapshots for reproducibility
- publish records and checksums for GitHub/Hugging Face bookkeeping

Large data artifacts are **not** tracked in GitHub. Canonical processed artifacts are published to the Hugging Face dataset repo:
- `mmmikolajczak/st312-data`

## HF surface note

The Hugging Face repo is an artifact store containing mixed JSONL datasets, request files, manifests, checksums, and bookkeeping records.
The default dataset viewer may be unavailable or misleading for this repository shape.
If the Hub UI still shows a generic viewer pane or generic task tags, treat those as stale platform-level UI artifacts rather than the repository contract.
Use the published contents index in the HF README and the published module index below as the reliable control-plane view.

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
9. Verify published HF surface paths against the expected section in `manifests/hf_repo/README.md`
10. Add publish record
11. Push GitHub metadata/manifests
12. Validate with `python scripts/utils/check_publish_records.py`

## Rights-governance fields for sensitive modules

For public-but-sensitive modules, use the same machine-readable control-plane keys in the dataset spec:

- `public_release_cleared`
- `upstream_access_mode`
- `publication_mode`
- `reuse_caution_summary`

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
- **Labeling note:** canonical source is the official `ymntseng/DynamicESG` ML-ESG-1 Chinese split release pinned to a concrete commit; official `train/dev/test` is preserved exactly; canonical text is the released headline only; labels are preserved as released multi-label code lists; the pinned release differs from the FinNLP 2023 workshop paper statistics and is treated as canonical with observed split counts `1058 / 118 / 131` and an observed 48-code inventory; family-stable `article_id` supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules.

### 15) DynamicESG ML-ESG-2 Chinese Official v0
- **Dataset ID:** `ml_esg2_zh_official_v0`
- **Task ID:** `TA_MLCLS_ML_ESG2_ZH_v0`
- **Task type:** Chinese headline-only 5-way single-label ESG impact type classification
- **HF dataset path:** `datasets/ml_esg2/zh_official/v0/`
- **HF task path:** `tasks/ml_esg2_zh_impact_type_v0/`
- **Publish record:** `manifests/publish/ml_esg2_zh_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `ymntseng/DynamicESG` ML-ESG-2 Chinese split release pinned to the same family commit as ML-ESG-1; official `train/dev/test` is preserved exactly; canonical text is the released headline only; the official 5-way impact type space is preserved exactly as `Opportunity`, `Risk`, `CannotDistinguish`, `NotRelatedtoCompany`, and `NotRelatedtoESGTopic`; `Impact_Type` is normalized from the released singleton list to a scalar canonical label while preserving the raw list in metadata.

### 16) DynamicESG ML-ESG-3 Chinese Official v0
- **Dataset ID:** `ml_esg3_zh_official_v0`
- **Task ID:** `TA_MLCLS_ML_ESG3_ZH_v0`
- **Task type:** Chinese headline-only 5-way single-label ESG impact duration classification
- **HF dataset path:** `datasets/ml_esg3/zh_official/v0/`
- **HF task path:** `tasks/ml_esg3_zh_impact_duration_v0/`
- **Publish record:** `manifests/publish/ml_esg3_zh_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `ymntseng/DynamicESG` ML-ESG-3 Chinese split release pinned to the same family commit as ML-ESG-1 and ML-ESG-2; official `train/dev/test` is preserved exactly; canonical text is the released headline only; the released 5-way impact duration space is preserved exactly as `<2`, `2~5`, `>5`, `NotRelatedtoCompany`, and `NotRelatedtoESGTopic`; `Impact_Duration` is normalized from the released singleton list to a scalar canonical label while preserving the raw list in metadata; the released JSON is treated as canonical even though workshop materials present a narrower 3-duration-label framing.

### 17) FinQA Official v0
- **Dataset ID:** `finqa_official_v0`
- **Task ID:** `TA_PROGGEN_FINQA_v0`
- **Task type:** financial-report numerical reasoning program generation
- **HF dataset path:** `datasets/finqa/official/v0/`
- **HF task path:** `tasks/finqa_program_generation_v0/`
- **Publish record:** `manifests/publish/finqa_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `czyssrs/FinQA` GitHub repo pinned to a concrete commit because the repo has no tagged releases; public supervised `train/dev/test` are preserved exactly; `private_test` is kept raw for provenance only and is not published as a supervised split, while a tiny non-sensitive `private_test_summary.json` artifact may be published to document exclusion policy; the canonical task target is executable program generation over `pre_text`, `table`, `post_text`, and question; the final answer is derived from executing the predicted program, with execution accuracy as the primary metric and program accuracy as the secondary metric.

### 18) TAT-QA Official v0
- **Dataset ID:** `tatqa_official_v0`
- **Task ID:** `TA_QA_TATQA_v0`
- **Task type:** structured hybrid financial question answering
- **HF dataset path:** `datasets/tatqa/official/v0/`
- **HF task path:** `tasks/tatqa_hybrid_qa_structured_v0/`
- **Publish record:** `manifests/publish/tatqa_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `NExTplusplus/TAT-QA` GitHub repo pinned to commit `644770eb2a66dddc24b92303bd2acbad84cd2b9f`; canonical processed `test.jsonl` is derived from the Jan 2024 `tatqa_dataset_test_gold.json` release, while the original unlabeled `tatqa_dataset_test.json` is retained raw-only for provenance; hybrid table-plus-paragraph context is preserved per question along with derivation, answer-type, answer-source, related-paragraph, comparison, and scale annotations; the top-line benchmark remains the official answer+scale `exact_match`, `f1`, and `scale_score`.

### 19) ConvFinQA Official v0
- **Dataset ID:** `convfinqa_official_v0`
- **Task ID:** `TA_PROGGEN_CONVFINQA_v0`
- **Task type:** conversational financial-report numerical reasoning program generation
- **HF dataset path:** `datasets/convfinqa/official/v0/`
- **HF task path:** `tasks/convfinqa_program_generation_v0/`
- **Publish record:** `manifests/publish/convfinqa_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `czyssrs/ConvFinQA` GitHub repo pinned to commit `cf3eed2d5984960bf06bb8145bcea5e80b0222a6`; ConvFinQA is a FinQA-family conversational derivative rather than an independent evidence-source family; the canonical modeling unit is the labeled turn-level release; only supervised `train/dev` are published because the pinned release exposes only unlabeled private test files; the canonical target is executable program generation over dialogue history plus report context, with execution accuracy as the primary metric and program accuracy as the secondary metric.

### 20) FinBen Regulations Public Test v0
- **Dataset ID:** `regulations_public_test_v0`
- **Task ID:** `TA_LFQA_REGULATIONS_FINBEN_v0`
- **Task type:** eval-only financial-regulation long-form question answering
- **HF dataset path:** `datasets/regulations/public_test/v0/`
- **HF task path:** `tasks/regulations_longform_qa_v0/`
- **Publish record:** `manifests/publish/regulations_public_test_v0_publish_record.json`
- **Labeling note:** canonical source is the gated `TheFinAI/regulations` Hugging Face dataset pinned to revision `918111376d5be0f97306f1e0b821529b4021da0b`; authenticated inspection exposed only `README.md` and `test_regulations.json`, so this module is treated as eval-only `test`-only wrapper input with no fabricated `train/dev`; the released wrapper contains only `id`, `query`, `answer`, and `text`, so the canonical processed schema preserves the bare question, reference answer, and prompt-prefixed source query while leaving context/source-document fields null; canonical scoring is best-faith paper-aligned ROUGE plus BERTScore.

### 21) ECTSum Official v0
- **Dataset ID:** `ectsum_official_v0`
- **Task ID:** `TA_SUM_ECTSUM_v0`
- **Task type:** bullet-style earnings-call transcript summarization
- **HF dataset path:** `datasets/ectsum/official/v0/`
- **HF task path:** `tasks/ectsum_bullet_summarization_v0/`
- **Publish record:** `manifests/publish/ectsum_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `rajdeep345/ECTSum` GitHub repo pinned to commit `6909f1fc543104c1c60cf9de63e799f6620d1b0a`; official `train/val/test` is preserved exactly over transcript-summary pairs from Prepared Remarks; the canonical task is original-paper bullet-style summarization with ROUGE, BERTScore, SummaCConv, and Num-Prec as the default evaluation variant, plus an optional FinBen-compatible ROUGE/BERTScore/BARTScore view; source texts derive from Motley Fool transcripts and Reuters summaries, so this module is publicly published with an upstream licensing and redistribution caution.

### 22) FLARE-EDTSUM Public Test v0
- **Dataset ID:** `flare_edtsum_public_test_v0`
- **Task ID:** `TA_HEADLINE_EDTSUM_FLARE_v0`
- **Task type:** eval-only financial news headline generation
- **HF dataset path:** `datasets/flare_edtsum/public_test/v0/`
- **HF task path:** `tasks/flare_edtsum_headline_generation_v0/`
- **Publish record:** `manifests/publish/flare_edtsum_public_test_v0_publish_record.json`
- **Labeling note:** canonical source is the gated `TheFinAI/flare-edtsum` Hugging Face dataset pinned to revision `e37154379a3162faf9d7b7a9cd1d582f2ae19adb`; authenticated inspection exposed only a single `test` split with `2000` examples and fields `id`, `query`, `answer`, and `text`; ST312 treats the task as financial news headline generation rather than generic long-form summarization, preserving raw wrapper fields while adding `article_text` and `reference_headline` aliases; this module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

### 23) BigData22 Official v0
- **Dataset ID:** `bigdata22_official_v0`
- **Task ID:** `TA_FORECAST_BIGDATA22_v0`
- **Task type:** binary stock movement forecasting from price history plus tweets
- **HF dataset path:** `datasets/bigdata22/official/v0/`
- **HF task path:** `tasks/bigdata22_stock_movement_v0/`
- **Publish record:** `manifests/publish/bigdata22_official_v0_publish_record.json`
- **Labeling note:** canonical source is the official `deeptrade-public/slot` GitHub repo pinned to commit `1c1a25671d4c81f5fcd45607447225862c308dd5`; the bundled archive contains BigData22 together with ACL18 and CIKM18, but this module canonically ingests only BigData22; labels are taken directly from the release and mapped to the stable binary interface `Rise / Fall`, with the neutral band excluded; the paper-window benchmark range `2019-07-05` through `2020-06-30` is preserved as canonical scope, while the missing split files are handled via a documented chronological `train / valid / test` reconstruction; publication is public but carries an upstream rights caution because the repo surface does not expose a clear redistribution license for the tweets and market data.

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
- Family-stable `article_id` supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules

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
- `private_test.json` is kept raw for provenance only and is excluded from the supervised canonical publication because it has no references; only a tiny non-sensitive `private_test_summary.json` provenance artifact may be published
- Canonical target is executable program generation in the FinQA DSL, not answer-only QA
- Canonical evaluation prioritizes execution accuracy, with program accuracy as the secondary metric
- The official repo is MIT-licensed; the Hugging Face mirror metadata differs and is not treated as canonical

### TAT-QA Official

- Canonical source is the official `NExTplusplus/TAT-QA` GitHub repo pinned to commit `644770eb2a66dddc24b92303bd2acbad84cd2b9f`
- Canonical processed `train / dev / test` preserves the official hybrid-context split, with `test.jsonl` derived from `tatqa_dataset_test_gold.json`
- The original unlabeled `tatqa_dataset_test.json` is retained raw-only for provenance and summarized separately as `original_test_summary.json`
- Hybrid context is preserved as question + raw table + ordered paragraphs, with deterministic serializations for prompts
- Rich supervision fields are preserved in processed rows, but the canonical benchmark contract remains official answer+scale scoring using `exact_match`, `f1`, and `scale_score`
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
- Official `train / val / test` prepared-remarks transcript-summary pairs are preserved exactly, with observed counts `1681 / 249 / 495` for `2425` total cleaned pairs
- Canonical modeling unit is one transcript-summary pair, preserving both joined text and ordered line/bullet lists
- Canonical task is original-paper bullet-style summarization, not a FinBen-only wrapper
- Default evaluation variant is original ECTSum with ROUGE, BERTScore, SummaCConv, and Num-Prec; an optional FinBen-compatible ROUGE/BERTScore/BARTScore view is also provided
- Source chain involves Motley Fool transcripts and Reuters summaries, so upstream licensing and redistribution terms should be reviewed before reuse

### FLARE-EDTSUM Public Test

- Canonical source is the gated `TheFinAI/flare-edtsum` Hugging Face dataset pinned to revision `e37154379a3162faf9d7b7a9cd1d582f2ae19adb`
- Authenticated inspection exposed only a single `test` split with `2000` rows; no `train / dev` release is published in the wrapper
- The wrapper exposes only `id`, `query`, `answer`, and `text`; canonical processed rows preserve those fields and add `article_text` plus `reference_headline`
- Canonical task framing is financial news headline generation, or headline-style abstractive summarization, not generic paragraph summarization
- Stable default evaluation uses ROUGE plus BERTScore, while the FinBen-paper-aligned view adds best-effort BARTScore
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

### BigData22 Official

- Canonical source is the official `deeptrade-public/slot` GitHub repo pinned to commit `1c1a25671d4c81f5fcd45607447225862c308dd5`
- The bundled `data.zip` archive contains `bigdata22`, `acl18`, and `cikm18`; only `bigdata22` is onboarded as the canonical module in this turn
- Canonical paper-window scope is `2019-07-05` through `2020-06-30`, which matches the paper's reported `272,762` tweet lines and 362-day calendar span
- Canonical labels are taken directly from the release: `1 -> Rise`, `-1 -> Fall`, and the neutral band `0` is excluded from the binary task
- The official archive does not ship split files or cut dates, so ST312 reconstructs a documented chronological `70 / 10 / 20` `train / valid / test` partition over the paper window, yielding `5624 / 1117 / 2063` examples
- Canonical evaluation uses `mcc` as the primary metric and `accuracy` as the secondary metric
- The public FinBen/OpenFinLLM-style wrapper is treated as a derived comparison surface rather than the source of truth because its counts and date range differ from the official paper-window release

## Validation

Use:
`python scripts/utils/check_publish_records.py`

Target status convention:
- registry status: `published`
- dataset spec status: `"published_to_hf": true`

## Notes

This repository is designed so that new datasets/tasks can be added with the same structure and minimal ambiguity. The published-modules section above should remain the only top-level module index, to avoid drift and duplication.
