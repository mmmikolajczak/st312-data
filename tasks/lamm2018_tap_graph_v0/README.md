# lamm2018_tap_graph_v0

Internal-only TAP graph prediction task for `lamm2018_tap_v0`.

## Formal task id
`TA_GRAPH_TAP_LAMM2018_v0`

## Input
- `data.sentence`
- `data.tokens`

## Target
Predict the benchmark-facing TAP graph:
- node labels: `agent`, `cause`, `co_quant`, `location`, `manner`, `quant`, `source`, `theme`, `time`, `value`, `whole`
- edge labels: `analogy`, `equivalence`, `fact`

## Output
Return only a JSON object with:
- `nodes`
- `edges`

Each node must have:
- `id`
- `label`
- `token_start`
- `token_end`

Each edge must have:
- `source_id`
- `target_id`
- `label`

## Evaluation
Local evaluator reports:
- overlap-based triple F1
- node F1 excluding `value`
- exact graph match
- validity / coverage

## Publication status
Published to the private HF dataset repo under the standard pipeline schema.
Public redistribution clearance remains unresolved.
