import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/finarg_arc_ecc_v0/task_spec.json")
LABELS = ["other", "support", "attack"]


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_output_text(row: dict):
    for k in ["output_text", "completion", "response_text", "text"]:
        v = row.get(k)
        if isinstance(v, str):
            return v
    return None


def _extract_json_object(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_prediction(pred_text: str):
    obj = _extract_json_object(pred_text)
    if obj is None:
        return None
    if set(obj.keys()) != {"label"}:
        return None
    label = obj["label"]
    if not isinstance(label, str):
        return None
    if label not in LABELS:
        return None
    return label


def safe_div(a, b):
    return a / b if b else 0.0


def prf(tp, fp, fn):
    p = safe_div(tp, tp + fp)
    r = safe_div(tp, tp + fn)
    f1 = safe_div(2 * p * r, p + r)
    return p, r, f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)

    comp_by_id = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        ex_id = row.get("example_id")
        out_text = extract_output_text(row)
        if isinstance(ex_id, str) and out_text is not None:
            comp_by_id[ex_id] = out_text

    counts = {lab: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for lab in LABELS}
    confusion = {gold: {pred: 0 for pred in LABELS} for gold in LABELS}

    total_examples = 0
    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_invalid = 0
    n_correct = 0

    for rec in load_jsonl(split_path):
        total_examples += 1
        gold = rec["label"]["label"]
        counts[gold]["support"] += 1

        out_text = comp_by_id.get(rec["example_id"])
        if out_text is None:
            n_missing_completion += 1
            for lab in LABELS:
                if lab == gold:
                    counts[lab]["fn"] += 1
            continue

        n_with_completion += 1
        pred = parse_prediction(out_text)
        if pred is None:
            n_invalid += 1
            for lab in LABELS:
                if lab == gold:
                    counts[lab]["fn"] += 1
            continue

        n_format_valid += 1
        confusion[gold][pred] += 1

        if pred == gold:
            n_correct += 1

        for lab in LABELS:
            if pred == lab and gold == lab:
                counts[lab]["tp"] += 1
            elif pred == lab and gold != lab:
                counts[lab]["fp"] += 1
            elif pred != lab and gold == lab:
                counts[lab]["fn"] += 1

    per_label = {}
    macro_p = macro_r = macro_f1 = 0.0
    weighted_p = weighted_r = weighted_f1 = 0.0
    total_support = sum(counts[lab]["support"] for lab in LABELS)

    micro_tp = sum(counts[lab]["tp"] for lab in LABELS)
    micro_fp = sum(counts[lab]["fp"] for lab in LABELS)
    micro_fn = sum(counts[lab]["fn"] for lab in LABELS)

    for lab in LABELS:
        c = counts[lab]
        p, r, f1 = prf(c["tp"], c["fp"], c["fn"])
        per_label[lab] = {
            "precision": p,
            "recall": r,
            "f1": f1,
            "support": c["support"],
            "counts": c,
        }
        macro_p += p
        macro_r += r
        macro_f1 += f1

        w = safe_div(c["support"], total_support)
        weighted_p += w * p
        weighted_r += w * r
        weighted_f1 += w * f1

    macro_p /= len(LABELS)
    macro_r /= len(LABELS)
    macro_f1 /= len(LABELS)

    micro_p, micro_r, micro_f1 = prf(micro_tp, micro_fp, micro_fn)
    accuracy = safe_div(n_correct, total_examples)

    report = {
        "task_id": task["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": total_examples,
        "completion_rows_read": n_completion_rows,
        "completion_coverage": safe_div(n_with_completion, total_examples),
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing_completion,
        "n_format_valid": n_format_valid,
        "n_invalid_or_unparseable": n_invalid,
        "format_valid_rate": safe_div(n_format_valid, total_examples),
        "accuracy": accuracy,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
        "weighted_precision": weighted_p,
        "weighted_recall": weighted_r,
        "weighted_f1": weighted_f1,
        "per_label_metrics": per_label,
        "confusion_matrix": confusion,
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    print(f"Accuracy            : {report['accuracy']:.4f} ({n_correct}/{total_examples})")
    print(f"Macro P/R/F1        : {report['macro_precision']:.4f} / {report['macro_recall']:.4f} / {report['macro_f1']:.4f}")
    print(f"Micro P/R/F1        : {report['micro_precision']:.4f} / {report['micro_recall']:.4f} / {report['micro_f1']:.4f}")
    print(f"Weighted P/R/F1     : {report['weighted_precision']:.4f} / {report['weighted_recall']:.4f} / {report['weighted_f1']:.4f}")
    print("=" * 100)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")


if __name__ == "__main__":
    main()
