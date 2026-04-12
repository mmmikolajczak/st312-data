# ml_esg1_zh_official_v0

Official shared-task release module for Chinese ML-ESG-1 ESG issue identification from `ymntseng/DynamicESG`.

## Current stance
- official shared-task release only
- Chinese
- headline-only canonical input
- multi-label ESG issue identification over released code labels
- no crawler enrichment included
- official `train / dev / test` split preserved exactly
- labels preserved exactly as released
- family-stable `article_id` added to support future ML-ESG-2 integration
- future ML-ESG-2 will be published as a separate dataset/task module

## Canonical provenance
- Official repo: `https://github.com/ymntseng/DynamicESG`
- Pinned source commit: `4f1bd162504c35df17100ff708ebdf04c68e2b10`
- Official split subtree: `data/ML-ESG-1_Chinese/`

## Key notes
- canonical input text is the released headline only
- source URL is preserved as metadata
- labels are stored as sorted unique code lists per row
- no article-body recovery is included
- no heuristic relabeling or split modification is applied
- the pinned official DynamicESG release differs from the FinNLP 2023 workshop paper statistics; this module follows the pinned release as canonical source of truth
- observed canonical split counts are `1058 / 118 / 131`
- observed released label inventory size is `48` codes
