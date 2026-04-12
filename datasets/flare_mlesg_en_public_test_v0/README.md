# flare_mlesg_en_public_test_v0

Eval-only published benchmark module for the public `TheFinAI/flare-mlesg` wrapper of the ML-ESG-1 English ESG issue identification task.

## Current stance
- canonical public artifact treated as eval-only benchmark input
- no full-source training dataset onboarding
- no fabricated train/validation split
- benchmark coverage limited to the public 300-example test wrapper
- published in the HF repo under the normal pipeline schema
- the full original ML-ESG-1 English corpus remains out of scope

## Canonical public artifact
- Hugging Face dataset: `TheFinAI/flare-mlesg`

## Important provenance note
The original ML-ESG-1 English task is described in the paper as a larger 35-issue benchmark with 1,199 train and 300 test examples.
This module instead treats only the already-public FLARE / FinBen wrapper as sourceable for pipeline use.

## Label inventory note
- the public wrapper exposes a single ordered 33-label choice inventory
- the original ML-ESG paper discusses a 35-issue task
- this module uses the wrapper-realized 33-label inventory as the canonical eval target

## Canonical split policy
- preserve the public `test` split exactly as exposed
- do not fabricate train or validation splits
