# Australian Credit UCI Statlog v0

Canonical raw-source dataset module for the UCI Statlog (Australian Credit Approval) dataset.

## Canonical source stance

- Canonical raw source is the UCI Statlog (Australian Credit Approval) release
- FLARE / FinBen promptified wrappers are treated as derived downstream reformulations, not canonical source
- Raw UCI files are preserved unchanged in the raw layer

## Integration stance

- Clean canonical tabular artifact uses anonymized features `A1`-`A14`
- Binary target is normalized to:
  - `label_id = 0` -> `Reject`
  - `label_id = 1` -> `Approve`
- Split policy is:
  - exact FLARE membership if verifiable
  - otherwise fixed-seed count-matched reconstruction to `482 / 69 / 139`

## Important metadata cautions

- UCI notes anonymized / semantically opaque attributes
- UCI documentation around missing values is ambiguous and is recorded as such in metadata
