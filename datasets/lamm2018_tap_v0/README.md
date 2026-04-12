# lamm2018_tap_v0

Dataset module for Lamm et al. (2018), *Textual Analogy Parsing*.

## Current state
- raw release acquired and preserved locally
- processed benchmark-facing graph view built from the author JSON release
- author train/test split preserved exactly as released
- task module implemented and smoke-tested successfully
- canonical processed artifacts and task requests published to the HF dataset repo
- public redistribution approval remains pending

## Canonical source
Author repository:
- `mrlamm/textual-analogy-parsing`

Released source files under `data/`:
- `train.json`
- `test.json`
- `train.xml`
- `test.xml`

## Processed representation
Each processed example preserves:
1. `label.raw_graph`: raw author graph
2. `label.benchmark_graph`: benchmark-facing prune-plus-argmax graph

## Audit notes
- The released `test.json` contains 97 examples, not 100.
- The benchmark-facing graph uses the reduced active label inventory found in the author code path.
- The module is published in the HF repo under the normal pipeline schema.
- Public redistribution permission remains under review.
