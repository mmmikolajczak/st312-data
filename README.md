# ST312 FinLLM Data Pipeline

This repository contains the **data/task pipeline** for the ST312 Applied Statistics project (Mateusz + Marco), designed as a scalable extension of the Risko-1 workflow.

## Architecture principle
- **GitHub = control plane**
  - code, scripts, task specs, dataset specs, manifests, docs
- **Hugging Face = data plane**
  - processed train/test datasets and related artifacts

This keeps GitHub lightweight and inspectable while allowing dataset versioning and sharing through HF.

---

## Repository structure

### `tasks/`
Task definitions (prompt/output/reward/eval contracts), one folder per task.

### `datasets/`
Dataset definitions (upstream source, parsing/split rules, schema expectations), one folder per dataset.

### `scripts/`
Runnable CLI scripts, grouped by:
- `scripts/datasets/...`
- `scripts/tasks/...`

### `manifests/`
Immutable metadata snapshots for dataset/task releases and runs.

### `data/`
Local working cache (gitignored). No data files are stored in GitHub.

---

## Current implemented task
- `TA_SENT_FPB_v0` — Financial PhraseBank sentiment classification

Task docs:
- `tasks/fpb_sentiment_v0/README.md`

Dataset definition:
- `datasets/fpb_allagree_v0/dataset_spec.json`

---

## Data policy
Actual datasets are NOT stored in this GitHub repo.

They are:
- built locally into `data/...` (gitignored)
- published to a private Hugging Face dataset repo (canonical source of artifacts)

---

## Adding a new dataset (pattern)
1. Create `datasets/<dataset_id>_v0/`
2. Add `dataset_spec.json` (+ README)
3. Add build scripts under `scripts/datasets/<family>/`
4. Build locally into `data/...`
5. Publish to HF
6. Add dataset manifest under `manifests/datasets/`

## Adding a new task (pattern)
1. Create `tasks/<task_name>_v0/`
2. Add `task_spec.json` (+ README)
3. Add task scripts under `scripts/tasks/<task_name>_v0/`
4. Build requests / evaluate outputs
5. Add task manifest under `manifests/tasks/`

