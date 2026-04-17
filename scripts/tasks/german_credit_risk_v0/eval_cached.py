from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/german_credit_risk_v0/task_spec.json")
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
    return Path(f"reports/statlog_german_credit_uci/german_credit_{split}_{variant}_eval_report.json")


def compute_accuracy(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    return sum(int(g == p) for g, p in zip(y_true, y_pred)) / len(y_true)


def compute_macro_f1(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    f1s = []
    for label in [0, 1]:
        tp = sum(1 for g, p in zip(y_true, y_pred) if g == label and p == label)
        fp = sum(1 for g, p in zip(y_true, y_pred) if g != label and p == label)
        fn = sum(1 for g, p in zip(y_true, y_pred) if g == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        if precision + recall == 0:
            f1s.append(0.0)
        else:
            f1s.append(2 * precision * recall / (precision + recall))
    return sum(f1s) / len(f1s)


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


def decision_cost(actual_label: str, predicted_label: str) -> int:
    if actual_label == predicted_label:
        return 0
    if actual_label == "good" and predicted_label == "bad":
        return 1
    if actual_label == "bad" and predicted_label == "good":
        return 5
    return 5


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


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int | None = None) -> Path:
    rows = []
    for idx, rec in enumerate(load_jsonl(split_path)):
        if limit is not None and idx >= limit:
            break
        rows.append({"example_id": rec["example_id"], "output_text": json.dumps({"label": rec["label_text"]}, ensure_ascii=False)})
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
    total_cost = 0
    confusion = {
        "actual_good_pred_good": 0,
        "actual_good_pred_bad": 0,
        "actual_bad_pred_good": 0,
        "actual_bad_pred_bad": 0,
    }

    for rec in split_rows:
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        rows_with_completion_text += 1
        inspection = pred["inspection"]
        if inspection["valid_json_object"]:
            rows_with_valid_json_object += 1
        if inspection["nonempty_label"]:
            rows_with_nonempty_label += 1
        if not inspection["valid_label_key"]:
            continue

        rows_with_valid_label_key += 1
        gold_label = rec["label_text"]
        pred_label = inspection["label"]
        y_true.append(0 if gold_label == "good" else 1)
        y_pred.append(0 if pred_label == "good" else 1)
        total_cost += decision_cost(gold_label, pred_label)

        confusion_key = f"actual_{gold_label}_pred_{pred_label}"
        confusion[confusion_key] += 1

    scored_examples = len(y_true)
    mean_cost = total_cost / scored_examples if scored_examples else 0.0
    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": split,
        "variant": variant,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "scored_examples": scored_examples,
        "completion_coverage": rows_with_completion_text / total_examples if total_examples else 0.0,
        "format_valid_rate": rows_with_valid_label_key / total_examples if total_examples else 0.0,
        "nonempty_label_rate": rows_with_nonempty_label / total_examples if total_examples else 0.0,
        "rows_with_completion_text": rows_with_completion_text,
        "rows_with_valid_json_object": rows_with_valid_json_object,
        "rows_with_valid_label_key": rows_with_valid_label_key,
        "rows_with_nonempty_label": rows_with_nonempty_label,
        "accuracy": compute_accuracy(y_true, y_pred),
        "mean_cost": mean_cost,
        "total_cost": total_cost,
        "normalized_cost_score": 1.0 - (mean_cost / 5.0),
        "confusion_matrix": confusion,
        **prediction_diagnostics,
    }
    if variant == "finben_optional_f1_mcc":
        report["macro_f1"] = compute_macro_f1(y_true, y_pred)
        report["mcc"] = compute_mcc(y_true, y_pred)

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "valid", "test"], default="test")
    ap.add_argument(
        "--variant",
        choices=["uci_cost_sensitive_default", "finben_optional_f1_mcc"],
        default="uci_cost_sensitive_default",
    )
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
            Path(f"reports/statlog_german_credit_uci/german_credit_{args.split}_{args.variant}_dummy_gold_predictions.jsonl"),
            limit=args.sanity_limit,
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
    print(f"Mean cost                : {report['mean_cost']:.4f}")
    print(f"Normalized cost score    : {report['normalized_cost_score']:.4f}")
    if args.variant == "finben_optional_f1_mcc":
        print(f"Macro F1                 : {report['macro_f1']:.4f}")
        print(f"MCC                      : {report['mcc']:.4f}")
    print(f"Duplicate prediction rows: {report['duplicate_prediction_rows']}")
    print(f"Unknown example-id rows  : {report['unknown_example_id_rows']}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
