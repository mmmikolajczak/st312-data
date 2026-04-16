import argparse
import json

ALLOWED = {"premise", "claim"}


def _extract_json_object(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_prediction(pred_text: str):
    obj = _extract_json_object(pred_text)
    if obj is None:
        return None
    if set(obj.keys()) != {"label"}:
        return None
    label = obj["label"]
    if not isinstance(label, str):
        return None
    if label not in ALLOWED:
        return None
    return label


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def correctness_reward_industry(pred_text: str, gold_label: str) -> float:
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0
    return 1.0 if pred == gold_label else 0.0


def total_reward(pred_text: str, gold_label: str) -> float:
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold_label)


def reward_breakdown(pred_text: str, gold_label: str):
    pred = parse_prediction(pred_text)
    accuracy = 1.0 if pred == gold_label else 0.0 if pred is not None else 0.0
    return {
        "format_reward": format_reward(pred_text),
        "accuracy": accuracy,
        "correctness_reward_industry": correctness_reward_industry(pred_text, gold_label),
        "total_reward": total_reward(pred_text, gold_label),
    }


def smoke_test():
    cases = [
        ("perfect_premise", json.dumps({"label": "premise"}), "premise"),
        ("perfect_claim", json.dumps({"label": "claim"}), "claim"),
        ("wrong", json.dumps({"label": "claim"}), "premise"),
        ("bad_label", json.dumps({"label": "other"}), "premise"),
        ("extra_key", json.dumps({"label": "premise", "score": 1.0}), "premise"),
        ("not_json", "premise", "premise"),
    ]
    for name, pred_text, gold in cases:
        print("=" * 88)
        print(f"Case: {name}")
        print(f"Parsed prediction: {parse_prediction(pred_text)}")
        for k, v in reward_breakdown(pred_text, gold).items():
            print(f"{k}={v}")


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

    print(f"parsed_prediction={parse_prediction(args.pred_text)}")
    for k, v in reward_breakdown(args.pred_text, args.gold_label).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
