import argparse
import json
from typing import Optional, Dict, Any

ALLOWED = {"negative", "neutral", "positive"}


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    Risko-1-style robust parsing:
    - find first '{' and last '}'
    - try json.loads on that slice
    Returns dict or None.
    """
    if not isinstance(text, str):
        return None

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None

    candidate = text[start:end + 1]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if not isinstance(obj, dict):
        return None
    return obj


def validate_output_schema(obj: Dict[str, Any]) -> bool:
    """
    Valid if:
    - exactly one key
    - key is 'sentiment'
    - value is one of allowed labels
    """
    if set(obj.keys()) != {"sentiment"}:
        return False
    val = obj.get("sentiment")
    return isinstance(val, str) and val in ALLOWED


def parse_prediction(text: str) -> Optional[str]:
    """
    Return the sentiment label if parsing+schema validation succeeds, else None.
    """
    obj = extract_json_object(text)
    if obj is None:
        return None
    if not validate_output_schema(obj):
        return None
    return obj["sentiment"]


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
        ('not json at all', "not json"),
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

    if args.gold_label not in ALLOWED:
        raise SystemExit(f"gold-label must be one of {sorted(ALLOWED)}")

    pred = parse_prediction(args.pred_text)
    rf = format_reward(args.pred_text)
    rc = correctness_reward(args.pred_text, args.gold_label)
    rt = total_reward(args.pred_text, args.gold_label)

    print(f"parsed_prediction={pred}")
    print(f"format_reward={rf}")
    print(f"correctness_reward={rc}")
    print(f"total_reward={rt}")


if __name__ == "__main__":
    main()
