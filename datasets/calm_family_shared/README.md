# CALM Family Shared Notes

This directory records shared metadata for the CALM benchmark-wrapper family integrated into ST312.

## Canonical benchmark release

- canonical public benchmark release: `Salesforce/FinEval`
- CRA subsets are treated as the canonical public benchmark release surface for CALM-family onboarding
- CALM's public repository remains the source of truth for role split, instruction style, and minority-resampling training-recipe notes

## Shared family flags

Every CALM-family module records:

- `calm_family`
- `calm_instruction_style`
- `calm_role`
- `calm_training_recipe_minority_resampled`

These family flags are metadata about the original CALM benchmark/training recipe. They do not imply that the public benchmark release exposes the same supervised split structure as the original CALM workflow.

## Source-chain confidence note template

Use the following wording pattern in dataset READMEs and specs:

1. Canonical benchmark release: identify the `Salesforce/FinEval` CRA subset and pinned revision.
2. Best known raw source: identify the strongest underlying source lineage available from public evidence.
3. Raw-source confidence: record `high`, `medium`, or `low`.
4. Caution note:
   - `high`: benchmark release is wrapper-based, but the underlying raw-source lineage is strong enough for future source-canonical audit work.
   - `medium`: benchmark release provenance is stronger than the raw-source trail; raw-source linkage should be treated as indicative rather than canonical.
   - `low`: benchmark release should be treated as the main canonical accessible surface, and downstream users should not infer source-canonical alignment or redistribution rights from the weaker raw-source trail.

## Family-specific caution

Several CALM datasets concern credit, fraud, distress, and insurance decisions over human or company profiles. They can contain sensitive attributes, post-outcome leakage fields, highly imbalanced label distributions, or feature surfaces that are hard to interpret semantically. ST312 treats them as benchmark artifacts rather than deployment templates.
