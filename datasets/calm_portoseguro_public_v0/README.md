# calm_portoseguro_public_v0

CALM-family benchmark-wrapper module over `CRA-ProtoSeguro` from `Salesforce/FinEval`.

## Current stance
- canonical benchmark release: `Salesforce/FinEval` subset `CRA-ProtoSeguro`
- benchmark release role in CALM metadata: `eval_only`
- CALM instruction style: `table_based`
- CALM minority-resampling training recipe flag: `false`
- best known raw source: Porto Seguro claim-status benchmark lineage as surfaced through CALM and FinEval public wrappers
- raw-source confidence: `low`
- public ST312 module type: eval-only benchmark wrapper over the public FinEval CRA subset

## Source-chain note
- benchmark release provenance is the strongest public anchor for this module
- underlying raw-source provenance should be treated according to the recorded confidence level, not as automatically source-canonical
- Keep spelling standardized to portoseguro in ST312 IDs. The wrapper should be treated as the canonical accessible release surface rather than as proof of a clean raw-source chain.
