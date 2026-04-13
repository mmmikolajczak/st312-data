# finqa_official_v0

Official FinQA program-generation module sourced from the pinned `czyssrs/FinQA` GitHub repository.

## Current stance
- official source repo and pinned commit are canonical
- the repo has no tagged releases, so the exact Git commit matters for reproducibility
- the official README documents 2022 bugfix history that matters for reproducibility
- canonical public supervised splits are `train / dev / test`
- `private_test.json` is kept raw for provenance only and is not part of the supervised canonical publication
- a small non-sensitive `private_test_summary.json` provenance artifact may be published to document count and exclusion policy without releasing raw private-test content
- canonical task target is executable program generation in the FinQA DSL, not answer-only QA
- schema drift exists between the official repo README summary and secondary loaders or mirrors, so this module follows the empirically observed pinned-repo schema
- official source repo license is MIT; the Hugging Face mirror metadata differs and is not treated as canonical

## Canonical provenance
- Official repo: `https://github.com/czyssrs/FinQA`
- Pinned source commit: `0f16e2867befa6840783e58be38c9efb9229d742`
- Canonical public supervised files:
  - `dataset/train.json`
  - `dataset/dev.json`
  - `dataset/test.json`
- Raw provenance-only file:
  - `dataset/private_test.json`

## Key notes
- canonical evidence preserves `pre_text`, `table`, and `post_text`
- canonical target preserves the gold executable reasoning program and gold execution answer
- the final answer is treated as a byproduct of executing the gold or predicted program
- deterministic table serialization is implemented locally and does not reuse the bug-prone legacy `table_row_to_text` helper from the original retriever code
- split-level report/page overlap is audited using `report_page_id`
