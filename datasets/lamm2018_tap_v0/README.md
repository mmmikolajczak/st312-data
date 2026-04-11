# lamm2018_tap_v0

Internal-only dataset module for Lamm et al. (2018), *Textual Analogy Parsing*.

## Current state
- raw release acquired and preserved locally
- processed benchmark-facing graph view built from author JSON release
- author train/test split preserved exactly as released
- local task smoke test passed
- published to the private HF dataset repo under the standard pipeline schema
- public redistribution rights remain uncleared

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
- The module is published to the private HF repo for internal pipeline use.
- Public redistribution permission remains unresolved.
