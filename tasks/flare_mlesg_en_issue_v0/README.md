# flare_mlesg_en_issue_v0

Eval-only published multiclass classification task over `flare_mlesg_en_public_test_v0`.

## Formal task id
`TA_ESG_ISSUE_MLESG_EN_FLARE_v0`

## Input
- `data.text`

## Output
Return ONLY a JSON object with exactly one key:
- `issue`

Allowed label values:
- `Access to Communications`
- `Biodiversity & Land Use`
- `Packaging Material & Waste`
- `Financing Environmental Impact`
- `Carbon Emissions`
- `Human Capital Development`
- `Ownership & Control`
- `Community Relations`
- `Responsible Investment`
- `Opportunities in Renewable Energy`
- `Consumer Financial Protection`
- `Accounting`
- `Business Ethics`
- `Opportunities in Clean Tech`
- `Toxic Emissions & Waste`
- `Product Carbon Footprint`
- `Opportunities in Green Building`
- `Climate Change Vulnerability`
- `Pay`
- `Water Stress`
- `Supply Chain Labor Standards`
- `Chemical Safety`
- `Board`
- `Opportunities in Nutrition & Health`
- `Access to Health Care`
- `Electronic Waste`
- `Access to Finance`
- `Raw Material Sourcing`
- `Health & Demographic Risk`
- `Labor Management`
- `Controversial Sourcing`
- `Privacy & Data Security`
- `Product Safety & Quality`

## Evaluation
The evaluator reports:
- accuracy
- macro F1
- format-valid rate

## Reward stance
This task follows the standard simple-classification reward shape:
- 1 point for valid schema / valid label
- 1 point for exact label correctness

## Provenance note
- canonical artifact is the already-public `TheFinAI/flare-mlesg` wrapper
- this wrapper exposes a 33-label inventory, while the original ML-ESG paper discusses a 35-issue task

This module is eval-only. The evaluator remains the source of truth.
