# tatqa_official_v0

Official TAT-QA hybrid financial QA module sourced from the pinned `NExTplusplus/TAT-QA` GitHub repository.

## Current stance
- official source repo and pinned commit are canonical
- pinned source commit: `644770eb2a66dddc24b92303bd2acbad84cd2b9f`
- canonical supervised publication preserves `train / dev / test` without resplitting
- canonical processed `test.jsonl` is derived from `tatqa_dataset_test_gold.json`, not the original unlabeled `tatqa_dataset_test.json`
- the original unlabeled `tatqa_dataset_test.json` is retained raw for provenance only and summarized via `original_test_summary.json`
- hybrid context is preserved as question + table + ordered paragraphs
- rich supervision fields are preserved in canonical processed rows: `derivation`, `answer_type`, `answer_from`, `rel_paragraphs`, `req_comparison`, and `scale`
- context-level release splits are preserved exactly; report-level disjointness is not guaranteed by the original release
- dataset content is CC BY 4.0, while repository code and official evaluation scripts are MIT-licensed

## Observed release counts at the pinned commit
- canonical train: `2201` contexts / `13215` questions
- canonical dev: `278` contexts / `1668` questions
- canonical test from `test_gold`: `277` contexts / `1663` questions
- original unlabeled challenge test retained raw-only: `278` contexts / `1669` questions

## Key notes
- the Jan 2024 upstream update released TAT-QA test-set ground truth, which is why the canonical supervised test split here comes from `tatqa_dataset_test_gold.json`
- the canonical scorer remains official answer+scale evaluation with exact match, F1, and scale score
- derivation and other auxiliary fields are preserved for richer supervision, but they are not the top-line benchmark contract
- canonical table and paragraph serializations are deterministic local renderings and do not reuse TagOp-specific heuristic preprocessing as the dataset layer
