# flare_ma_public_test_v0

Eval-only benchmark module for the public `TheFinAI/flare-ma` wrapper of the Yang et al. (COLING 2020) deal completeness classification task.

## Current stance
- public artifact treated as canonical eval input
- no full-source training dataset onboarding
- no synthetic train/validation split
- benchmark coverage limited to the public 500-example test wrapper
- suitable for evaluation, not for training-data republication claims

## Canonical public artifact
- Hugging Face dataset: `TheFinAI/flare-ma`

## Important provenance note
The original Yang et al. dataset is described as being derived from Zephyr, a commercial M&A database.
This module therefore treats only the already-public benchmark wrapper as sourceable for pipeline use.

## Canonical split policy
- preserve the public `test` split exactly as exposed
- do not fabricate train or validation splits
