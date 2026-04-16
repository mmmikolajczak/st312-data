from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/flare_edtsum_headline_generation_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_summ_shared"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from parse_reward import inspect_prediction, normalize_headline_text  # noqa: E402
from run_bartscore import compute_bartscore  # noqa: E402
from run_rouge_bertscore import compute_rouge_bertscore  # noqa: E402


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
    return Path(f"reports/flare_edtsum_public_test/flare_edtsum_{split}_{variant}_eval_report.json")


def load_predictions(path: Path, expected_ids: set[str]) -> tuple[dict[str, dict], str, dict]:
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
        inspection = inspect_prediction(output_text)
        pred_by_id[example_id] = {
            "output_text": output_text,
            "inspection": inspection,
        }
    diagnostics["duplicate_example_ids"] = sorted(duplicate_example_ids)
    diagnostics["unknown_example_ids"] = sorted(unknown_example_ids)
    return pred_by_id, "jsonl_completions", diagnostics


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int | None = None) -> Path:
    rows = []
    for idx, rec in enumerate(load_jsonl(split_path)):
        if limit is not None and idx >= limit:
            break
        rows.append(
            {
                "example_id": rec["example_id"],
                "output_text": json.dumps({"answer": rec["reference_headline"]}, ensure_ascii=False),
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def _all_reference_aligned(predictions: list[str], references: list[str]) -> bool:
    return len(predictions) == len(references) and all(pred == ref for pred, ref in zip(predictions, references))


def evaluate(split: str, variant: str, completions_path: Path, report_out: Path, *, sanity_mode: bool = False) -> dict:
    split_path = Path(TASK_SPEC["dataset"][f"{split}_file"])
    split_rows = list(load_jsonl(split_path))
    expected_ids = {rec["example_id"] for rec in split_rows}
    pred_by_id, prediction_input_format, prediction_diagnostics = load_predictions(completions_path, expected_ids)

    total_examples = 0
    rows_with_completion_text = 0
    rows_with_valid_json_object = 0
    rows_with_valid_answer_key = 0
    rows_with_nonempty_answer = 0
    metric_predictions = []
    metric_references = []

    for rec in split_rows:
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        rows_with_completion_text += 1
        inspection = pred["inspection"]
        if inspection["valid_json_object"]:
            rows_with_valid_json_object += 1
        if inspection["valid_answer_key"]:
            rows_with_valid_answer_key += 1
            metric_predictions.append(inspection["normalized_answer"])
            metric_references.append(normalize_headline_text(rec["reference_headline"]))
        if inspection["nonempty_answer"]:
            rows_with_nonempty_answer += 1

    common = {
        "rouge1": 0.0,
        "rouge2": 0.0,
        "rougeL": 0.0,
        "bertscore_precision": 0.0,
        "bertscore_recall": 0.0,
        "bertscore_f1": 0.0,
    }
    if sanity_mode and _all_reference_aligned(metric_predictions, metric_references):
        common = {
            "rouge1": 1.0,
            "rouge2": 1.0,
            "rougeL": 1.0,
            "bertscore_precision": 1.0,
            "bertscore_recall": 1.0,
            "bertscore_f1": 1.0,
        }
    elif metric_predictions:
        common = compute_rouge_bertscore(
            metric_predictions,
            metric_references,
            bertscore_model=TASK_SPEC["evaluation_config"]["variants"][variant]["bertscore_model"],
        )

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": split,
        "variant": variant,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "completion_coverage": rows_with_completion_text / total_examples if total_examples else 0.0,
        "format_valid_rate": rows_with_valid_answer_key / total_examples if total_examples else 0.0,
        "nonempty_answer_rate": rows_with_nonempty_answer / total_examples if total_examples else 0.0,
        "rows_with_completion_text": rows_with_completion_text,
        "rows_with_valid_json_object": rows_with_valid_json_object,
        "rows_with_valid_answer_key": rows_with_valid_answer_key,
        "rows_with_nonempty_answer": rows_with_nonempty_answer,
        "content_metric_examples": len(metric_predictions),
        **prediction_diagnostics,
        **common,
        "metric_versions": TASK_SPEC["evaluation_config"]["variants"][variant],
    }

    if variant == "finben_paper_alignment":
        report["bartscore"] = None
        report["bartscore_status"] = "not_run"
        if sanity_mode and _all_reference_aligned(metric_predictions, metric_references):
            report["bartscore"] = 1.0
            report["bartscore_status"] = "sanity_exact_match"
        elif metric_predictions:
            try:
                report["bartscore"] = compute_bartscore(
                    metric_predictions,
                    metric_references,
                    model_name=TASK_SPEC["evaluation_config"]["variants"][variant]["bartscore_model"],
                )["bartscore"]
                report["bartscore_status"] = "ok"
            except Exception as exc:  # pragma: no cover - dependency/runtime variability is intentional here
                report["bartscore_status"] = "error"
                report["bartscore_error"] = str(exc)
    elif variant != "stable_default":
        raise ValueError(f"Unknown variant: {variant}")

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["test"], default="test")
    ap.add_argument("--variant", choices=["stable_default", "finben_paper_alignment"], default="stable_default")
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
            Path(f"reports/flare_edtsum_public_test/flare_edtsum_{args.split}_{args.variant}_dummy_gold_predictions.jsonl"),
            limit=args.sanity_limit,
        )
    elif args.completions:
        completions_path = Path(args.completions)
    else:
        raise SystemExit("Provide --completions or use --sanity-gold")

    report = evaluate(args.split, args.variant, completions_path, report_out, sanity_mode=args.sanity_gold)

    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']} | Variant: {report['variant']}")
    print(f"Completion coverage            : {report['completion_coverage']:.4f}")
    print(f"Format valid rate             : {report['format_valid_rate']:.4f}")
    print(f"Non-empty answer rate         : {report['nonempty_answer_rate']:.4f}")
    print(f"Rows with completion text     : {report['rows_with_completion_text']}")
    print(f"Rows with valid JSON object   : {report['rows_with_valid_json_object']}")
    print(f"Rows with valid answer key    : {report['rows_with_valid_answer_key']}")
    print(f"Rows with non-empty answer    : {report['rows_with_nonempty_answer']}")
    print(f"Duplicate prediction rows     : {report['duplicate_prediction_rows']}")
    print(f"Unknown example-id rows       : {report['unknown_example_id_rows']}")
    print(f"ROUGE-1                       : {report['rouge1']:.4f}")
    print(f"ROUGE-2                       : {report['rouge2']:.4f}")
    print(f"ROUGE-L                       : {report['rougeL']:.4f}")
    print(f"BERTScore Precision           : {report['bertscore_precision']:.4f}")
    print(f"BERTScore Recall              : {report['bertscore_recall']:.4f}")
    print(f"BERTScore F1                  : {report['bertscore_f1']:.4f}")
    if args.variant == "finben_paper_alignment":
        print(f"BARTScore status              : {report['bartscore_status']}")
        print(f"BARTScore                     : {report['bartscore']}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
