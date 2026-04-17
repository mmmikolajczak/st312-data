# calm_polish_public_v0

CALM-family benchmark-wrapper module over `CRA-Polish` from `Salesforce/FinEval`.

## Current stance
- canonical benchmark release: `Salesforce/FinEval` subset `CRA-Polish`
- benchmark release role in CALM metadata: `eval_only`
- CALM instruction style: `description_based`
- CALM minority-resampling training recipe flag: `false`
- best known raw source: UCI Polish Companies Bankruptcy
- raw-source confidence: `high`
- public ST312 module type: eval-only benchmark wrapper over the public FinEval CRA subset

## Source-chain note
- benchmark release provenance is the strongest public anchor for this module
- underlying raw-source provenance should be treated according to the recorded confidence level, not as automatically source-canonical
- The benchmark release is wrapper-based, but the raw-source lineage is strong enough that a future source-canonical alignment audit is appropriate.
