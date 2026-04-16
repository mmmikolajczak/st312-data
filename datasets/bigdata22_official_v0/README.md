# bigdata22_official_v0

Canonical dataset module for the original-paper BigData22 stock movement prediction benchmark.

## Current stance
- canonical source is the official `deeptrade-public/slot` GitHub repo pinned to commit `1c1a25671d4c81f5fcd45607447225862c308dd5`
- the repo README states that the repository stores the accepted paper and its dataset
- the repo has no tagged releases and does not expose explicit dataset split files
- canonical task is binary stock movement prediction from historical price features plus tweets
- paper-level labels follow the adjusted-close return thresholds `>= +0.55% -> rise`, `<= -0.5% -> fall`; raw release labels are preserved, canonical interface maps `1 -> Rise` and `-1 -> Fall`, and the neutral band `0` is excluded from the canonical binary task
- canonical scope for this module is the BigData22 paper window `2019-07-05` through `2020-06-30`
- the official archive also contains `acl18` and `cikm18`; those families are preserved raw for provenance but are not onboarded as canonical modules in this turn
- this module is publicly published in the standard artifact layout with an upstream rights / source-chain caution because the release surface does not expose a clear dataset redistribution license for the tweets and market data

## Preserved raw release
- `README.md`
- `Accurate Stock Movement Prediction with Self-supervised Learning from Sparse Noisy Tweets(BigData22).pdf`
- `data.zip`
- full extracted archive tree under `data/bigdata22_official/raw/extracted/`
- `download_meta.json`

## Canonical processed mapping
- one processed row per stock-date prediction instance
- `target_date` is the market day whose movement label is predicted
- `history_end_date` is the prior trading day that ends the model-visible history
- `price_history_rows` preserves the prior 30 structured price-feature rows ending at `history_end_date`
- `tweets` preserves the local ticker tweets available for `history_end_date`
- `gold_label` is the stable internal binary id `1 / 0`
- `gold_label_text` is the stable user-facing label `Rise / Fall`
- `original_release_label` preserves the raw release label `1 / -1`

## Split note
- the official archive does not ship explicit `train / valid / test` files or boundary dates
- the paper states only that the split is chronological, so ST312 derives a documented chronological `train / valid / test` reconstruction over sorted unique target trading dates inside the paper window after excluding neutral-band rows
- the current ST312-derived split uses `175 / 25 / 50` target-trading-date buckets and yields `5624 / 1164 / 2016` examples for `train / valid / test`
- the public wrapper `TheFinAI/en-forecasting-bigdata` exposes different counts over a broader date range and is treated only as a secondary comparison surface, not as the canonical source of truth
