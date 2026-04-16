# stocknet_acl18_paper_v0

Canonical dataset module for the ACL 2018 StockNet stock movement prediction benchmark.

## Current stance
- canonical source is the official `yumoxu/stocknet-dataset` GitHub repository pinned to commit `330708b5ddc359961078bef469f43f48992fd6e4`
- canonical paper is Xu & Cohen (ACL 2018), not the later FLARE / FinBen wrapper
- canonical benchmark scope is the paper window `2014-01-01` through `2016-01-01` over the paper's temporal `train / dev / test` split
- canonical task is binary stock movement forecasting from aligned tweet corpora plus historical stock prices
- canonical label thresholds are `<= -0.5% -> Fall` and `> 0.55% -> Rise`, with the middle band removed
- the official release reproduces the paper's exact `20,339 / 2,555 / 3,720` split counts and `26,614` total when the paper's split boundaries, 5-day alignment, and threshold rule are preserved
- the FLARE wrapper `TheFinAI/flare-sm-acl` is audited only as a compatibility surface and is not the canonical source of truth
- this module is publicly published in the normal ST312 artifact layout with a small source-terms caution
- Original source repository is MIT-licensed. The released corpus includes tweet-derived content collected under Twitter's official license and price data sourced from Yahoo Finance; downstream users should review applicable platform/source terms before reuse.

## Important source discrepancy
- the paper states that samples were further filtered to ensure tweet presence in the lag
- the official StockNet release and the official stocknet-code reference do not reproduce the paper counts under that extra hard filter
- across every official dataset snapshot containing the released data, enforcing an at-least-one-tweet-in-lag rule drops the corpus to `18,695` examples instead of `26,614`
- ST312 therefore preserves the exact paper counts as the canonical benchmark invariant and records the tweet-sparsity discrepancy explicitly in the reconstruction audit

## Preserved raw release
- `README.md`
- `LICENSE`
- `StockTable`
- `appendix_table_of_target_stocks.pdf`
- full `price/` and `tweet/` trees under `data/stocknet_acl18_paper/raw/source_snapshot/`
- `download_meta.json`
- `source_snapshot_checksums.sha256`

## Canonical processed mapping
- one processed row per stock-date prediction target
- `aligned_days` preserves the paper-style trading-day alignment units used for forecasting
- each aligned trading day stores the aligned tweet texts plus the historical price features used for that trading-day prediction step
- `auxiliary_targets` preserves the ordered labels for earlier aligned trading days inside the sample
- `label_int` / `label_text` preserve the canonical binary target as `0 / Fall` and `1 / Rise`
- `target_price_prev_adj_close` and `target_price_adj_close` preserve the raw adjusted-close values underlying the main target movement

## Split note
- canonical splits are preserved exactly from the paper as half-open target-date intervals
- `train`: `2014-01-01 <= target_date < 2015-08-01`
- `dev`: `2015-08-01 <= target_date < 2015-10-01`
- `test`: `2015-10-01 <= target_date < 2016-01-01`
- exact reconstructed counts are `20,339 / 2,555 / 3,720`
