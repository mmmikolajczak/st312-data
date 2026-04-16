from __future__ import annotations

import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/stocknet_acl18_stockmove_v0/task_spec.json")


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def render_aligned_day(day: dict) -> str:
    pre = day["price_features_preprocessed"]
    raw = day["price_features_raw"]
    tweets = day["tweets"]
    tweet_lines = "\n".join(f"- {text}" for text in tweets) if tweets else "- [no aligned tweets assigned]"
    return (
        f"Day {day['day_index']} | trading_date={day['date']} | price_feature_date={day['price_feature_date']} | "
        f"tweet_count={day['tweet_count']}\n"
        f"Preprocessed price features: movement_percent={_fmt(pre['movement_percent'])}, open_norm={_fmt(pre['open_norm'])}, "
        f"high_norm={_fmt(pre['high_norm'])}, low_norm={_fmt(pre['low_norm'])}, close_norm={_fmt(pre['close_norm'])}, "
        f"volume={_fmt(pre['volume'])}\n"
        f"Raw price features: open={_fmt(raw['open'])}, high={_fmt(raw['high'])}, low={_fmt(raw['low'])}, "
        f"close={_fmt(raw['close'])}, adj_close={_fmt(raw['adj_close'])}, volume={_fmt(raw['volume'])}\n"
        f"Tweets:\n{tweet_lines}"
    )


def render_user_prompt(rec: dict) -> str:
    aligned = "\n\n".join(render_aligned_day(day) for day in rec["aligned_days"])
    return (
        f"Stock symbol: {rec['stock_symbol']}\n"
        f"Target date: {rec['target_date']}\n"
        f"Calendar lag days: {rec['calendar_lag_days']}\n"
        f"Aligned trading days count: {rec['aligned_trading_days_count']}\n\n"
        f"Aligned history:\n{aligned}\n\n"
        f"Forecast whether the target stock's movement on {rec['target_date']} is Rise or Fall.\n"
        f"Return JSON only in this form:\n{{\"label\":\"Rise\"}}"
    )


def main() -> None:
    sample = {
        "stock_symbol": "WFC",
        "target_date": "2015-10-01",
        "calendar_lag_days": 5,
        "aligned_trading_days_count": 3,
        "aligned_days": [],
    }
    print(json.dumps({"system": json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))["prompt_template"]["system"], "user": render_user_prompt(sample)}, indent=2))


if __name__ == "__main__":
    main()
