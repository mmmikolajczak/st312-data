# flare_ma_public_test_v0

Eval-only published benchmark module for the public `TheFinAI/flare-ma` wrapper of the Yang et al. (COLING 2020) deal completeness classification task.

## Current stance
- canonical public artifact treated as eval-only benchmark input
- no full-source training dataset onboarding
- no fabricated train/validation split
- benchmark coverage limited to the public 500-example test wrapper
- published in the HF repo under the normal pipeline schema
- the full original Zephyr-derived corpus remains out of scope

## Canonical public artifact
- Hugging Face dataset: `TheFinAI/flare-ma`

## Important provenance note
The original Yang et al. dataset is described as being derived from Zephyr, a commercial M&A database.
This module therefore treats only the already-public benchmark wrapper as sourceable for pipeline use.

## Canonical split policy
- preserve the public `test` split exactly as exposed
- do not fabricate train or validation splits
