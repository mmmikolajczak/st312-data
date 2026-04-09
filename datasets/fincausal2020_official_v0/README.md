# FinCausal 2020 Official Dataset (v0)

Dataset module for the official YseopLab FinCausal 2020 release.

## Dataset ID

`fincausal2020_official_v0`

## Canonical provenance

- Official repo: `https://github.com/yseop/YseopLab/tree/develop/FNP_2020_FinCausal`
- Shared-task paper: `https://aclanthology.org/2020.fnp-1.3.pdf`

## Key notes

- Preserve the official `trial / practice / evaluation` structure
- Task 1 and Task 2 are linked but separate modules
- Task 1 blank-text rows are removed defensively during ingestion
- Task 2 is stored row-wise as cause/effect pair extraction
- Evaluation split is blind and treated as held-out/no-gold
- Official scoring scripts are the source of truth for evaluation semantics
