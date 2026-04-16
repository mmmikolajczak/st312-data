from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/bigdata22_stock_movement_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_forecast_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from parse_binary_direction import parse_label_prediction  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
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
    return Path(f"reports/bigdata22_official/bigdata22_{split}_eval_report.json")


def load_predictions(path: Path) -> tuple[dict[str, dict], str]:
    pred_by_id = {}
    for row in load_jsonl(path):
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            pred = parse_label_prediction(output_text)
            if pred is not None:
                pred_by_id[example_id] = pred
    return pred_by_id, "jsonl_completions"


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int = 1) -> Path:
    rows = []
    for rec in list(load_jsonl(split_path))[:limit]:
        rows.append(
            {
                "example_id": rec["example_id"],
                "output_text": json.dumps({"label": rec["gold_label_text"]}, ensure_ascii=False),
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def compute_accuracy(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    return sum(int(g == p) for g, p in zip(y_true, y_pred)) / len(y_true)


def compute_mcc(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    tp = sum(1 for g, p in zip(y_true, y_pred) if g == 1 and p == 1)
    tn = sum(1 for g, p in zip(y_true, y_pred) if g == 0 and p == 0)
    fp = sum(1 for g, p in zip(y_true, y_pred) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(y_true, y_pred) if g == 1 and p == 0)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denom == 0:
        return 0.0
    return (tp * tn - fp * fn) / denom


def evaluate(split: str, completions_path: Path, report_out: Path) -> dict:
    split_path = Path(TASK_SPEC["dataset"][f"{split}_file"])
    pred_by_id, prediction_input_format = load_predictions(completions_path)

    total_examples = 0
    n_with_completion = 0
    n_format_valid = 0
    y_true = []
    y_pred = []

    raw_completion_rows = {}
    for row in load_jsonl(completions_path):
        example_id = row.get("example_id")
        if isinstance(example_id, str):
            raw_completion_rows[example_id] = row

    for rec in load_jsonl(split_path):
        total_examples += 1
        if rec["example_id"] in raw_completion_rows:
            n_with_completion += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        n_format_valid += 1
        y_true.append(rec["gold_label"])
        y_pred.append(1 if pred["label"] == "Rise" else 0)

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "scored_examples": len(y_true),
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "mcc": compute_mcc(y_true, y_pred),
        "accuracy": compute_accuracy(y_true, y_pred),
    }

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "valid", "test"], default="test")
    ap.add_argument("--completions", default=None)
    ap.add_argument("--report-out", default=None)
    ap.add_argument("--sanity-gold", action="store_true")
    ap.add_argument("--sanity-limit", type=int, default=50)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split)
    if args.sanity_gold:
        completions_path = build_sanity_predictions(
            split_path,
            Path(f"reports/bigdata22_official/bigdata22_{args.split}_dummy_gold_predictions.jsonl"),
            limit=args.sanity_limit,
        )
    elif args.completions:
        completions_path = Path(args.completions)
    else:
        raise SystemExit("Provide --completions or use --sanity-gold")

    report = evaluate(args.split, completions_path, report_out)
    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f}")
    print(f"Format valid rate  : {report['format_valid_rate']:.4f}")
    print(f"MCC                : {report['mcc']:.4f}")
    print(f"Accuracy           : {report['accuracy']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
