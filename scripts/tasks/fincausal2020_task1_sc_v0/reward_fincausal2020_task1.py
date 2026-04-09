import argparse
import json


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
    if label not in [0, 1]:
        return None
    return int(label)


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def correctness_reward_industry(pred_text: str, gold_label: int) -> float:
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0
    return 1.0 if pred == gold_label else 0.0


def total_reward(pred_text: str, gold_label: int) -> float:
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold_label)


def reward_breakdown(pred_text: str, gold_label: int):
    pred = parse_prediction(pred_text)
    out = {
        "format_reward": format_reward(pred_text),
        "accuracy": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred is not None:
        acc = 1.0 if pred == gold_label else 0.0
        out["accuracy"] = acc
        out["correctness_reward_industry"] = acc
        out["total_reward"] = total_reward(pred_text, gold_label)
    return out


def smoke_test():
    gold = 1
    cases = {
        "perfect_positive": json.dumps({"label": 1}),
        "perfect_negative": json.dumps({"label": 0}),
        "string_label": json.dumps({"label": "1"}),
        "extra_key": json.dumps({"label": 1, "x": 1}),
        "not_json": "not json",
    }
    for name, txt in cases.items():
        pred = parse_prediction(txt)
        br = reward_breakdown(txt, gold)
        print("=" * 72)
        print(f"Case: {name}")
        print(f"Parsed prediction: {pred}")
        for k, v in br.items():
            print(f"{k}={v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=int, choices=[0, 1], default=None)
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
