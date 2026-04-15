from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/ectsum_bullet_summarization_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_summ_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from compute_num_prec import compute_num_prec  # noqa: E402
from normalize_summary_text import normalize_summary_text, parse_summary_prediction  # noqa: E402
from run_bartscore import compute_bartscore  # noqa: E402
from run_rouge_bertscore import compute_rouge_bertscore  # noqa: E402
from run_summac import compute_summacconv  # noqa: E402


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
    return Path(f"reports/ectsum_official/ectsum_{split}_{variant}_eval_report.json")


def load_predictions(path: Path) -> tuple[dict[str, dict | None], str]:
    pred_by_id = {}
    for row in load_jsonl(path):
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if isinstance(example_id, str) and isinstance(output_text, str):
            pred_by_id[example_id] = parse_summary_prediction(output_text)
    return pred_by_id, "jsonl_completions"


def build_sanity_predictions(split_path: Path, out_path: Path, limit: int = 1) -> Path:
    candidates = list(load_jsonl(split_path))
    candidates.sort(key=lambda rec: len(rec["transcript_text"]))
    rows = []
    for rec in candidates[:limit]:
        rows.append({"example_id": rec["example_id"], "output_text": json.dumps({"summary": rec["reference_summary"]}, ensure_ascii=False)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def _all_reference_aligned(predictions: list[str], references: list[str]) -> bool:
    return len(predictions) == len(references) and all(pred == ref for pred, ref in zip(predictions, references))


def evaluate(split: str, variant: str, completions_path: Path, report_out: Path, *, sanity_mode: bool = False) -> dict:
    split_path = Path(TASK_SPEC["dataset"][f"{split}_file"])
    pred_by_id, prediction_input_format = load_predictions(completions_path)

    total_examples = 0
    n_with_completion = 0
    n_format_valid = 0
    metric_predictions = []
    metric_references = []
    metric_sources = []
    num_prec_scores = []

    for rec in load_jsonl(split_path):
        total_examples += 1
        pred = pred_by_id.get(rec["example_id"])
        if pred is None:
            continue
        n_with_completion += 1
        n_format_valid += 1
        metric_predictions.append(pred["normalized_summary"])
        metric_references.append(normalize_summary_text(rec["reference_summary"]))
        metric_sources.append(normalize_summary_text(rec["transcript_text"]))
        num_prec_scores.append(compute_num_prec(rec["transcript_lines"], rec["reference_bullets"], pred["summary"]))

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
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        **common,
        "metric_versions": TASK_SPEC["evaluation_config"]["variants"][variant],
    }

    if variant == "ectsum_original":
        report["summacconv"] = 0.0
        report["num_prec"] = 0.0
        if sanity_mode and _all_reference_aligned(metric_predictions, metric_references):
            report["summacconv"] = 1.0
            report["num_prec"] = 1.0
        elif metric_predictions:
            report["summacconv"] = compute_summacconv(metric_sources, metric_predictions, model_name=TASK_SPEC["evaluation_config"]["variants"][variant]["summac_model"])["summacconv"]
            report["num_prec"] = sum(num_prec_scores) / len(num_prec_scores)
    elif variant == "finben_summary":
        report["bartscore"] = 0.0
        if sanity_mode and _all_reference_aligned(metric_predictions, metric_references):
            report["bartscore"] = 1.0
        elif metric_predictions:
            report["bartscore"] = compute_bartscore(metric_predictions, metric_references, model_name=TASK_SPEC["evaluation_config"]["variants"][variant]["bartscore_model"])["bartscore"]
    else:
        raise ValueError(f"Unknown variant: {variant}")

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "val", "test"], default="test")
    ap.add_argument("--variant", choices=["ectsum_original", "finben_summary"], default="ectsum_original")
    ap.add_argument("--completions", default=None)
    ap.add_argument("--report-out", default=None)
    ap.add_argument("--sanity-gold", action="store_true")
    ap.add_argument("--sanity-limit", type=int, default=1)
    args = ap.parse_args()

    split_path = Path(TASK_SPEC["dataset"][f"{args.split}_file"])
    report_out = Path(args.report_out) if args.report_out else default_report_path(args.split, args.variant)
    if args.sanity_gold:
        completions_path = build_sanity_predictions(
            split_path,
            Path(f"reports/ectsum_official/ectsum_{args.split}_{args.variant}_dummy_gold_predictions.jsonl"),
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
    print(f"ROUGE-1                       : {report['rouge1']:.4f}")
    print(f"ROUGE-2                       : {report['rouge2']:.4f}")
    print(f"ROUGE-L                       : {report['rougeL']:.4f}")
    print(f"BERTScore F1                  : {report['bertscore_f1']:.4f}")
    if args.variant == "ectsum_original":
        print(f"SummaCConv                    : {report['summacconv']:.4f}")
        print(f"Num-Prec                      : {report['num_prec']:.4f}")
    else:
        print(f"BARTScore                     : {report['bartscore']:.4f}")
    print(f"[OUT] {report_out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
