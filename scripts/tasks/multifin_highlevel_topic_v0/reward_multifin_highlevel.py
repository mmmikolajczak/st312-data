import argparse
import json
from typing import Optional

ALLOWED = {
    "Technology",
    "Industry",
    "Tax & Accounting",
    "Finance",
    "Government & Controls",
    "Business & Management",
}


def extract_json_object(text: str) -> Optional[dict]:
    text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def parse_prediction(text: str) -> Optional[str]:
    obj = extract_json_object(text)
    if obj is None:
        return None
    if set(obj.keys()) != {"topic"}:
        return None

    pred = obj["topic"]
    if not isinstance(pred, str):
        return None

    pred = pred.strip()
    if pred not in ALLOWED:
        return None

    return pred


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def correctness_reward(text: str, gold_label: str) -> float:
    if not isinstance(gold_label, str):
        return 0.0
    gold_label = gold_label.strip()
    if gold_label not in ALLOWED:
        return 0.0

    pred = parse_prediction(text)
    return 1.0 if pred == gold_label else 0.0


def total_reward(text: str, gold_label: str) -> float:
    return format_reward(text) + correctness_reward(text, gold_label)


def smoke_test() -> None:
    gold = "Finance"
    cases = {
        "perfect": '{"topic":"Finance"}',
        "valid_wrong_label": '{"topic":"Industry"}',
        "extra_text_invalid": 'Answer: {"topic":"Finance"}',
        "bad_label": '{"topic":"Banking"}',
        "extra_key": '{"topic":"Finance","confidence":0.9}',
        "not_json": "not json",
    }

    for name, txt in cases.items():
        print("=" * 60)
        print(f"Case: {name}")
        print(f"Parsed prediction: {parse_prediction(txt)}")
        print(f"format_reward={format_reward(txt)}")
        print(f"correctness_reward={correctness_reward(txt, gold)}")
        print(f"total_reward={total_reward(txt, gold)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=str, default=None)
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
    print(f"parsed_prediction={pred}")
    print(f"format_reward={format_reward(args.pred_text)}")
    print(f"correctness_reward={correctness_reward(args.pred_text, args.gold_label)}")
    print(f"total_reward={total_reward(args.pred_text, args.gold_label)}")


if __name__ == "__main__":
    main()
