import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from reward_fiqasa import parse_prediction


LABELS = ["negative", "neutral", "positive"]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def safe_div(a, b):
    return a / b if b else 0.0


def compute_macro_f1(golds, preds):
    # preds can contain None
    per_class = {}
    f1s = []

    for c in LABELS:
        tp = 0
        fp = 0
        fn = 0
        for g, p in zip(golds, preds):
            if p == c and g == c:
                tp += 1
            elif p == c and g != c:
                fp += 1
            elif p != c and g == c:
                fn += 1

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0

        per_class[c] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }
        f1s.append(f1)

    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    return macro_f1, per_class


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-spec", default="tasks/fiqasa_sentiment_v0/task_spec.json")
    ap.add_argument("--split", choices=["train", "valid", "test"], default="test")
    ap.add_argument("--completions", required=True, help="JSONL with {example_id, output_text}")
    ap.add_argument("--report-out", default=None, help="Optional JSON report output path")
    args = ap.parse_args()

    task_spec = load_json(Path(args.task_spec))
    ds = task_spec["dataset"]

    split_key = f"{args.split}_file"
    split_path = Path(ds[split_key])
    completions_path = Path(args.completions)

    # Load completions (latest row per example_id wins if duplicated)
    completion_map = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        ex_id = row.get("example_id")
        out_text = row.get("output_text")
        if ex_id is None:
            continue
        completion_map[ex_id] = out_text

    total = 0
    n_with_completion = 0
    n_missing = 0
    n_format_valid = 0
    n_invalid = 0
    n_correct = 0

    golds = []
    preds = []
    confusion = Counter()

    for rec in load_jsonl(split_path):
        total += 1
        ex_id = rec["example_id"]
        gold = rec["label"]["sentiment"]

        if ex_id not in completion_map:
            n_missing += 1
            pred = None
            golds.append(gold)
            preds.append(pred)
            confusion[(gold, "MISSING")] += 1
            continue

        n_with_completion += 1
        output_text = completion_map[ex_id]

        pred = parse_prediction(output_text)

        if pred is None:
            n_invalid += 1
        else:
            n_format_valid += 1
            if pred == gold:
                n_correct += 1

        golds.append(gold)
        preds.append(pred)
        confusion[(gold, pred if pred is not None else "INVALID_OR_MISSING")] += 1

    format_valid_rate = safe_div(n_format_valid, total)
    accuracy = safe_div(n_correct, total)
    accuracy_on_valid = safe_div(n_correct, n_format_valid) if n_format_valid > 0 else 0.0
    coverage = safe_div(n_with_completion, total)

    macro_f1, per_class = compute_macro_f1(golds, preds)

    report = {
        "task_id": task_spec["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": total,
        "completion_rows_read": n_completion_rows,
        "completion_coverage": coverage,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing,
        "n_format_valid": n_format_valid,
        "n_invalid_or_unparseable": n_invalid,
        "format_valid_rate": format_valid_rate,
        "accuracy": accuracy,
        "accuracy_on_valid": accuracy_on_valid,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_counts": {f"{g} -> {p}": c for (g, p), c in sorted(confusion.items())},
    }

    print("=" * 80)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Gold file: {report['split_file']}")
    print(f"Completions: {report['completions_file']}")
    print("-" * 80)
    print(f"Total examples         : {total}")
    print(f"Completion coverage    : {coverage:.4f} ({n_with_completion}/{total})")
    print(f"Format valid rate      : {format_valid_rate:.4f} ({n_format_valid}/{total})")
    print(f"Accuracy               : {accuracy:.4f} ({n_correct}/{total})")
    print(f"Accuracy on valid only : {accuracy_on_valid:.4f}")
    print(f"Macro F1               : {macro_f1:.4f}")
    print("-" * 80)
    print("Per-class metrics:")
    for c in LABELS:
        m = per_class[c]
        print(
            f"  {c:<8} "
            f"P={m['precision']:.4f} R={m['recall']:.4f} F1={m['f1']:.4f} "
            f"(tp={m['tp']}, fp={m['fp']}, fn={m['fn']})"
        )

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("-" * 80)
        print(f"[OUT] Wrote report JSON: {out_path}")

    print("=" * 80)


if __name__ == "__main__":
    main()
