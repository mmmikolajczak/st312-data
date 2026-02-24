import argparse
import json
import re
from typing import Optional

ALLOWED = {"dovish", "hawkish", "neutral"}

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

def parse_prediction(text: str) -> Optional[str]:
    obj = extract_json_object(text)
    if obj is None:
        return None
    if set(obj.keys()) != {"stance"}:
        return None
    val = obj.get("stance")
    if not isinstance(val, str):
        return None
    val = val.strip().lower()
    return val if val in ALLOWED else None

def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0

def correctness_reward(text: str, gold_label: str) -> float:
    pred = parse_prediction(text)
    if pred is None:
        return 0.0
    return 1.0 if pred == gold_label else 0.0

def total_reward(text: str, gold_label: str, w_format: float = 1.0, w_correct: float = 1.0) -> float:
    return w_format * format_reward(text) + w_correct * correctness_reward(text, gold_label)

def smoke_test():
    gold = "hawkish"
    examples = [
        ('{"stance":"hawkish"}', "perfect"),
        ('{"stance":"neutral"}', "valid json, wrong label"),
        ('Answer: {"stance":"hawkish"}', "extra text but parsable"),
        ('{"stance":"tightening"}', "invalid label"),
        ('{"stance":"hawkish","confidence":0.9}', "extra key"),
        ('not json', "not json")
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
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=str, default=None)
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
    print(f"parsed_prediction={pred}")
    print(f"format_reward={format_reward(args.pred_text)}")
    print(f"correctness_reward={correctness_reward(args.pred_text, gold)}")
    print(f"total_reward={total_reward(args.pred_text, gold)}")

if __name__ == "__main__":
    main()
