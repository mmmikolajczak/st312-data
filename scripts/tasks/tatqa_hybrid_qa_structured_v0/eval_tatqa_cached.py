from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/tatqa_hybrid_qa_structured_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_tatqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_tatqa_prediction import SCALE_INVENTORY, parse_prediction_text  # noqa: E402
from wrap_official_tatqa_eval import OfficialTATQAMetric, processed_row_to_official_ground_truth  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_output_text(row: dict) -> str | None:
    for key in ["output_text", "completion", "response_text", "text"]:
        value = row.get(key)
        if isinstance(value, str):
            return value
    return None


def default_report_path(split: str) -> Path:
    return Path(f"reports/tatqa_official/tatqa_{split}_eval_report.json")


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
    return " ".join(text.split())


def load_predictions(path: Path) -> tuple[dict[str, dict | None], str]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            pred_by_id: dict[str, dict | None] = {}
            for example_id, value in data.items():
                if isinstance(example_id, str) and isinstance(value, list) and len(value) == 2:
                    scale = value[1] if isinstance(value[1], str) and value[1] in SCALE_INVENTORY else ""
                    pred_by_id[example_id] = {
                        "answer": value[0],
                        "scale": scale,
                        "derivation": "",
                        "answer_type": None,
                        "answer_from": None,
                        "rel_paragraphs": [],
                        "req_comparison": None,
                        "_format_valid": True,
                    }
            return pred_by_id, "official_prediction_json"

    pred_by_id = {}
    for row in load_jsonl(path):
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            parsed = parse_prediction_text(output_text)
            pred_by_id[example_id] = parsed
    return pred_by_id, "jsonl_completions"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split)

    pred_by_id, prediction_input_format = load_predictions(completions_path)
    metric = OfficialTATQAMetric()

    total_examples = 0
    n_with_completion = 0
    n_format_valid = 0
    aux_answer_type_correct = 0
    aux_answer_from_correct = 0
    aux_req_comparison_correct = 0
    aux_rel_paragraph_f1_total = 0.0
    aux_rel_paragraph_count = 0
    aux_derivation_correct = 0
    aux_derivation_count = 0

    for rec in load_jsonl(split_path):
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is not None:
            n_with_completion += 1
        if pred is not None:
            n_format_valid += 1

        metric.add(
            processed_row_to_official_ground_truth(rec),
            pred["answer"] if pred is not None else None,
            pred["scale"] if pred is not None else "",
        )

        if pred is None:
            continue

        if pred.get("answer_type") is not None:
            aux_answer_type_correct += 1 if pred["answer_type"] == rec["gold_answer_type_norm"] else 0
            aux_answer_from_correct += 1 if pred["answer_from"] == rec["gold_answer_from"] else 0
            aux_req_comparison_correct += 1 if pred["req_comparison"] == rec["gold_req_comparison"] else 0
            aux_rel_paragraph_f1_total += _set_f1(pred["rel_paragraphs"], rec["gold_rel_paragraphs_raw"])
            aux_rel_paragraph_count += 1
            if rec["gold_answer_type_norm"] == "arithmetic":
                aux_derivation_count += 1
                aux_derivation_correct += 1 if _normalize_derivation(pred["derivation"]) == _normalize_derivation(rec["gold_derivation"]) else 0

    overall = metric.get_overall_metric()
    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "exact_match": overall["exact_match"],
        "f1": overall["f1"],
        "scale_score": overall["scale_score"],
        "answer_type_accuracy_on_structured_predictions": aux_answer_type_correct / aux_rel_paragraph_count if aux_rel_paragraph_count else 0.0,
        "answer_from_accuracy_on_structured_predictions": aux_answer_from_correct / aux_rel_paragraph_count if aux_rel_paragraph_count else 0.0,
        "req_comparison_accuracy_on_structured_predictions": aux_req_comparison_correct / aux_rel_paragraph_count if aux_rel_paragraph_count else 0.0,
        "rel_paragraph_f1_on_structured_predictions": aux_rel_paragraph_f1_total / aux_rel_paragraph_count if aux_rel_paragraph_count else 0.0,
        "derivation_accuracy_on_arithmetic_structured_predictions": aux_derivation_correct / aux_derivation_count if aux_derivation_count else 0.0,
    }

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage            : {report['completion_coverage']:.4f}")
    print(f"Format valid rate             : {report['format_valid_rate']:.4f}")
    print(f"Exact match                   : {report['exact_match']:.4f}")
    print(f"F1                            : {report['f1']:.4f}")
    print(f"Scale score                   : {report['scale_score']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
