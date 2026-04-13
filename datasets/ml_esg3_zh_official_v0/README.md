# ml_esg3_zh_official_v0

Official shared-task release module for Chinese ML-ESG-3 ESG impact duration classification from `ymntseng/DynamicESG`.

## Current stance
- official ML-ESG-3 Chinese shared-task split release only
- Chinese
- headline-only canonical input
- 5-way official single-label impact duration classification
- no crawler enrichment included
- official `train / dev / test` split preserved exactly
- no collapsed 3-label alternative view is used as the canonical artifact
- family-stable `article_id` reused from the DynamicESG Chinese family

## Canonical provenance
- Official repo: `https://github.com/ymntseng/DynamicESG`
- Pinned source commit: `4f1bd162504c35df17100ff708ebdf04c68e2b10`
- Official split subtree: `data/ML-ESG-3_Chinese/`

## Key notes
- canonical input text is the released headline only
- source URL is preserved as metadata
- canonical target is a scalar `impact_duration` label, normalized from the released singleton-list `Impact_Duration`
- original singleton list is preserved in `source_impact_duration_list` for auditability
- no article-body recovery is included
- no heuristic relabeling, class collapsing, or split modification is applied
- observed canonical split counts are `995 / 111 / 123`
- observed released label inventory is `<2, 2~5, >5, NotRelatedtoCompany, NotRelatedtoESGTopic`
- the pinned released JSON is broader than the narrower 3-duration-label workshop framing, so this module treats the released 5-label single-label space as canonical
