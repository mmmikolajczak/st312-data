from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/stocknet_acl18_stockmove_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parse_reward import inspect_prediction  # noqa: E402


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


def default_report_path(split: str, variant: str) -> Path:
    return Path(f"reports/stocknet_acl18_paper/stocknet_acl18_{split}_{variant}_eval_report.json")


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


def load_predictions(path: Path, expected_ids: set[str], variant: str) -> tuple[dict[str, dict], str, dict]:
    pred_by_id: dict[str, dict] = {}
    duplicate_example_ids: set[str] = set()
    unknown_example_ids: set[str] = set()
    diagnostics = {
        "completion_rows_read": 0,
        "rows_missing_example_id": 0,
        "rows_missing_completion_text": 0,
        "duplicate_prediction_rows": 0,
        "duplicate_example_ids": [],
        "unknown_example_id_rows": 0,
        "unknown_example_ids": [],
        "duplicate_policy": "first_completion_wins_reported_duplicate",
    }
    for row in load_jsonl(path):
        diagnostics["completion_rows_read"] += 1
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if not isinstance(example_id, str) or not example_id.strip():
            diagnostics["rows_missing_example_id"] += 1
            continue
        example_id = example_id.strip()
        if not isinstance(output_text, str) or not output_text.strip():
            diagnostics["rows_missing_completion_text"] += 1
            continue
        if example_id not in expected_ids:
            diagnostics["unknown_example_id_rows"] += 1
            unknown_example_ids.add(example_id)
            continue
        if example_id in pred_by_id:
            diagnostics["duplicate_prediction_rows"] += 1
            duplicate_example_ids.add(example_id)
            continue
        inspection = inspect_prediction(output_text, variant=variant)
        pred_by_id[example_id] = {"output_text": output_text, "inspection": inspection}
    diagnostics["duplicate_example_ids"] = sorted(duplicate_example_ids)
    diagnostics["unknown_example_ids"] = sorted(unknown_example_ids)
    return pred_by_id, "jsonl_completions", diagnostics


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int | None = None, variant: str = "paper_default") -> Path:
    rows = []
    key = "label" if variant == "paper_default" else "answer"
    for idx, rec in enumerate(load_jsonl(split_path)):
        if limit is not None and idx >= limit:
            break
        rows.append({"example_id": rec["example_id"], "output_text": json.dumps({key: rec["label_text"]}, ensure_ascii=False)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def evaluate(split: str, variant: str, completions_path: Path, report_out: Path) -> dict:
    split_path = Path(TASK_SPEC["dataset"][f"{split}_file"])
    split_rows = list(load_jsonl(split_path))
    expected_ids = {rec["example_id"] for rec in split_rows}
    pred_by_id, prediction_input_format, prediction_diagnostics = load_predictions(completions_path, expected_ids, variant=variant)

    total_examples = 0
    rows_with_completion_text = 0
    rows_with_valid_json_object = 0
    rows_with_valid_label_key = 0
    rows_with_nonempty_label = 0
    y_true = []
    y_pred = []

    for rec in split_rows:
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        rows_with_completion_text += 1
        inspection = pred["inspection"]
        if inspection["valid_json_object"]:
            rows_with_valid_json_object += 1
        if inspection["valid_label_key"]:
            rows_with_valid_label_key += 1
            y_true.append(rec["label_int"])
            y_pred.append(1 if inspection["label"] == "Rise" else 0)
        if inspection["nonempty_label"]:
            rows_with_nonempty_label += 1

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": split,
        "variant": variant,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "scored_examples": len(y_true),
        "completion_coverage": rows_with_completion_text / total_examples if total_examples else 0.0,
        "format_valid_rate": rows_with_valid_label_key / total_examples if total_examples else 0.0,
        "nonempty_label_rate": rows_with_nonempty_label / total_examples if total_examples else 0.0,
        "rows_with_completion_text": rows_with_completion_text,
        "rows_with_valid_json_object": rows_with_valid_json_object,
        "rows_with_valid_label_key": rows_with_valid_label_key,
        "rows_with_nonempty_label": rows_with_nonempty_label,
        "accuracy": compute_accuracy(y_true, y_pred),
        "mcc": compute_mcc(y_true, y_pred),
        **prediction_diagnostics,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], default="test")
    ap.add_argument("--variant", choices=["paper_default", "finben_acl18_optional"], default="paper_default")
    ap.add_argument("--completions", default=None)
    ap.add_argument("--report-out", default=None)
    ap.add_argument("--sanity-gold", action="store_true")
    ap.add_argument("--sanity-limit", type=int, default=None)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split, args.variant)
    if args.sanity_gold:
        completions_path = build_sanity_predictions(
            split_path,
            Path(f"reports/stocknet_acl18_paper/stocknet_acl18_{args.split}_{args.variant}_dummy_gold_predictions.jsonl"),
            limit=args.sanity_limit,
            variant=args.variant,
        )
    elif args.completions:
        completions_path = Path(args.completions)
    else:
        raise SystemExit("Provide --completions or use --sanity-gold")

    report = evaluate(args.split, args.variant, completions_path, report_out)
    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']} | Variant: {report['variant']}")
    print(f"Completion coverage       : {report['completion_coverage']:.4f}")
    print(f"Format valid rate        : {report['format_valid_rate']:.4f}")
    print(f"Non-empty label rate     : {report['nonempty_label_rate']:.4f}")
    print(f"Accuracy                 : {report['accuracy']:.4f}")
    print(f"MCC                      : {report['mcc']:.4f}")
    print(f"Duplicate prediction rows: {report['duplicate_prediction_rows']}")
    print(f"Unknown example-id rows  : {report['unknown_example_id_rows']}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
