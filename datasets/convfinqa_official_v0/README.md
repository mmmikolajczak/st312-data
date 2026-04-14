# convfinqa_official_v0

Official ConvFinQA program-generation module sourced from the pinned `czyssrs/ConvFinQA` GitHub repository.

## Current stance
- official source repo and pinned commit are canonical
- the repo has no tagged releases, so the exact Git commit matters for reproducibility
- ConvFinQA is a FinQA-family conversational derivative, not an independent evidence-source family
- canonical modeling unit is turn-level, not conversation-level
- canonical task target is executable program generation in the FinQA DSL, not answer-only conversational QA
- public test-label availability was explicitly audited at the pinned commit
- the pinned official release exposes labeled `train_turn.json` and `dev_turn.json`, but only unlabeled `test_private.json` and `test_turn_private.json`
- this module therefore publishes supervised `train / dev` only; test is raw-only provenance summarized by `test_release_summary.json`
- conversation-level files are preserved raw for provenance and possible future tasks, but are not the canonical processed unit
- some `number_turn` examples use a single numeric program token followed by `EOF`; this matches the upstream conversion/evaluation behavior and is treated as canonical
- upstream license surface is MIT per the official repo

## Canonical provenance
- Official repo: `https://github.com/czyssrs/ConvFinQA`
- Pinned source commit: `cf3eed2d5984960bf06bb8145bcea5e80b0222a6`
- Raw conversation-level files:
  - `data/train.json`
  - `data/dev.json`
  - `data/test_private.json`
- Raw turn-level files:
  - `data/train_turn.json`
  - `data/dev_turn.json`
  - `data/test_turn_private.json`

## Key notes
- canonical evidence preserves `pre_text`, `table`, `post_text`, dialogue history, and the current question
- canonical gold target is the current-turn executable reasoning program
- the final answer is treated as a byproduct of executing the gold or predicted program
- training on FinQA plus ConvFinQA does not add fully independent source evidence, because ConvFinQA is constructed from FinQA-family material
