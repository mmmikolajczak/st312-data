import argparse
import json
from collections import Counter

LABEL_ID_MIN = 1
LABEL_ID_MAX = 2799


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
    if set(obj.keys()) != {"mentions"}:
        return None
    mentions = obj["mentions"]
    if not isinstance(mentions, list):
        return None

    parsed = []
    seen_pairs = set()

    for item in mentions:
        if not isinstance(item, dict):
            return None
        if set(item.keys()) != {"token_index", "label_id"}:
            return None

        token_index = item["token_index"]
        label_id = item["label_id"]

        if not isinstance(token_index, int) or token_index < 0:
            return None
        if not isinstance(label_id, int) or not (LABEL_ID_MIN <= label_id <= LABEL_ID_MAX):
            return None

        pair = (token_index, label_id)
        if pair in seen_pairs:
            return None

        seen_pairs.add(pair)
        parsed.append(pair)

    parsed.sort()
    return parsed


def gold_pairs(gold_mentions):
    return sorted((int(m["token_index"]), int(m["label_id"])) for m in gold_mentions)


def prf_from_sets(pred_set, gold_set):
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn


def macro_f1_from_pairs(pred_pairs, gold_pairs_):
    pred_by_label = Counter(label_id for _, label_id in pred_pairs)
    gold_by_label = Counter(label_id for _, label_id in gold_pairs_)
    label_ids = sorted(set(pred_by_label) | set(gold_by_label))
    if not label_ids:
        return 1.0

    f1s = []
    pred_set = set(pred_pairs)
    gold_set = set(gold_pairs_)
    for label_id in label_ids:
        pred_label = {p for p in pred_set if p[1] == label_id}
        gold_label = {g for g in gold_set if g[1] == label_id}
        _, _, f1, _, _, _ = prf_from_sets(pred_label, gold_label)
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def correctness_reward_industry(pred_text: str, gold_mentions):
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0

    gold = gold_pairs(gold_mentions)
    pred_set = set(pred)
    gold_set = set(gold)

    _, _, micro_f1, _, _, _ = prf_from_sets(pred_set, gold_set)
    macro_f1 = macro_f1_from_pairs(pred, gold)
    exact = 1.0 if pred == gold else 0.0

    return 0.70 * micro_f1 + 0.20 * macro_f1 + 0.10 * exact


def total_reward(pred_text: str, gold_mentions):
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold_mentions)


def reward_breakdown(pred_text: str, gold_mentions):
    pred = parse_prediction(pred_text)
    gold = gold_pairs(gold_mentions)

    out = {
        "format_reward": format_reward(pred_text),
        "micro_precision": 0.0,
        "micro_recall": 0.0,
        "micro_f1": 0.0,
        "macro_f1": 0.0,
        "exact_set_match": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred is None:
        return out

    pred_set = set(pred)
    gold_set = set(gold)
    p, r, f1, _, _, _ = prf_from_sets(pred_set, gold_set)
    macro_f1 = macro_f1_from_pairs(pred, gold)
    exact = 1.0 if pred == gold else 0.0

    out["micro_precision"] = p
    out["micro_recall"] = r
    out["micro_f1"] = f1
    out["macro_f1"] = macro_f1
    out["exact_set_match"] = exact
    out["correctness_reward_industry"] = 0.70 * f1 + 0.20 * macro_f1 + 0.10 * exact
    out["total_reward"] = total_reward(pred_text, gold_mentions)
    return out


def smoke_test():
    gold = [
        {"token_index": 26, "label_id": 1},
        {"token_index": 35, "label_id": 2},
    ]
    cases = {
        "perfect": json.dumps({"mentions": [
            {"token_index": 26, "label_id": 1},
            {"token_index": 35, "label_id": 2},
        ]}),
        "one_wrong_label": json.dumps({"mentions": [
            {"token_index": 26, "label_id": 1},
            {"token_index": 35, "label_id": 3},
        ]}),
        "missing_one": json.dumps({"mentions": [
            {"token_index": 26, "label_id": 1},
        ]}),
        "same_token_two_labels": json.dumps({"mentions": [
            {"token_index": 26, "label_id": 1},
            {"token_index": 26, "label_id": 2},
        ]}),
        "duplicate_exact_pair": json.dumps({"mentions": [
            {"token_index": 26, "label_id": 1},
            {"token_index": 26, "label_id": 1},
        ]}),
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

    gold_mentions = json.loads(args.gold_json)
    print(f"parsed_prediction={parse_prediction(args.pred_text)}")
    for k, v in reward_breakdown(args.pred_text, gold_mentions).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
