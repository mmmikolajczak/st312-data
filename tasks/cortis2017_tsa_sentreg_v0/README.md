# Cortis 2017 TSA Sentiment Regression Task (v0)

Task module for target-aware continuous sentiment prediction on financial headlines.

## Task ID
`TA_SENTREG_TSA_CORTIS2017_v0`

## Dataset module
- Dataset ID: `cortis2017_tsa_v0`
- Train: `data/cortis2017_tsa/processed/cortis2017_tsa_train.jsonl`
- Trial/dev: `data/cortis2017_tsa/processed/cortis2017_tsa_trial.jsonl`
- Blind test inputs: `data/cortis2017_tsa/processed/cortis2017_tsa_test_inputs.jsonl`
- Scored test: `data/cortis2017_tsa/processed/cortis2017_tsa_test_scored.jsonl` (only after GS join)

## Output schema
Return ONLY:
{"sentiment_score": <number between -1 and 1>}

No extra keys. No extra text.

## Reward / eval notes
- Reward should favour valid JSON, in-range values, and numerical proximity to gold.
- Local evaluation should report the official weighted cosine similarity, plus MAE/RMSE and coverage.
- Until held-out GS arrives, `trial` is the default scored evaluation split.
