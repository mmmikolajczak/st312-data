import argparse
import json

LABEL_KEYS = [
    "price_or_not_norm",
    "direction_up",
    "direction_constant",
    "direction_down",
    "past_price",
    "future_price",
    "past_news",
    "future_news",
    "asset_comparison",
]


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
    if set(obj.keys()) != {"labels"}:
        return None
    labels = obj["labels"]
    if not isinstance(labels, dict):
        return None
    if set(labels.keys()) != set(LABEL_KEYS):
        return None

    parsed = {}
    for k in LABEL_KEYS:
        v = labels[k]
        if not isinstance(v, int) or v not in (0, 1):
            return None
        parsed[k] = int(v)
    return parsed


def confusion(pred: dict, gold: dict, key: str):
    p = int(pred[key])
    g = int(gold[key])
    tp = int(p == 1 and g == 1)
    fp = int(p == 1 and g == 0)
    fn = int(p == 0 and g == 1)
    tn = int(p == 0 and g == 0)
    return tp, fp, fn, tn


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if tp == 0 and fp == 0 and fn == 0:
        f1 = 1.0
    else:
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def correctness_reward_industry(pred_text: str, gold: dict):
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0

    macro_f1s = []
    micro_tp = micro_fp = micro_fn = 0
    exact = 1.0

    for k in LABEL_KEYS:
        tp, fp, fn, _ = confusion(pred, gold, k)
        _, _, f1 = prf(tp, fp, fn)
        macro_f1s.append(f1)
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn
        if pred[k] != int(gold[k]):
            exact = 0.0

    _, _, micro_f1 = prf(micro_tp, micro_fp, micro_fn)
    macro_f1 = sum(macro_f1s) / len(macro_f1s)
    return 0.70 * macro_f1 + 0.20 * micro_f1 + 0.10 * exact


def total_reward(pred_text: str, gold: dict):
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold)


def reward_breakdown(pred_text: str, gold: dict):
    pred = parse_prediction(pred_text)
    out = {
        "format_reward": format_reward(pred_text),
        "macro_f1": 0.0,
        "micro_f1": 0.0,
        "subset_accuracy": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred is None:
        return out

    macro_f1s = []
    micro_tp = micro_fp = micro_fn = 0
    exact = 1.0

    for k in LABEL_KEYS:
        tp, fp, fn, _ = confusion(pred, gold, k)
        _, _, f1 = prf(tp, fp, fn)
        macro_f1s.append(f1)
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn
        if pred[k] != int(gold[k]):
            exact = 0.0

    _, _, micro_f1 = prf(micro_tp, micro_fp, micro_fn)
    macro_f1 = sum(macro_f1s) / len(macro_f1s)

    out["macro_f1"] = macro_f1
    out["micro_f1"] = micro_f1
    out["subset_accuracy"] = exact
    out["correctness_reward_industry"] = 0.70 * macro_f1 + 0.20 * micro_f1 + 0.10 * exact
    out["total_reward"] = total_reward(pred_text, gold)
    return out


def smoke_test():
    gold = {
        "price_or_not_norm": 1,
        "direction_up": 1,
        "direction_constant": 0,
        "direction_down": 0,
        "past_price": 1,
        "future_price": 0,
        "past_news": 0,
        "future_news": 0,
        "asset_comparison": 0,
    }
    cases = {
        "perfect": json.dumps({"labels": gold}),
        "one_bit_wrong": json.dumps({"labels": {**gold, "future_news": 1}}),
        "all_zero": json.dumps({"labels": {k: 0 for k in gold}}),
        "bad_key": json.dumps({"labels": {**gold, "asset_comparision": 0}}),
        "not_json": "not json",
    }
    for name, txt in cases.items():
        parsed = parse_prediction(txt)
        br = reward_breakdown(txt, gold)
        print("=" * 88)
        print(f"Case: {name}")
        print(f"Parsed prediction: {parsed}")
        for k, v in br.items():
            print(f"{k}={v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-json", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_json is None:
        raise SystemExit("Provide --pred-text and --gold-json, or use --smoke-test")

    gold = json.loads(args.gold_json)
    print(f"parsed_prediction={parse_prediction(args.pred_text)}")
    for k, v in reward_breakdown(args.pred_text, gold).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
