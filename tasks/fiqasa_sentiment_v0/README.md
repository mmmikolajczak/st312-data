# FiQA Sentiment Task (v0)

Task module for FiQA-SA sentiment classification (3-way), using the upstream HF split and a discretised label from the continuous sentiment score.

## Task ID
`TA_SENT_FIQASA_v0`

## Dataset module
- Dataset ID: `fiqasa_hf_default_v0`
- Source files:
  - `data/fiqasa/processed/fiqasa_train_clean.jsonl`
  - `data/fiqasa/processed/fiqasa_valid_clean.jsonl`
  - `data/fiqasa/processed/fiqasa_test_clean.jsonl`

## Label scheme
Derived from `label.sentiment_score` using:
- `score <= -0.1` -> `negative`
- `score >=  0.1` -> `positive`
- otherwise -> `neutral`

## Input fields
Required:
- `data.text`
- `data.target`

Optional:
- `data.aspect`
- `data.type`

## Output schema (strict)
Return ONLY:
```json
{"sentiment": "negative" | "neutral" | "positive"}
```

No extra keys. No extra text.

## Scripts
- Reward parser: `scripts/tasks/fiqasa_sentiment_v0/reward_fiqasa.py`
- Prompt preview: `scripts/tasks/fiqasa_sentiment_v0/render_fiqasa_prompt.py`
- Request builder: `scripts/tasks/fiqasa_sentiment_v0/build_fiqasa_requests.py`
- Cached evaluator: `scripts/tasks/fiqasa_sentiment_v0/eval_fiqasa_cached.py`

## Typical workflow
1. Render prompt previews
2. Build request JSONL files
3. Run model externally / cache completions
4. Evaluate with cached evaluator

## Useful commands

### Reward smoke test
```bash
python scripts/tasks/fiqasa_sentiment_v0/reward_fiqasa.py --smoke-test
```

### Prompt preview
```bash
python scripts/tasks/fiqasa_sentiment_v0/render_fiqasa_prompt.py --split train --num 2
python scripts/tasks/fiqasa_sentiment_v0/render_fiqasa_prompt.py --split valid --num 2
python scripts/tasks/fiqasa_sentiment_v0/render_fiqasa_prompt.py --split test --num 2
```

### Build requests
```bash
python scripts/tasks/fiqasa_sentiment_v0/build_fiqasa_requests.py --split train
python scripts/tasks/fiqasa_sentiment_v0/build_fiqasa_requests.py --split valid
python scripts/tasks/fiqasa_sentiment_v0/build_fiqasa_requests.py --split test
```

### Evaluate cached completions
```bash
python scripts/tasks/fiqasa_sentiment_v0/eval_fiqasa_cached.py \
  --split test \
  --completions <PATH_TO_COMPLETIONS_JSONL>
```
