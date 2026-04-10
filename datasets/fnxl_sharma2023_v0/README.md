# FNXL Sharma 2023 Dataset (v0)

Dataset module for the FNXL numeric labelling benchmark from *Financial Numeric Extreme Labelling: A Dataset and Benchmarking for XBRL Tagging*.

## Dataset ID

`fnxl_sharma2023_v0`

## Provenance stance

- Canonical task definition comes from the Sharma 2023 FNXL paper.
- Runtime ingestion uses a user-provided local copy of the released FNXL files.
- Absolute local filesystem paths are intentionally omitted from repo-facing metadata.
- `allLabelCount.csv` is treated as the authoritative label inventory.
- `labels.json` is auxiliary only and is used to resolve sparse label-id mappings.
- `consolidated_xbrl_*` files are downstream derived artifacts and are not used for raw benchmark ingestion.

## Canonical pipeline stance

- Preserve the released `train/dev/test` split for provenance only.
- Do **not** use the released split as canonical evaluation, because leakage across companies and filing paths was confirmed.
- Use the rebuilt grouped 80/20 company/file-disjoint split as the canonical train/test split.
- Use `tokens` + `ner_tags` as the canonical supervision layer.
- Keep `numerals-tags` only as auxiliary metadata.

## FNXL-specific notes

- Aggregate rows: `79,088`
- Positive labelled numeric mentions: `142,922`
- Authoritative inventory size: `2,794`
- Observed used positive label-id range: sparse within `1..2799`
