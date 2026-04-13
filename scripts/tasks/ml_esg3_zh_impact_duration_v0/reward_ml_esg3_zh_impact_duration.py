import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/ml_esg3_zh_impact_duration_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_labels import canonicalize_single_label  # noqa: E402
from parse_singlelabel_json import parse_keyed_singlelabel_prediction  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
ALLOWED_LABELS = TASK_SPEC["output_schema"]["allowed_values"]["impact_duration"]
ALIAS_KEYS = ["impact_duration", "label", "duration", "impactDuration"]


def parse_prediction(text: str):
    return parse_keyed_singlelabel_prediction(text, ALLOWED_LABELS, ALIAS_KEYS)


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def correctness_reward(text: str, gold_label: str) -> float:
    pred = parse_prediction(text)
    gold = canonicalize_single_label(gold_label, ALLOWED_LABELS)
    if pred is None or gold is None:
        return 0.0
    return 1.0 if pred == gold else 0.0


def total_reward(text: str, gold_label: str) -> float:
    return format_reward(text) + correctness_reward(text, gold_label)


def reward_breakdown(text: str, gold_label: str) -> dict:
    pred = parse_prediction(text)
    gold = canonicalize_single_label(gold_label, ALLOWED_LABELS)
    return {
        "parsed_prediction": pred,
        "gold_label": gold,
        "format_reward": format_reward(text),
        "correctness_reward": correctness_reward(text, gold_label),
        "total_reward": total_reward(text, gold_label),
    }


def smoke_test():
    gold = "2~5"
    cases = [
        ("perfect_json", '{"impact_duration":"2~5"}', "2~5"),
        ("alias_key_and_normalization", 'Answer: {"impactDuration":" >5 "}', ">5"),
        ("wrong_label", '{"impact_duration":"<2"}', "<2"),
        ("invalid_label", '{"impact_duration":"6~9"}', None),
        ("extra_key", '{"impact_duration":"2~5","note":"x"}', None),
        ("malformed_json", '{"impact_duration":"2~5"', None),
    ]
    for name, text, expected in cases:
        parsed = parse_prediction(text)
        assert parsed == expected, f"{name}: expected {expected}, got {parsed}"
        print("=" * 72)
        print(name)
        print(json.dumps(reward_breakdown(text, gold), ensure_ascii=False, indent=2))
    print("[PASS] Smoke test passed")


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

    print(json.dumps(reward_breakdown(args.pred_text, args.gold_label), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
