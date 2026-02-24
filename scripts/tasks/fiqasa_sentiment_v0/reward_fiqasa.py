import argparse
import json
import re
from typing import Optional


ALLOWED = {"negative", "neutral", "positive"}


def _extract_first_json_object(text: str) -> Optional[str]:
    text = text.strip()

    # Fast path: whole string is JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Robust path: find first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        return m.group(0)

    return None


def parse_prediction(text: str) -> Optional[str]:
    json_blob = _extract_first_json_object(text)
    if json_blob is None:
        return None

    try:
        obj = json.loads(json_blob)
    except Exception:
        return None

    if not isinstance(obj, dict):
        return None

    # Strict schema: exactly one key, "sentiment"
    if set(obj.keys()) != {"sentiment"}:
        return None

    value = obj.get("sentiment")
    if not isinstance(value, str):
        return None

    value = value.strip().lower()
    if value not in ALLOWED:
        return None

    return value


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def correctness_reward(text: str, gold_label: str) -> float:
    pred = parse_prediction(text)
    if pred is None:
        return 0.0
    return 1.0 if pred == gold_label else 0.0


def total_reward(text: str, gold_label: str, w_format: float = 1.0, w_correct: float = 1.0) -> float:
    rf = format_reward(text)
    rc = correctness_reward(text, gold_label)
    return w_format * rf + w_correct * rc


def smoke_test():
    gold = "positive"

    examples = [
        ('{"sentiment": "positive"}', "perfect"),
        ('{"sentiment": "neutral"}', "valid json, wrong label"),
        ('Here is my answer: {"sentiment": "positive"}', "extra text but parsable"),
        ('{"sentiment": "bullish"}', "invalid label"),
        ('{"sentiment": "positive", "confidence": 0.9}', "extra key"),
        ('not json at all', "not json")
    ]

    for text, name in examples:
        pred = parse_prediction(text)
        rf = format_reward(text)
        rc = correctness_reward(text, gold)
        rt = total_reward(text, gold)
        print("=" * 60)
        print(f"Case: {name}")
        print(f"Text: {text}")
        print(f"Parsed prediction: {pred}")
        print(f"format_reward={rf} correctness_reward={rc} total={rt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None, help="Model output text to score")
    ap.add_argument("--gold-label", type=str, default=None, help="Gold sentiment label")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_label is None:
        raise SystemExit("Provide --pred-text and --gold-label, or use --smoke-test")

    gold = args.gold_label.strip().lower()
    if gold not in ALLOWED:
        raise SystemExit(f"gold-label must be one of {sorted(ALLOWED)}")

    pred = parse_prediction(args.pred_text)
    rf = format_reward(args.pred_text)
    rc = correctness_reward(args.pred_text, gold)
    rt = total_reward(args.pred_text, gold)

    print(f"parsed_prediction={pred}")
    print(f"format_reward={rf}")
    print(f"correctness_reward={rc}")
    print(f"total_reward={rt}")


if __name__ == "__main__":
    main()
