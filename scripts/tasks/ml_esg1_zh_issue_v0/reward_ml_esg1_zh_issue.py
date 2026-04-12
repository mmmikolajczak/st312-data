import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/ml_esg1_zh_issue_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from multilabel_metrics import label_set_f1  # noqa: E402
from normalize_labels import canonicalize_label_list  # noqa: E402
from parse_multilabel_json import parse_multilabel_prediction  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
ALLOWED_LABELS = TASK_SPEC["output_schema"]["allowed_values"]["esg_categories"]
ALLOWED_LABEL_SET = set(ALLOWED_LABELS)


def parse_prediction(text: str):
    return parse_multilabel_prediction(text, ALLOWED_LABEL_SET)


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def correctness_reward(text: str, gold_labels: list[str]) -> float:
    pred = parse_prediction(text)
    gold = canonicalize_label_list(gold_labels, allowed_labels=ALLOWED_LABEL_SET)
    if pred is None or gold is None:
        return 0.0
    return label_set_f1(pred, gold)


def exact_set_match(text: str, gold_labels: list[str]) -> float:
    pred = parse_prediction(text)
    gold = canonicalize_label_list(gold_labels, allowed_labels=ALLOWED_LABEL_SET)
    if pred is None or gold is None:
        return 0.0
    return 1.0 if pred == gold else 0.0


def total_reward(text: str, gold_labels: list[str]) -> float:
    return format_reward(text) + correctness_reward(text, gold_labels)


def reward_breakdown(text: str, gold_labels: list[str]) -> dict:
    pred = parse_prediction(text)
    gold = canonicalize_label_list(gold_labels, allowed_labels=ALLOWED_LABEL_SET) or []
    return {
        "parsed_prediction": pred,
        "format_reward": format_reward(text),
        "instance_f1_reward": correctness_reward(text, gold),
        "exact_set_match": exact_set_match(text, gold),
        "predicted_label_count": len(pred or []),
        "gold_label_count": len(gold),
        "total_reward": total_reward(text, gold),
    }


def smoke_test():
    gold = ["E01", "S13"]
    cases = [
        ("perfect_json", '{"esg_categories":["E01","S13"]}', ["E01", "S13"]),
        ("alias_key_and_normalization", 'Answer: {"labels":[" s13 ","e01","E01"]}', ["E01", "S13"]),
        ("partial_overlap", '{"esg_categories":["E01","G08"]}', ["E01", "G08"]),
        ("invalid_label", '{"esg_categories":["ZZ99"]}', None),
        ("extra_key", '{"esg_categories":["E01"],"note":"x"}', None),
        ("malformed_json", '{"esg_categories":["E01"', None),
    ]
    for name, text, expected in cases:
        parsed = parse_prediction(text)
        assert parsed == expected, f"{name}: expected {expected}, got {parsed}"
        breakdown = reward_breakdown(text, gold)
        print("=" * 72)
        print(name)
        print(json.dumps(breakdown, ensure_ascii=False, indent=2))
    print("[PASS] Smoke test passed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-labels-json", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_labels_json is None:
        raise SystemExit("Provide --pred-text and --gold-labels-json, or use --smoke-test")

    gold_labels = json.loads(args.gold_labels_json)
    print(json.dumps(reward_breakdown(args.pred_text, gold_labels), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
