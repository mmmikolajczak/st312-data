import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_SPEC_PATH = REPO_ROOT / "tasks" / "finred_re_v0" / "task_spec.json"


def load_allowed_relations() -> List[str]:
    task_spec = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    return task_spec["output_schema"]["allowed_relations"]


ALLOWED_RELATIONS = set(load_allowed_relations())


def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("’", "'").replace("`", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_triplet(head: str, relation: str, tail: str) -> Tuple[str, str, str]:
    return (normalize_text(head), relation.strip(), normalize_text(tail))


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


def parse_prediction(pred_text: str) -> Optional[Set[Tuple[str, str, str]]]:
    obj = _extract_json_object(pred_text)
    if obj is None:
        return None
    if set(obj.keys()) != {"triplets"}:
        return None
    triplets = obj["triplets"]
    if not isinstance(triplets, list):
        return None

    out: Set[Tuple[str, str, str]] = set()
    for item in triplets:
        if not isinstance(item, dict):
            return None
        if set(item.keys()) != {"head", "relation", "tail"}:
            return None

        head = item["head"]
        relation = item["relation"]
        tail = item["tail"]

        if not (isinstance(head, str) and isinstance(relation, str) and isinstance(tail, str)):
            return None
        if relation not in ALLOWED_RELATIONS:
            return None

        out.add(normalize_triplet(head, relation, tail))
    return out


def _gold_head_text(x: dict) -> str:
    head = x["head"]
    if isinstance(head, dict):
        return head["text"]
    return head


def _gold_tail_text(x: dict) -> str:
    tail = x["tail"]
    if isinstance(tail, dict):
        return tail["text"]
    return tail


def gold_triplet_set(gold_triplets: List[dict]) -> Set[Tuple[str, str, str]]:
    out: Set[Tuple[str, str, str]] = set()
    for x in gold_triplets:
        out.add(normalize_triplet(_gold_head_text(x), x["relation"], _gold_tail_text(x)))
    return out


def pair_set(triplet_set: Set[Tuple[str, str, str]]) -> Set[Tuple[str, str]]:
    return {(h, t) for h, _, t in triplet_set}


def f1_from_sets(pred_set: set, gold_set: set):
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def exact_set_match(pred_set: set, gold_set: set) -> float:
    return 1.0 if pred_set == gold_set else 0.0


def correctness_reward_industry(pred_text: str, gold_triplets: List[dict]) -> float:
    pred_set = parse_prediction(pred_text)
    if pred_set is None:
        return 0.0
    gold_set = gold_triplet_set(gold_triplets)

    _, _, triplet_f1, _, _, _ = f1_from_sets(pred_set, gold_set)
    _, _, pair_f1, _, _, _ = f1_from_sets(pair_set(pred_set), pair_set(gold_set))
    exact = exact_set_match(pred_set, gold_set)

    return 0.70 * triplet_f1 + 0.20 * pair_f1 + 0.10 * exact


def total_reward(pred_text: str, gold_triplets: List[dict]) -> float:
    return format_reward(pred_text) + correctness_reward_industry(pred_text, gold_triplets)


def reward_breakdown(pred_text: str, gold_triplets: List[dict]) -> Dict[str, float]:
    pred_set = parse_prediction(pred_text)
    gold_set = gold_triplet_set(gold_triplets)

    out = {
        "format_reward": format_reward(pred_text),
        "triplet_f1": 0.0,
        "entity_pair_f1": 0.0,
        "exact_set_match": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred_set is None:
        return out

    _, _, triplet_f1, _, _, _ = f1_from_sets(pred_set, gold_set)
    _, _, pair_f1, _, _, _ = f1_from_sets(pair_set(pred_set), pair_set(gold_set))
    exact = exact_set_match(pred_set, gold_set)

    out["triplet_f1"] = triplet_f1
    out["entity_pair_f1"] = pair_f1
    out["exact_set_match"] = exact
    out["correctness_reward_industry"] = correctness_reward_industry(pred_text, gold_triplets)
    out["total_reward"] = total_reward(pred_text, gold_triplets)
    return out


def smoke_test():
    gold = [
        {
            "head": {"text": "Apple Inc"},
            "relation": "founded_by",
            "tail": {"text": "Steve Jobs"},
        },
        {
            "head": {"text": "Apple Inc"},
            "relation": "chief_executive_officer",
            "tail": {"text": "Steve Jobs"},
        },
    ]
    cases = {
        "perfect": json.dumps({
            "triplets": [
                {"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs"},
                {"head": "Apple Inc", "relation": "chief_executive_officer", "tail": "Steve Jobs"},
            ]
        }),
        "partial_relation_wrong": json.dumps({
            "triplets": [
                {"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs"},
                {"head": "Apple Inc", "relation": "employer", "tail": "Steve Jobs"},
            ]
        }),
        "duplicate_triplets": json.dumps({
            "triplets": [
                {"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs"},
                {"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs"},
            ]
        }),
        "bad_relation": json.dumps({
            "triplets": [
                {"head": "Apple Inc", "relation": "not_a_relation", "tail": "Steve Jobs"},
            ]
        }),
        "extra_key": json.dumps({
            "triplets": [
                {"head": "Apple Inc", "relation": "founded_by", "tail": "Steve Jobs", "x": 1},
            ]
        }),
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

    try:
        gold = json.loads(args.gold_json)
    except Exception as e:
        raise SystemExit(f"Invalid --gold-json: {e}")

    if not isinstance(gold, list):
        raise SystemExit("--gold-json must be a JSON array")

    parsed = parse_prediction(args.pred_text)
    print(f"parsed_prediction={parsed}")
    for k, v in reward_breakdown(args.pred_text, gold).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
