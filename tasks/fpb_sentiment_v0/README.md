# FPB Sentiment Task (v0)

This is the first ST312 data task module, based on **Financial PhraseBank** (all-agree subset), built as a **Risko-1-style** pipeline component:

- reproducible local scripts
- deterministic processed dataset
- explicit task spec (prompt + output schema)
- robust parser / reward functions
- cached-completions evaluator
- model-request JSONL builder for pipeline handoff

---

## 1) Task identity

### Task ID
`TA_SENT_FPB_v0`

### Purpose
Financial sentiment classification with a **strict JSON output schema**:

```json
{"sentiment": "negative" | "neutral" | "positive"}
```

### Why this task was chosen first
This is a strong “confidence builder” task because it is:
- easy to score deterministically (exact-match label classification)
- simple output format (single label in JSON)
- ideal for testing the full prompt → parse → reward → eval loop before harder tasks (NER/RE/QA/numeric)

---

## 2) Pipeline overview (what exists already)

This task module currently includes the full data/eval side of the pipeline:

1. **Raw ingest**
   - Download official Financial PhraseBank ZIP
   - Parse `sentence@label` lines into raw JSONL

2. **Cleaning / standardization**
   - Add stable deterministic `example_id`
   - Standardize fields into:
     - `data.text`
     - `label.sentiment`

3. **Deterministic train/test split**
   - Stratified by sentiment label
   - Fixed seed
   - Split metadata saved (counts, seed, proportions)

4. **Task specification**
   - Prompt template
   - Output schema
   - Reward components
   - Evaluation metrics

5. **Reward parser + reward functions**
   - Robust JSON extraction
   - Schema validation
   - Format reward
   - Correctness reward
   - Combined reward

6. **Prompt renderer**
   - Preview exactly what the model will see (system + user prompts)

7. **Cached completions evaluator**
   - Evaluate model outputs from JSONL cache:
     - coverage
     - format-valid rate
     - accuracy
     - macro-F1
     - per-class metrics

8. **Request builder**
   - Build model-ready `messages` JSONL rows from train/test splits

---

## 3) Source-of-truth files

### A) Task spec (prompt + schema + reward spec)
- `tasks/fpb_sentiment_v0/task_spec.json`

This is the main contract between:
- your data/prompt pipeline
- Marco’s model/training pipeline

---

### B) Dataset files (processed, local only by default)
- Train examples: `data/fpb/processed/fpb_allagree_train.jsonl`
- Test examples: `data/fpb/processed/fpb_allagree_test.jsonl`
- Split metadata: `data/fpb/processed/fpb_allagree_split_meta.json`

These are generated locally and are **not committed to git** (the `data/` directory is intentionally ignored).

---

### C) Model request files (ready for inference/training)
- Train requests: `data/fpb/processed/fpb_allagree_train_requests.jsonl`
- Test requests: `data/fpb/processed/fpb_allagree_test_requests.jsonl`

These are also generated locally (not committed).

---

### D) Core scripts
- Ingest raw FPB ZIP: `scripts/ingest_fpb.py`
- Clean + add stable IDs: `scripts/clean_fpb.py`
- Stratified split: `scripts/split_fpb.py`
- Reward parser / rewards: `scripts/reward_fpb.py`
- Prompt preview renderer: `scripts/render_fpb_prompt.py`
- Cached completions evaluator: `scripts/eval_fpb_cached.py`
- Request builder (messages JSONL): `scripts/build_fpb_requests.py`

---

## 4) Dataset and split details

### Dataset
Financial PhraseBank (`allagree` subset)

### Split method
- stratified by `label.sentiment`
- test fraction = `0.2`
- seed = `42`

### Current split sizes
- Train: `1811`
- Test: `453`
- Total: `2264`

Exact counts are recorded in:
- `data/fpb/processed/fpb_allagree_split_meta.json`

---

## 5) Processed dataset row format (standardized examples)

Each processed example row looks like:

```json
{
  "example_id": "197d178dc7ad1fda",
  "dataset_id": "fpb",
  "config": "allagree",
  "data": {
    "text": "According to Gran , the company has no plans to move all production to Russia ..."
  },
  "label": {
    "sentiment": "neutral"
  },
  "meta": {
    "source": "takala/financial_phrasebank"
  }
}
```

### Notes
- `example_id` is deterministic (hash of config + sentence)
- This makes examples stable across reruns and useful for split tracking / cached evaluation

---

## 6) Prompt contract (what the model should see)

### System prompt
Defined in `task_spec.json` and injected into every request.

Current system prompt:
> You are a financial sentiment classifier. Return ONLY a JSON object with exactly one key: "sentiment". The value must be one of: "negative", "neutral", "positive". Do not include any extra text.

### User prompt template
Defined in `task_spec.json`:

```text
Classify the sentiment of the following financial sentence.

Sentence: {{data.text}}
```

This is rendered per-example using `record["data"]["text"]`.

---

## 7) Request JSONL format (input to model pipeline)

The request builder creates a model-ready JSONL file with one row per example.

### Required fields per row
- `example_id` (string)
- `task_id` (string)
- `messages` (chat-style list)

### Example request row
```json
{
  "example_id": "4431dd3025767640",
  "task_id": "TA_SENT_FPB_v0",
  "messages": [
    {
      "role": "system",
      "content": "You are a financial sentiment classifier. Return ONLY a JSON object with exactly one key: \"sentiment\". The value must be one of: \"negative\", \"neutral\", \"positive\". Do not include any extra text."
    },
    {
      "role": "user",
      "content": "Classify the sentiment of the following financial sentence.\n\nSentence: Earlier today , Geberit's Finnish rival ..."
    }
  ]
}
```

### Optional debug field
The request builder can include:
- `gold_label`

This is useful for preview/debugging, but not necessary for training.

---

## 8) Expected completions JSONL format (output from model pipeline)

Marco’s inference/training pipeline should write a JSONL file where each row contains:

- `example_id` (must match a dataset/request example ID)
- `output_text` (raw model output text)

### Example completions row
```json
{
  "example_id": "4431dd3025767640",
  "output_text": "{\"sentiment\":\"negative\"}"
}
```

### Important
The evaluator expects these exact field names:
- `example_id`
- `output_text`

If the model pipeline uses different names, either:
- rename them before evaluation, or
- update `scripts/eval_fpb_cached.py`

---

## 9) Output schema (strict)

The desired output JSON schema is:

```json
{
  "sentiment": "negative" | "neutral" | "positive"
}
```

### Constraints
- Must be a JSON object
- Must contain exactly one key: `sentiment`
- No extra keys allowed
- Value must be one of:
  - `negative`
  - `neutral`
  - `positive`

---

## 10) Reward parser and reward functions

Reward logic is implemented in:

- `scripts/reward_fpb.py`

### Core parsing behavior (Risko-1-style robust parsing)
The parser:
1. finds the first `{` and last `}` in `output_text`
2. tries to parse the substring as JSON
3. validates strict schema

This means outputs like:
- `Here is my answer: {"sentiment":"positive"}`

are currently treated as **parsable and valid** (because the JSON object is recoverable).

This is intentionally robust and useful for early-stage training.

---

### Reward components
Implemented functions:
- `parse_prediction(text)` → returns label or `None`
- `format_reward(text)` → `1.0` if valid schema, else `0.0`
- `correctness_reward(text, gold_label)` → `1.0` if exact match, else `0.0`
- `total_reward(text, gold_label)` → sum of the above (default equal weights)

### Current reward interpretation
- perfect valid + correct JSON label → `2.0`
- valid JSON but wrong label → `1.0`
- invalid schema / not parseable → `0.0`

---

## 11) Evaluation (cached completions)

Evaluation is done with:

- `scripts/eval_fpb_cached.py`

### What it computes
- completion coverage
- format-valid rate
- accuracy (over all examples)
- accuracy on valid outputs only
- macro-F1
- per-class precision / recall / F1
- confusion counts (including invalid/missing)

### Basic evaluation command (test split)
```bash
python scripts/eval_fpb_cached.py \
  --split test \
  --completions <PATH_TO_COMPLETIONS_JSONL>
```

### Save JSON report (optional)
```bash
python scripts/eval_fpb_cached.py \
  --split test \
  --completions <PATH_TO_COMPLETIONS_JSONL> \
  --report-out reports/fpb_eval_test.json
```

---

## 12) Prompt preview (debugging / integration check)

Before model runs, preview exactly what prompts look like:

### Train preview
```bash
python scripts/render_fpb_prompt.py --split train --num 2
```

### Test preview
```bash
python scripts/render_fpb_prompt.py --split test --num 2
```

This prints:
- `example_id`
- `gold_label`
- system prompt
- rendered user prompt

This is useful for catching:
- wrong placeholder replacement
- bad newline formatting
- wrong file wiring

---

## 13) Request builder (generate model-ready inputs)

Use the request builder to create JSONL files for Marco’s pipeline.

### Build full train requests
```bash
python scripts/build_fpb_requests.py --split train
```

### Build full test requests
```bash
python scripts/build_fpb_requests.py --split test
```

### Build a small preview file
```bash
python scripts/build_fpb_requests.py \
  --split test \
  --limit 2 \
  --include-gold \
  --out data/fpb/processed/fpb_test_requests_preview.jsonl
```

---

## 14) Reproducibility and repo hygiene

### What is committed to git (code/spec side)
The following are committed:
- scripts in `scripts/`
- task spec and task README in `tasks/fpb_sentiment_v0/`

### What is NOT committed (data side)
The `data/` directory is intentionally ignored by git, so the following remain local:
- raw ZIP
- raw JSONL
- cleaned JSONL
- train/test splits
- requests JSONL
- dummy completions JSONL
- evaluation reports (unless saved outside `data/` and explicitly committed)

This is intentional and good practice.

---

## 15) Suggested Marco integration flow

### What Marco should consume
Use:
- `data/fpb/processed/fpb_allagree_train_requests.jsonl`
- `data/fpb/processed/fpb_allagree_test_requests.jsonl`

Each row contains:
- `example_id`
- `messages`

### What Marco should produce
A completions JSONL file with rows:
```json
{"example_id": "...", "output_text": "...raw model text..."}
```

### How to evaluate Marco’s outputs
Run:
```bash
python scripts/eval_fpb_cached.py \
  --split test \
  --completions <marco_outputs.jsonl>
```

---

## 16) Common pitfalls to avoid

1. **Wrong completions schema**
   - Evaluator needs `example_id` + `output_text`

2. **Extra keys in model JSON output**
   - Current schema rejects extra keys (e.g. `"confidence"`)

3. **Different label strings**
   - Only valid labels:
     - `negative`
     - `neutral`
     - `positive`

4. **Mismatched example IDs**
   - Evaluation joins completions to gold labels by `example_id`

5. **Prompt changes without updating requests**
   - If you change `task_spec.json`, rebuild requests:
   ```bash
   python scripts/build_fpb_requests.py --split train
   python scripts/build_fpb_requests.py --split test
   ```

---

## 17) Useful commands (full list)

### A) Reward smoke test
```bash
python scripts/reward_fpb.py --smoke-test
```

### B) Single reward check
```bash
python scripts/reward_fpb.py \
  --pred-text '{"sentiment":"neutral"}' \
  --gold-label neutral
```

### C) Prompt previews
```bash
python scripts/render_fpb_prompt.py --split train --num 2
python scripts/render_fpb_prompt.py --split test --num 2
```

### D) Build request files
```bash
python scripts/build_fpb_requests.py --split train
python scripts/build_fpb_requests.py --split test
```

### E) Evaluate cached completions
```bash
python scripts/eval_fpb_cached.py \
  --split test \
  --completions <PATH_TO_COMPLETIONS_JSONL>
```

### F) Evaluate and save JSON report
```bash
python scripts/eval_fpb_cached.py \
  --split test \
  --completions <PATH_TO_COMPLETIONS_JSONL> \
  --report-out reports/fpb_eval_test.json
```

---

