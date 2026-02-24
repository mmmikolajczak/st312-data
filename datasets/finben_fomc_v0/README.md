# FinBen FOMC Dataset Module (v0)

Dataset module for `TheFinAI/finben-fomc`, converted into the ST312 canonical format.

## Dataset ID
`finben_fomc_v0`

## Upstream source
- Hugging Face dataset: `TheFinAI/finben-fomc`

## Label scheme
3-way categorical monetary-policy stance:
- `dovish`
- `hawkish`
- `neutral`

Labels are taken from the upstream annotation (`answer`, with cross-check against `gold` + `choices`).

## Split policy
Upstream provides only a single split (`test`), so we create a local reproducible stratified split:
- train: 80%
- test: 20%
- stratified by `label.stance`
- seed: 42
