# AGENTS.md

## Repository purpose
This repository is the code + metadata control plane for the ST312 Applied Statistics project data/task pipeline for FinLLM training and benchmarking.

It contains:
- dataset ingestion, cleaning, normalisation, and split scripts
- task specs, prompt templates, reward parsers, and cached evaluators
- dataset/task registries and manifest snapshots for reproducibility
- publish records and checksums for GitHub/Hugging Face bookkeeping

The pipeline supports both benchmark preparation and training-oriented task construction for FinLLMs. In particular, task modules include components such as prompt templates, reward parsers, and evaluators, which are relevant to downstream training and benchmarking workflows.

Large data artifacts are not tracked in GitHub. Canonical processed artifacts are published to the Hugging Face dataset repo `mmmikolajczak/st312-data`.

## Repository architecture
- `datasets/`: dataset modules (metadata only), including dataset README, dataset spec, checksums, and `datasets/dataset_registry.json`
- `tasks/`: task modules (metadata only), including task README, task spec, and `tasks/task_registry.json`
- `scripts/datasets/<dataset>/`: ingestion, cleaning / normalization, splitting
- `scripts/tasks/<task_module>/`: reward parser, prompt renderer, request builder, cached evaluator
- `manifests/`: dataset/task snapshots, checksums, publish records, and HF repo-facing README source
- `data/`: local-only working artifacts
- `reports/`: evaluation outputs

## Reproducibility conventions
GitHub tracks metadata, manifests, and checksums.
Hugging Face stores the canonical processed artifacts and request files.

Every published dataset/task module should have:
- dataset/task README
- dataset/task spec
- manifest snapshot(s)
- checksums
- publish record with HF commit hashes
- registry entries marked consistently

Validation command:
`python scripts/utils/check_publish_records.py`

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
