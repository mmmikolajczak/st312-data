# FNXL Sharma 2023 Dataset (v0)

Dataset module for the FNXL numeric labelling benchmark from *Financial Numeric Extreme Labelling: A Dataset and Benchmarking for XBRL Tagging*.

## Dataset ID

`fnxl_sharma2023_v0`

## Canonical provenance

- Paper-defined task: numeric labelling over 10-K sentences with US-GAAP XBRL labels
- Local runtime source: `/Users/matti/Downloads/FNXL`
- Auxiliary local provenance source: `/Users/matti/Downloads/Data`

## Pipeline stance

- Preserve the released `train/dev/test` split for provenance only
- Build a new grouped 80/20 company/file-disjoint split as the canonical pipeline split
- Use `allLabelCount.csv` as the authoritative label inventory
- Use `tokens` + `ner_tags` as the canonical supervision layer
- Keep `numerals-tags` only as auxiliary metadata
