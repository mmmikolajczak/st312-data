# Gold Commodity News Multi-label Classification Task (v0)

Task module for 9-dimensional binary multi-label classification of gold-market news headlines.

## Task ID

`TA_MLC_GOLD_COMMODITY_NEWS_v0`

## Canonical split

- Train: `data/gold_commodity_news/processed/gold_commodity_news_train.jsonl`
- Test: `data/gold_commodity_news/processed/gold_commodity_news_test.jsonl`

## Output schema (strict)

    {
      "labels": {
        "price_or_not_norm": 1,
        "direction_up": 0,
        "direction_constant": 0,
        "direction_down": 1,
        "past_price": 1,
        "future_price": 0,
        "past_news": 0,
        "future_news": 0,
        "asset_comparison": 0
      }
    }

Rules:
- Exactly one key: `labels`
- All 9 label keys must be present
- Each value must be integer `0` or `1`
- No extra text

## Evaluation

Cached evaluation reports:
- per-label precision / recall / F1 / accuracy
- macro precision / recall / F1
- micro precision / recall / F1
- subset accuracy
