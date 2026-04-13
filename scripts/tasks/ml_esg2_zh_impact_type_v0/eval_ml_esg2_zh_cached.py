import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/ml_esg2_zh_impact_type_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from multiclass_metrics import compute_multiclass_metrics  # noqa: E402
from parse_singlelabel_json import parse_singlelabel_prediction  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
ALLOWED_LABELS = TASK_SPEC["output_schema"]["allowed_values"]["impact_type"]


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
    return Path(f"reports/ml_esg2_zh_official/ml_esg2_zh_{split}_eval_report.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split)

    comp_by_id = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            comp_by_id[example_id] = output_text

    gold_labels = []
    pred_labels = []
    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_invalid = 0

    for rec in load_jsonl(split_path):
        gold_label = rec["impact_type"]
        output_text = comp_by_id.get(rec["example_id"])
        if output_text is None:
            n_missing_completion += 1
            pred_label = None
        else:
            n_with_completion += 1
            pred_label = parse_singlelabel_prediction(output_text, ALLOWED_LABELS)
            if pred_label is None:
                n_invalid += 1
            else:
                n_format_valid += 1

        gold_labels.append(gold_label)
        pred_labels.append(pred_label)

    metrics = compute_multiclass_metrics(gold_labels, pred_labels, ALLOWED_LABELS)
    total_examples = len(gold_labels)
    n_correct = sum(1 for gold, pred in zip(gold_labels, pred_labels) if gold == pred)

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": total_examples,
        "completion_rows_read": n_completion_rows,
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing_completion,
        "n_format_valid": n_format_valid,
        "n_invalid_or_unparseable": n_invalid,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "accuracy_on_valid": n_correct / n_format_valid if n_format_valid else 0.0,
        **metrics,
    }

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    print(f"Accuracy            : {report['accuracy']:.4f}")
    print(f"Accuracy on valid   : {report['accuracy_on_valid']:.4f}")
    print(f"Macro F1            : {report['macro_f1']:.4f}")
    print(f"Weighted F1         : {report['weighted_f1']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
