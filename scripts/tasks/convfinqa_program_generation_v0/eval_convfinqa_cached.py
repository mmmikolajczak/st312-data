from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/convfinqa_program_generation_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_convfinqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_convfinqa_program import equal_program, execution_matches_gold, parse_program_prediction, program_exact_match, validate_program_tokens  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_output_text(row: dict):
    for key in ["output_text", "completion", "response_text", "text"]:
        value = row.get(key)
        if isinstance(value, str):
            return value
    return None


def default_report_path(split: str) -> Path:
    return Path(f"reports/convfinqa_official/convfinqa_{split}_eval_report.json")


def load_predictions(completions_path: Path) -> tuple[dict[str, list[str] | None], str]:
    if completions_path.suffix == ".json":
        data = json.loads(completions_path.read_text(encoding="utf-8"))
        pred_by_id = {}
        for row in data:
            if isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("predicted"), list):
                pred_by_id[row["id"]] = row["predicted"]
        return pred_by_id, "official_prediction_json"

    pred_by_id = {}
    for row in load_jsonl(completions_path):
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            pred_by_id[example_id] = parse_program_prediction(output_text, require_dsl_valid=False)
    return pred_by_id, "jsonl_completions"


def available_splits(task: dict) -> list[str]:
    return [key.replace("_file", "") for key in task["dataset"] if key.endswith("_file")]


def main() -> None:
    splits = available_splits(TASK_SPEC)
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=splits, required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split)

    pred_by_id, prediction_input_format = load_predictions(completions_path)
    total_examples = 0
    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_dsl_valid = 0
    n_execution_correct = 0
    n_program_correct = 0
    n_program_exact_match = 0

    for rec in load_jsonl(split_path):
        total_examples += 1
        pred_tokens = pred_by_id.get(rec["example_id"])
        if pred_tokens is None:
            n_missing_completion += 1
            continue
        n_with_completion += 1
        if isinstance(pred_tokens, list) and pred_tokens and pred_tokens[-1] == "EOF":
            n_format_valid += 1
        valid, _ = validate_program_tokens(pred_tokens) if isinstance(pred_tokens, list) else (False, "not_a_list")
        if not valid:
            continue
        n_dsl_valid += 1
        execution_match, _, _ = execution_matches_gold(pred_tokens, rec["table"], rec["gold_execution_answer"])
        if execution_match:
            n_execution_correct += 1
        if equal_program(rec["gold_program_tokens"], pred_tokens):
            n_program_correct += 1
        if program_exact_match(rec["gold_program_tokens"], pred_tokens):
            n_program_exact_match += 1

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing_completion,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "dsl_valid_rate": n_dsl_valid / total_examples if total_examples else 0.0,
        "execution_accuracy": n_execution_correct / total_examples if total_examples else 0.0,
        "execution_accuracy_on_valid_programs": n_execution_correct / n_dsl_valid if n_dsl_valid else 0.0,
        "program_accuracy": n_program_correct / total_examples if total_examples else 0.0,
        "program_exact_match": n_program_exact_match / total_examples if total_examples else 0.0,
    }

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage            : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate             : {report['format_valid_rate']:.4f}")
    print(f"DSL valid rate                : {report['dsl_valid_rate']:.4f}")
    print(f"Execution accuracy            : {report['execution_accuracy']:.4f}")
    print(f"Execution accuracy on valid   : {report['execution_accuracy_on_valid_programs']:.4f}")
    print(f"Program accuracy              : {report['program_accuracy']:.4f}")
    print(f"Program exact match           : {report['program_exact_match']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
