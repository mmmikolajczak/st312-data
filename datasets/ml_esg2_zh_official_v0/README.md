# ml_esg2_zh_official_v0

Official shared-task release module for Chinese ML-ESG-2 ESG impact type classification from `ymntseng/DynamicESG`.

## Current stance
- official ML-ESG-2 Chinese shared-task split release only
- Chinese
- headline-only canonical input
- 5-way official single-label impact type classification
- no crawler enrichment included
- official `train / dev / test` split preserved exactly
- no binary or 3-way collapsing is applied
- family-stable `article_id` reused from the ML-ESG Chinese family
- family-stable `article_id` supports cross-task joins across ML-ESG-1, ML-ESG-2, ML-ESG-3, and future DynamicESG sibling modules

## Canonical provenance
- Official repo: `https://github.com/ymntseng/DynamicESG`
- Pinned source commit: `4f1bd162504c35df17100ff708ebdf04c68e2b10`
- Official split subtree: `data/ML-ESG-2_Chinese/`

## Key notes
- canonical input text is the released headline only
- source URL is preserved as metadata
- canonical target is a scalar `impact_type` label, normalized from the released singleton-list `Impact_Type`
- original singleton list is preserved in `source_impact_type_list` for auditability
- no article-body recovery is included
- no heuristic relabeling, class merging, or split modification is applied
- observed canonical split counts are `1260 / 140 / 156`
- observed released label inventory is `Opportunity, Risk, CannotDistinguish, NotRelatedtoCompany, NotRelatedtoESGTopic`
