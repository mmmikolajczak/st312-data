from __future__ import annotations

import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/calm_taiwan_risk_v0/task_spec.json")
REPORT_DIR = Path("reports/calm_taiwan_public")
SHARED_DIR = Path(__file__).resolve().parents[1] / "_calm_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from calm_binary_wrapper import build_sanity_predictions, eval_argparser, evaluate, load_task_spec  # noqa: E402


TASK_SPEC = load_task_spec(TASK_SPEC_PATH)


def main() -> None:
    args = eval_argparser(["test"]).parse_args()
    split_path = Path(TASK_SPEC["dataset"]["test_file"])
    report_out = Path(args.report_out) if args.report_out else REPORT_DIR / "calm_taiwan_test_eval_report.json"
    if args.sanity_gold:
        completions_path = build_sanity_predictions(split_path, REPORT_DIR / "calm_taiwan_test_dummy_gold_predictions.jsonl")
    elif args.completions:
        completions_path = Path(args.completions)
    else:
        raise SystemExit("Provide --completions or use --sanity-gold")
    report = evaluate(TASK_SPEC_PATH, args.split, completions_path, report_out)
    print("=" * 88)
    print(f"Task: {report['task_id']} | Split: {report['split']} | Variant: {report['variant']}")
    print(f"Completion coverage       : {report['completion_coverage']:.4f}")
    print(f"Format valid rate        : {report['format_valid_rate']:.4f}")
    print(f"Non-empty label rate     : {report['nonempty_label_rate']:.4f}")
    print(f"Accuracy                 : {report['accuracy']:.4f}")
    print(f"Macro F1                 : {report['macro_f1']:.4f}")
    print(f"MCC                      : {report['mcc']:.4f}")
    print(f"Duplicate prediction rows: {report['duplicate_prediction_rows']}")
    print(f"Unknown example-id rows  : {report['unknown_example_id_rows']}")
    print(f"[OUT] {report_out}")


if __name__ == "__main__":
    main()
