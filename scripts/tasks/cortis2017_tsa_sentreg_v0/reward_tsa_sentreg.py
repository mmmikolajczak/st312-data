import argparse
import json
import re
from typing import Optional


JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> Optional[dict]:
    m = JSON_OBJ_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_numeric_payload(text: str) -> Optional[float]:
    obj = extract_json_object(text)
    if obj is None:
        return None
    if set(obj.keys()) != {"sentiment_score"}:
        return None
    value = obj.get("sentiment_score")
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def parse_prediction(text: str) -> Optional[float]:
    value = parse_numeric_payload(text)
    if value is None:
        return None
    if value < -1.0 or value > 1.0:
        return None
    return value


def format_reward(text: str) -> float:
    return 1.0 if parse_numeric_payload(text) is not None else 0.0


def range_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def proximity_reward(text: str, gold_score: float) -> float:
    pred = parse_prediction(text)
    if pred is None:
        return 0.0
    return max(0.0, 1.0 - abs(pred - gold_score) / 2.0)


def total_reward(text: str, gold_score: float, w_format: float = 1.0, w_range: float = 1.0, w_prox: float = 1.0) -> float:
    return (
        w_format * format_reward(text)
        + w_range * range_reward(text)
        + w_prox * proximity_reward(text, gold_score)
    )


def smoke_test():
    gold = 0.35
    examples = [
        ('{"sentiment_score": 0.35}', "perfect"),
        ('{"sentiment_score": 0.10}', "valid json, in range, close"),
        ('Answer: {"sentiment_score": -0.90}', "extra text but parsable"),
        ('{"sentiment_score": 1.5}', "out of range"),
        ('{"sentiment_score": "0.25"}', "string numeric"),
        ('{"sentiment_score": 0.35, "confidence": 0.9}', "extra key"),
        ('not json', "not json"),
    ]
    for text, name in examples:
        pred = parse_prediction(text)
        rf = format_reward(text)
        rr = range_reward(text)
        rp = proximity_reward(text, gold)
        rt = total_reward(text, gold)
        print("=" * 72)
        print(f"Case: {name}")
        print(f"Text: {text}")
        print(f"Parsed prediction: {pred}")
        print(f"format_reward={rf} range_reward={rr} proximity_reward={rp:.4f} total={rt:.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-score", type=float, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_score is None:
        raise SystemExit("Provide --pred-text and --gold-score, or use --smoke-test")

    print(f"parsed_prediction={parse_prediction(args.pred_text)}")
    print(f"format_reward={format_reward(args.pred_text)}")
    print(f"range_reward={range_reward(args.pred_text)}")
    print(f"proximity_reward={proximity_reward(args.pred_text, args.gold_score)}")
    print(f"total_reward={total_reward(args.pred_text, args.gold_score)}")


if __name__ == "__main__":
    main()
