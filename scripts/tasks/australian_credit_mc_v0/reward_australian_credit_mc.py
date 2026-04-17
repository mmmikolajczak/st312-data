import argparse
import json

ALLOWED = {"Reject", "Approve"}

def parse_prediction(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end+1])
    except Exception:
        return None
    if not isinstance(obj, dict) or set(obj.keys()) != {"label"}:
        return None
    label = obj["label"]
    if not isinstance(label, str) or label not in ALLOWED:
        return None
    return label

def format_reward(pred_text: str) -> float:
    return 0.1 if parse_prediction(pred_text) is not None else 0.0

def correctness_reward_industry(pred_text: str, gold_label: str) -> float:
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0
    return 0.9 if pred == gold_label else 0.0

def total_reward(pred_text: str, gold_label: str) -> float:
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold_label)

def smoke_test():
    cases = [
        ("perfect_approve", json.dumps({"label": "Approve"}), "Approve"),
        ("perfect_reject", json.dumps({"label": "Reject"}), "Reject"),
        ("valid_wrong", json.dumps({"label": "Approve"}), "Reject"),
        ("bad_value", json.dumps({"label": "Maybe"}), "Reject"),
        ("extra_key", json.dumps({"label": "Reject", "x": 1}), "Reject"),
        ("not_json", "Reject", "Reject"),
    ]
    for name, pred, gold in cases:
        print("=" * 88)
        print("Case:", name)
        print("Parsed prediction:", parse_prediction(pred))
        print("format_reward=", format_reward(pred))
        print("correctness_reward_industry=", correctness_reward_industry(pred, gold))
        print("total_reward=", total_reward(pred, gold))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if args.smoke_test:
        smoke_test()

if __name__ == "__main__":
    main()
