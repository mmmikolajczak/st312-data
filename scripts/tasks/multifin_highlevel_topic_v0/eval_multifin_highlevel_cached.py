import argparse
import json
from collections import Counter
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

TASK_SPEC_PATH = Path("tasks/multifin_highlevel_topic_v0/task_spec.json")
REWARD_SCRIPT_PATH = Path("scripts/tasks/multifin_highlevel_topic_v0/reward_multifin_highlevel.py")

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def safe_div(a, b):
    return a / b if b else 0.0

def load_reward_module():
    spec = spec_from_file_location("reward_multifin_highlevel", REWARD_SCRIPT_PATH)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def compute_macro_f1(golds, preds, labels):
    per_class = {}
    f1s = []

    for label in labels:
        tp = sum(1 for g, p in zip(golds, preds) if g == label and p == label)
        fp = sum(1 for g, p in zip(golds, preds) if g != label and p == label)
        fn = sum(1 for g, p in zip(golds, preds) if g == label and p != label)

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)

        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }
        f1s.append(f1)

    return safe_div(sum(f1s), len(labels)), per_class

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "validation", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    reward_mod = load_reward_module()
    labels = task["output_schema"]["allowed_values"]

    split_path = Path(task["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)

    gold_rows = list(load_jsonl(split_path))
    total = len(gold_rows)

    completion_map = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        completion_map[row["example_id"]] = row["output_text"]

    n_with_completion = 0
    n_missing = 0
    n_format_valid = 0
    n_invalid = 0
    n_correct = 0

    golds = []
    preds = []
    confusion = Counter()

    for rec in gold_rows:
        ex_id = rec["example_id"]
        gold = rec["label"]["topic"]

        if ex_id not in completion_map:
            n_missing += 1
            pred = None
        else:
            n_with_completion += 1
            pred_text = completion_map[ex_id]
            pred = reward_mod.parse_prediction(pred_text)
            if pred is None:
                n_invalid += 1
            else:
                n_format_valid += 1
                if pred == gold:
                    n_correct += 1

        golds.append(gold)
        preds.append(pred)
        confusion[(gold, pred if pred is not None else "INVALID_OR_MISSING")] += 1

    coverage = safe_div(n_with_completion, total)
    format_valid_rate = safe_div(n_format_valid, total)
    accuracy = safe_div(n_correct, total)
    accuracy_on_valid = safe_div(n_correct, n_format_valid)
    macro_f1, per_class = compute_macro_f1(golds, preds, labels)

    report = {
        "task_id": task["task_id"],
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
        "confusion_counts": {f"{g} -> {p}": c for (g, p), c in sorted(confusion.items())}
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
    for c in labels:
        m = per_class[c]
        print(f"  {c:<24} P={m['precision']:.4f} R={m['recall']:.4f} F1={m['f1']:.4f} (tp={m['tp']}, fp={m['fp']}, fn={m['fn']})")

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("-" * 80)
        print(f"[OUT] Wrote report JSON: {out_path}")

    print("=" * 80)

if __name__ == "__main__":
    main()
