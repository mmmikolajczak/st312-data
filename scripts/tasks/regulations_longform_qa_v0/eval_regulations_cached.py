from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/regulations_longform_qa_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_lfqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_longform_answer import normalize_answer_text, parse_answer_prediction  # noqa: E402
from run_rouge_bertscore import DEFAULT_BERTSCORE_MODEL, compute_rouge_bertscore  # noqa: E402


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
    return Path(f"reports/regulations_public_test/regulations_{split}_eval_report.json")


def load_predictions(path: Path) -> tuple[dict[str, dict | None], str]:
    pred_by_id = {}
    for row in load_jsonl(path):
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            pred_by_id[example_id] = parse_answer_prediction(output_text)
    return pred_by_id, "jsonl_completions"


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int = 3) -> Path:
    rows = []
    for idx, rec in enumerate(load_jsonl(split_path)):
        if idx >= limit:
            break
        rows.append(
            {
                "example_id": rec["example_id"],
                "output_text": json.dumps({"answer": rec["reference_answer"]}, ensure_ascii=False),
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def evaluate(split: str, completions_path: Path, report_out: Path) -> dict:
    split_path = Path(TASK_SPEC["dataset"][f"{split}_file"])
    pred_by_id, prediction_input_format = load_predictions(completions_path)

    total_examples = 0
    n_with_completion = 0
    n_format_valid = 0
    metric_predictions = []
    metric_references = []

    for rec in load_jsonl(split_path):
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        n_with_completion += 1
        n_format_valid += 1
        metric_predictions.append(normalize_answer_text(pred["answer"]))
        metric_references.append(normalize_answer_text(rec["reference_answer"]))

    metrics = {
        "rouge1": 0.0,
        "rouge2": 0.0,
        "rougeL": 0.0,
        "bertscore_precision": 0.0,
        "bertscore_recall": 0.0,
        "bertscore_f1": 0.0,
    }
    if metric_predictions:
        metrics = compute_rouge_bertscore(
            metric_predictions,
            metric_references,
            bertscore_model=TASK_SPEC["evaluation_config"]["bertscore_model"],
        )

    report = {
        "task_id": TASK_SPEC["task_id"],
        "split": split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "prediction_input_format": prediction_input_format,
        "total_examples": total_examples,
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "rouge1": metrics["rouge1"],
        "rouge2": metrics["rouge2"],
        "rougeL": metrics["rougeL"],
        "bertscore_precision": metrics["bertscore_precision"],
        "bertscore_recall": metrics["bertscore_recall"],
        "bertscore_f1": metrics["bertscore_f1"],
        "metric_versions": TASK_SPEC["evaluation_config"],
    }

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["test"], default="test")
    ap.add_argument("--completions", default=None)
    ap.add_argument("--report-out", default=None)
    ap.add_argument("--sanity-gold", action="store_true")
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split)

    if args.sanity_gold:
        completions_path = build_sanity_predictions(
            split_path,
            Path(f"reports/regulations_public_test/regulations_{args.split}_dummy_gold_predictions.jsonl"),
        )
    elif args.completions:
        completions_path = Path(args.completions)
    else:
        raise SystemExit("Provide --completions or use --sanity-gold")

    report = evaluate(args.split, completions_path, report_out)

    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage            : {report['completion_coverage']:.4f}")
    print(f"Format valid rate             : {report['format_valid_rate']:.4f}")
    print(f"ROUGE-1                       : {report['rouge1']:.4f}")
    print(f"ROUGE-2                       : {report['rouge2']:.4f}")
    print(f"ROUGE-L                       : {report['rougeL']:.4f}")
    print(f"BERTScore Precision           : {report['bertscore_precision']:.4f}")
    print(f"BERTScore Recall              : {report['bertscore_recall']:.4f}")
    print(f"BERTScore F1                  : {report['bertscore_f1']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
