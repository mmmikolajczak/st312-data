# calm_taiwan_public_v0

CALM-family benchmark-wrapper module over `CRA-Taiwan` from `Salesforce/FinEval`.

## Current stance
- canonical benchmark release: `Salesforce/FinEval` subset `CRA-Taiwan`
- benchmark release role in CALM metadata: `train_eval`
- CALM instruction style: `description_based`
- CALM minority-resampling training recipe flag: `true`
- best known raw source: UCI Taiwanese Bankruptcy Prediction
- raw-source confidence: `high`
- public ST312 module type: eval-only benchmark wrapper over the public FinEval CRA subset

## Source-chain note
- benchmark release provenance is the strongest public anchor for this module
- underlying raw-source provenance should be treated according to the recorded confidence level, not as automatically source-canonical
- The FinEval CRA subset is the canonical public benchmark release surface for this module. ST312 records the stronger UCI source lineage for future source-canonical audit work, but does not reconstruct or replace the public benchmark wrapper in this pass.
