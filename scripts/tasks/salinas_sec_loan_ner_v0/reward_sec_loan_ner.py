import argparse
import json
from typing import Dict, List, Optional, Tuple

ALLOWED = {
    "O",
    "B-PER", "I-PER",
    "B-LOC", "I-LOC",
    "B-ORG", "I-ORG",
    "B-MISC", "I-MISC",
}


def _extract_json_object(text: str) -> Optional[dict]:
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


def parse_prediction(pred_text: str, expected_len: Optional[int] = None) -> Optional[List[str]]:
    obj = _extract_json_object(pred_text)
    if obj is None:
        return None
    if set(obj.keys()) != {"tags"}:
        return None
    tags = obj["tags"]
    if not isinstance(tags, list) or not all(isinstance(x, str) for x in tags):
        return None
    if any(x not in ALLOWED for x in tags):
        return None
    if expected_len is not None and len(tags) != expected_len:
        return None
    return tags


def format_reward(pred_text: str, expected_len: Optional[int] = None) -> float:
    return 1.0 if parse_prediction(pred_text, expected_len=expected_len) is not None else 0.0


def token_accuracy(pred_tags: List[str], gold_tags: List[str]) -> float:
    if len(pred_tags) != len(gold_tags) or len(gold_tags) == 0:
        return 0.0
    correct = sum(1 for p, g in zip(pred_tags, gold_tags) if p == g)
    return correct / len(gold_tags)


def _split_bio(tag: str) -> Tuple[str, Optional[str]]:
    if tag == "O":
        return "O", None
    if "-" not in tag:
        return "O", None
    prefix, ent = tag.split("-", 1)
    if prefix not in {"B", "I"}:
        return "O", None
    return prefix, ent


def bio_to_spans(tags: List[str]) -> List[Tuple[str, int, int]]:
    spans: List[Tuple[str, int, int]] = []
    current_type: Optional[str] = None
    start_idx: Optional[int] = None

    def close_span(end_idx_exclusive: int):
        nonlocal current_type, start_idx
        if current_type is not None and start_idx is not None:
            spans.append((current_type, start_idx, end_idx_exclusive))
        current_type = None
        start_idx = None

    for i, tag in enumerate(tags):
        prefix, ent = _split_bio(tag)
        if prefix == "O":
            close_span(i)
            continue
        if prefix == "B":
            close_span(i)
            current_type = ent
            start_idx = i
            continue
        if current_type is None:
            current_type = ent
            start_idx = i
        elif current_type != ent:
            close_span(i)
            current_type = ent
            start_idx = i

    close_span(len(tags))
    return spans


def entity_span_f1(pred_tags: List[str], gold_tags: List[str]) -> float:
    if len(pred_tags) != len(gold_tags):
        return 0.0
    pred_spans = set(bio_to_spans(pred_tags))
    gold_spans = set(bio_to_spans(gold_tags))
    tp = len(pred_spans & gold_spans)
    fp = len(pred_spans - gold_spans)
    fn = len(gold_spans - pred_spans)
    if tp == 0 and fp == 0 and fn == 0:
        return 1.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def exact_sequence_match(pred_tags: List[str], gold_tags: List[str]) -> float:
    return 1.0 if pred_tags == gold_tags else 0.0


def correctness_reward_industry(pred_text: str, gold_tags: List[str]) -> float:
    pred = parse_prediction(pred_text, expected_len=len(gold_tags))
    if pred is None:
        return 0.0
    ent_f1 = entity_span_f1(pred, gold_tags)
    tok_acc = token_accuracy(pred, gold_tags)
    exact = exact_sequence_match(pred, gold_tags)
    return 0.50 * ent_f1 + 0.40 * tok_acc + 0.10 * exact


def total_reward(pred_text: str, gold_tags: List[str]) -> float:
    return format_reward(pred_text, expected_len=len(gold_tags)) + correctness_reward_industry(pred_text, gold_tags)


def reward_breakdown(pred_text: str, gold_tags: List[str]) -> Dict[str, float]:
    pred = parse_prediction(pred_text, expected_len=len(gold_tags))
    out = {
        "format_reward": format_reward(pred_text, expected_len=len(gold_tags)),
        "token_accuracy": 0.0,
        "entity_span_f1": 0.0,
        "exact_sequence_match": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred is not None:
        out["token_accuracy"] = token_accuracy(pred, gold_tags)
        out["entity_span_f1"] = entity_span_f1(pred, gold_tags)
        out["exact_sequence_match"] = exact_sequence_match(pred, gold_tags)
        out["correctness_reward_industry"] = correctness_reward_industry(pred_text, gold_tags)
        out["total_reward"] = total_reward(pred_text, gold_tags)
    return out


def smoke_test():
    gold = ["B-ORG", "I-ORG", "O", "B-MISC", "O", "B-PER", "I-PER"]
    cases = {
        "perfect": json.dumps({"tags": gold}),
        "valid wrong sequence": json.dumps({"tags": ["B-ORG", "I-ORG", "O", "O", "O", "B-PER", "I-PER"]}),
        "bad label": json.dumps({"tags": ["B-ORG", "I-ORG", "O", "B-X", "O", "B-PER", "I-PER"]}),
        "wrong length": json.dumps({"tags": ["B-ORG", "I-ORG"]}),
        "extra key": json.dumps({"tags": gold, "x": 1}),
        "not json": "not json",
    }
    for name, txt in cases.items():
        pred = parse_prediction(txt, expected_len=len(gold))
        br = reward_breakdown(txt, gold)
        print("=" * 72)
        print(f"Case: {name}")
        print(f"Parsed prediction: {pred}")
        for k, v in br.items():
            print(f"{k}={v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-tags-json", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_tags_json is None:
        raise SystemExit("Provide --pred-text and --gold-tags-json, or use --smoke-test")

    try:
        gold = json.loads(args.gold_tags_json)
    except Exception as e:
        raise SystemExit(f"Invalid --gold-tags-json: {e}")

    if not isinstance(gold, list) or not all(isinstance(x, str) for x in gold):
        raise SystemExit("--gold-tags-json must be a JSON array of strings")
    if any(x not in ALLOWED for x in gold):
        raise SystemExit(f"gold tags must be within {sorted(ALLOWED)}")

    pred = parse_prediction(args.pred_text, expected_len=len(gold))
    print(f"parsed_prediction={pred}")
    for k, v in reward_breakdown(args.pred_text, gold).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
