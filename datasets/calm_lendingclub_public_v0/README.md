# calm_lendingclub_public_v0

CALM-family benchmark-wrapper module over `CRA-LendingClub` from `Salesforce/FinEval`.

## Current stance
- canonical benchmark release: `Salesforce/FinEval` subset `CRA-LendingClub`
- benchmark release role in CALM metadata: `eval_only`
- CALM instruction style: `description_based`
- CALM minority-resampling training recipe flag: `false`
- best known raw source: Lending Club accepted-loans public release lineage, commonly mirrored through Kaggle derivatives
- raw-source confidence: `medium`
- public ST312 module type: eval-only benchmark wrapper over the public FinEval CRA subset

## Source-chain note
- benchmark release provenance is the strongest public anchor for this module
- underlying raw-source provenance should be treated according to the recorded confidence level, not as automatically source-canonical
- Observed wrapper fields include likely post-outcome or downstream lending signals such as lastPaymentAmount, grade, and interestRate. ST312 treats this as a benchmark wrapper rather than a source-canonical underwriting dataset.
