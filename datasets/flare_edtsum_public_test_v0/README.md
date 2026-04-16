# flare_edtsum_public_test_v0

License-sensitive, eval-first wrapper over the gated Hugging Face dataset `TheFinAI/flare-edtsum`.

## Current stance
- canonical source is the gated HF dataset `TheFinAI/flare-edtsum`
- ST312 treats this task as financial news headline generation, or headline-style abstractive summarization, not generic long-form summarization
- the visible upstream surface exposes only a single `test` split with 2,000 examples
- no train or validation split is fabricated in the canonical benchmark module
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

## Canonical public artifact
- Hugging Face dataset: `TheFinAI/flare-edtsum`

## Source-chain note
- FinBen describes EDTSUM as manually selected and cleaned from Zhou et al. (2021)
- public OpenFinLLM documentation describes EDTSUM as financial news paired with their headlines as ground-truth summaries
- the deeper EDT lineage uses financial news / press-release text sourced from PRNewswire, Businesswire, and GlobeNewswire
- This module is publicly published in the ST312 artifact store, but `public_release_cleared` remains `false`; upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review.

## Observed raw wrapper schema
- raw release files observed at the pinned revision: `.gitattributes`, `README.md`, and one parquet shard
- the parquet wrapper exposes exactly four fields: `id`, `query`, `answer`, and `text`
- `text` is the full source article text
- `answer` is the reference headline / title target
- `query` is a prompt-prefixed wrapper field and is preserved for provenance rather than discarded

## Canonical processed mapping
- `id` preserves the upstream identifier verbatim
- `query`, `text`, and `answer` are preserved verbatim after minimal line-ending / trailing-whitespace normalization
- `article_text` is the canonical alias for `text`
- `reference_headline` is the canonical alias for `answer`
- `task_target_type` is fixed to `headline_generation`

## Data-quality and task-quality notes
- EDTSUM is effectively headline generation. ST312 therefore frames the task as article-to-headline generation rather than plain free-form summarization.
- The corpus is broad and somewhat noisy. Visible examples include press-release-style announcements and corporate disclosures in addition to newsroom prose.
- Input lengths vary substantially. In the observed wrapper, `query` reaches about 58.9k characters and `text` about 58.6k characters.
- Metric documentation differs across public surfaces. FinBen reports ROUGE, BERTScore, and BARTScore, while OpenFinLLM surfaces emphasize ROUGE and BERTScore.
- ST312 keeps both a stable default evaluation view and a best-effort FinBen-paper-aligned view.
