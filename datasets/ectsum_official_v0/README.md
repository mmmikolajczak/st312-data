# ectsum_official_v0

Canonical dataset module for the original-paper ECTSum benchmark.

## Current stance
- canonical source is the official `rajdeep345/ECTSum` GitHub repo pinned to commit `6909f1fc543104c1c60cf9de63e799f6620d1b0a`
- the repo has no tagged releases
- canonical task is bullet-style summarization of the Prepared Remarks section of earnings-call transcripts
- the paper reports 2,425 cleaned transcript-summary pairs with a random `70 / 10 / 20` split
- the source chain involves Motley Fool earnings-call transcripts and Reuters summary text
- this module is publicly published in the standard artifact layout with an upstream licensing / redistribution caution
- canonical task framing follows the original paper rather than a FinBen-only wrapper

## Preserved raw release
- `data/final/train/ects/` and `data/final/train/gt_summaries/`
- `data/final/val/ects/` and `data/final/val/gt_summaries/`
- `data/final/test/ects/` and `data/final/test/gt_summaries/`
- `README.md`
- `LICENSE.txt`
- `evaluate.py`
- `prepare_data_ectbps_ext.py`
- `prepare_data_ectbps_para.py`

## Canonical processed mapping
- one processed row per transcript-summary pair
- `transcript_text` preserves the prepared-remarks transcript with newline joins
- `transcript_lines` preserves the ordered raw transcript lines
- `reference_summary` preserves the gold summary text with newline joins
- `reference_bullets` preserves the ordered summary bullet lines
- `source_section` is fixed to `prepared_remarks`

## Publication note
- artifacts are published in the normal ST312 HF artifact layout
- upstream source-chain licensing should be reviewed before reuse
- metadata and publish bookkeeping carry a concise redistribution caution rather than a non-public release restriction
