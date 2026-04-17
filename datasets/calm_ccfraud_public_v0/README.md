# calm_ccfraud_public_v0

CALM-family benchmark-wrapper module over `CRA-CCFraud` from `Salesforce/FinEval`.

## Current stance
- canonical benchmark release: `Salesforce/FinEval` subset `CRA-CCFraud`
- benchmark release role in CALM metadata: `train_eval`
- CALM instruction style: `description_based`
- CALM minority-resampling training recipe flag: `true`
- best known raw source: ccFraud benchmark lineage as surfaced through CALM and FinEval public wrappers
- raw-source confidence: `low`
- public ST312 module type: eval-only benchmark wrapper over the public FinEval CRA subset

## Source-chain note
- benchmark release provenance is the strongest public anchor for this module
- underlying raw-source provenance should be treated according to the recorded confidence level, not as automatically source-canonical
- The public benchmark release provenance is stronger than the raw-source trail. ST312 treats the FinEval wrapper as the canonical accessible surface and records CALM's minority-resampling note as training metadata only.
