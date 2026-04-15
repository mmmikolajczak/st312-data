# regulations_public_test_v0

Eval-only FinBen Regulations wrapper sourced from the gated Hugging Face dataset `TheFinAI/regulations`.

## Current stance
- canonical source is the gated HF dataset `TheFinAI/regulations`
- exact pinned HF revision used for this module: `918111376d5be0f97306f1e0b821529b4021da0b`
- the visible public release surface showed only `README.md` and `test_regulations.json`
- no public `train` or `dev` release was found during due diligence, so this module is treated as eval-only
- canonical published split is `test` only
- the authenticated gated wrapper contains 254 labeled test examples
- this task belongs to the FinBen long-form QA family and focuses on financial-regulation questions such as EMIR
- public provenance and annotation detail are limited compared with FinQA, TAT-QA, and ConvFinQA
- the visible wrapper license field is MIT, but provenance clarity is limited and users should review upstream gating and use conditions carefully

## Observed raw wrapper schema
- one JSON object per line in `test_regulations.json`
- top-level fields observed: `id`, `query`, `answer`, `text`
- `text` is the bare question
- `query` is a prompt-prefixed version of the same question and is preserved as source metadata
- no explicit context, regulation excerpt, jurisdiction, or source-document field is present in the released wrapper

## Canonical processed mapping
- `question` = raw `text`
- `reference_answer` = raw `answer`
- `source_query` preserves the prompt-prefixed raw `query`
- `context` and other source-document metadata remain `null` because they are not provided in the wrapper
