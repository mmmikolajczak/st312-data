# flare_sm_cikm_public_v0

Wrapper-based canonical accessible CIKM18-family dataset module built from the public Hugging Face dataset `TheFinAI/flare-sm-cikm`.

## Current stance
- canonical accessible source surface is `TheFinAI/flare-sm-cikm` pinned to revision `af627b4405e69e298ec45505c91dc17395be712b`
- the original first-party CIKM18 author release is publicly unrecoverable from the author repo plus linked Baidu Pan source, so this module is explicitly wrapper-based rather than an original-author release
- the wrapper `train / valid / test` split is preserved exactly as observed: `3396 / 431 / 1143` rows, `4970` total
- raw wrapper fields are preserved canonically as `id`, `query`, `answer`, `text`, `choices`, and `gold`, with ST312 normalization layered on top without discarding the wrapper surface
- original-paper conventions are preserved where still supportable: binary next-day movement framing, no neutral-band semantics in the canonical label interpretation, and `accuracy` as the default original-like metric
- public-surface drift is documented rather than normalized away:
  - wrapper page reports roughly `4.97k` rows
  - OpenFinLLM docs say `4,967`
  - OpenFinLLM docs also drift from original-paper semantics on threshold wording and `accuracy + mcc`
- publication is public, but carries an upstream/source-chain caution because the wrapper sits over an unrecoverable original dataset family built from market data and social text

## Canonical processed mapping
- one processed row per wrapper example
- `query` is preserved exactly as the wrapper prompt field
- `context_text` is preserved exactly as wrapper `text`
- `wrapper_answer_text` preserves the wrapper string answer verbatim
- `wrapper_gold_int` preserves the wrapper integer label exactly
- `gold_label_text` is the canonical ST312 label `Rise` or `Fall`
- `gold_label` is the canonical binary id `1` for `Rise`, `0` for `Fall`
- optional enrichments such as `ticker`, `target_date`, `price_history_block`, and `social_text_block` are extracted only when they are robustly parseable from the wrapper surface

## Gold-label mapping audit
- the integer-to-label mapping is derived empirically by cross-tabulating wrapper `answer` against wrapper `gold` on each split
- observed consistent mapping at the pinned revision:
  - `0 -> Rise`
  - `1 -> Fall`
- this mapping is recorded in `label_inventory.json`, `ingest_summary.json`, and `reports/flare_sm_cikm_public/ingest_audit.json`

## Provenance note
- original-paper CIKM18 is a first-party stock movement benchmark over Yahoo Finance price data and Twitter text
- this module does not claim to recover the first-party author release
- this module is the canonical accessible ST312 surface for that family because the original first-party release is publicly unrecoverable
