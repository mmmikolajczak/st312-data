from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/tatqa_hybrid_qa_structured_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_tatqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_tatqa_prediction import parse_prediction_text  # noqa: E402
from wrap_official_tatqa_eval import processed_row_to_official_ground_truth, score_prediction  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))


def _set_f1(predicted: list[str], gold: list[str]) -> float:
    pred_set = set(predicted)
    gold_set = set(gold)
    if not pred_set and not gold_set:
        return 1.0
    if not pred_set or not gold_set:
        return 0.0
    precision = len(pred_set & gold_set) / len(pred_set)
    recall = len(pred_set & gold_set) / len(gold_set)
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _normalize_derivation(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def format_reward(text: str) -> float:
    return 0.5 if parse_prediction_text(text) is not None else 0.0


def official_answer_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    score = score_prediction(processed_row_to_official_ground_truth(gold_record), pred["answer"], pred["scale"])
    return 2.0 * score["f1"]


def scale_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    return 0.5 if pred["scale"] == gold_record["gold_scale"] else 0.0


def answer_type_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    return 0.2 if pred["answer_type"] == gold_record["gold_answer_type_norm"] else 0.0


def answer_from_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    return 0.1 if pred["answer_from"] == gold_record["gold_answer_from"] else 0.0


def rel_paragraph_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    return 0.2 * _set_f1(pred["rel_paragraphs"], gold_record["gold_rel_paragraphs_raw"])


def req_comparison_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    return 0.1 if pred["req_comparison"] == gold_record["gold_req_comparison"] else 0.0


def derivation_reward(text: str, gold_record: dict) -> float:
    pred = parse_prediction_text(text)
    if pred is None:
        return 0.0
    if gold_record["gold_answer_type_norm"] != "arithmetic":
        return 0.0
    return 0.2 if _normalize_derivation(pred["derivation"]) == _normalize_derivation(gold_record["gold_derivation"]) else 0.0


def total_reward(text: str, gold_record: dict) -> float:
    return (
        format_reward(text)
        + official_answer_reward(text, gold_record)
        + scale_reward(text, gold_record)
        + answer_type_reward(text, gold_record)
        + answer_from_reward(text, gold_record)
        + rel_paragraph_reward(text, gold_record)
        + req_comparison_reward(text, gold_record)
        + derivation_reward(text, gold_record)
    )


def reward_breakdown(text: str, gold_record: dict) -> dict:
    pred = parse_prediction_text(text)
    official = score_prediction(
        processed_row_to_official_ground_truth(gold_record),
        pred["answer"] if pred is not None else None,
        pred["scale"] if pred is not None else "",
    )
    return {
        "parsed_prediction": pred,
        "official_exact_match": official["exact_match"],
        "official_f1": official["f1"],
        "official_scale_score": official["scale_score"],
        "format_reward": format_reward(text),
        "official_answer_reward": official_answer_reward(text, gold_record),
        "scale_reward": scale_reward(text, gold_record),
        "answer_type_reward": answer_type_reward(text, gold_record),
        "answer_from_reward": answer_from_reward(text, gold_record),
        "rel_paragraph_reward": rel_paragraph_reward(text, gold_record),
        "req_comparison_reward": req_comparison_reward(text, gold_record),
        "derivation_reward": derivation_reward(text, gold_record),
        "total_reward": total_reward(text, gold_record),
    }


def smoke_test() -> None:
    gold_record = {
        "example_id": "smoke-1",
        "gold_answer": 17.7,
        "gold_scale": "percent",
        "gold_derivation": "(16.6/93.8 ) * 100",
        "gold_answer_type_raw": "arithmetic",
        "gold_answer_type_norm": "arithmetic",
        "gold_answer_from": "table-text",
        "gold_rel_paragraphs_raw": ["3"],
        "gold_req_comparison": False,
    }

    cases = [
        (
            "perfect_json",
            '{"answer":17.7,"scale":"percent","derivation":"(16.6/93.8 ) * 100","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["3"],"req_comparison":false}',
        ),
        (
            "embedded_json",
            'Prediction: {"answer":17.7,"scale":"percent","derivation":"(16.6/93.8 ) * 100","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["3"],"req_comparison":false}',
        ),
        (
            "wrong_scale",
            '{"answer":17.7,"scale":"","derivation":"(16.6/93.8 ) * 100","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["3"],"req_comparison":false}',
        ),
        (
            "invalid_scale",
            '{"answer":17.7,"scale":"trillion","derivation":"(16.6/93.8 ) * 100","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["3"],"req_comparison":false}',
        ),
        (
            "extra_key",
            '{"answer":17.7,"scale":"percent","derivation":"(16.6/93.8 ) * 100","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["3"],"req_comparison":false,"note":"x"}',
        ),
    ]

    for name, text in cases:
        print("=" * 72)
        print(name)
        print(json.dumps(reward_breakdown(text, gold_record), indent=2, ensure_ascii=False))
    print("[PASS] Smoke test passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-json", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if not args.pred_text or not args.gold_json:
        raise SystemExit("Provide --pred-text and --gold-json, or use --smoke-test")

    gold_record = json.loads(args.gold_json)
    print(json.dumps(reward_breakdown(args.pred_text, gold_record), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
