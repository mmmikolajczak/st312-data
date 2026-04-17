# statlog_german_credit_uci_v0

Canonical dataset module for the UCI Statlog (German Credit Data) archive.

## Current stance
- canonical source is the UCI Statlog (German Credit Data) archive, DOI `10.24432/C5NC77`
- canonical raw files are `german.data`, `german.data-numeric`, and `german.doc`
- canonical preserved source surface is the original symbolic `german.data` file; `german.data-numeric` is retained as an auxiliary raw artifact only
- original UCI columns `Attribute1` through `Attribute20` and `Class` are preserved in processed rows, together with original row order via `uci_row_index`
- the public wrapper `TheFinAI/german-credit-benchmark` is used only to replicate a `700 / 100 / 200` split after exact row-level matching; it is not the provenance source of truth
- default evaluation is cost-sensitive because UCI explicitly states the task requires the cost matrix `[[0,1],[5,0]]` over classes `1 = Good`, `2 = Bad`
- the dataset contains sensitive demographic-style variables including personal status and sex, age in years, and foreign-worker status; ST312 treats it as a historical benchmark, not a deployment template
- canonical source license is CC BY 4.0, so this module is intended for normal public artifact publication with attribution

## Canonical processed mapping
- one processed row preserves `uci_row_index`, `Attribute1..Attribute20`, and `Class`
- `label_int_uci` preserves the source target exactly as `1` or `2`
- `label_text` maps source labels to lower-case `good` / `bad`
- `feature_pairs_decoded` preserves an ordered decoded rendering for each original attribute without mutating the canonical source columns
- `feature_text_decoded` provides a deterministic LLM-friendly prompt surface in original UCI feature order

## Split policy
- UCI does not publish an official supervised split on the archive page
- ST312 therefore reuses the public wrapper split only if exact row-level replication succeeds against all 1,000 UCI rows
- no fallback split is invented in this implementation pass; failure to replicate exactly is a publication blocker

