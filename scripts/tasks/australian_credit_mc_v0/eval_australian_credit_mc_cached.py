import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/australian_credit_mc_v0/task_spec.json")
LABELS = ["Reject", "Approve"]

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def extract_output_text(row):
    for key in ["output_text", "completion", "response_text", "text"]:
        v = row.get(key)
        if isinstance(v, str):
            return v
    return None

def parse_prediction(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end+1])
    except Exception:
        return None
    if not isinstance(obj, dict) or set(obj.keys()) != {"label"}:
        return None
    label = obj["label"]
    if not isinstance(label, str) or label not in LABELS:
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
    ap.add_argument("--split", choices=["train", "valid", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", required=True)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)

    comp_by_id = {}
    for row in load_jsonl(completions_path):
        ex_id = row.get("example_id")
        out = extract_output_text(row)
        if isinstance(ex_id, str) and isinstance(out, str):
            comp_by_id[ex_id] = out

    counts = {lab: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for lab in LABELS}
    total = 0
    n_format_valid = 0
    n_correct = 0

    for rec in load_jsonl(split_path):
        total += 1
        gold = rec["label"]["label"]
        counts[gold]["support"] += 1
        pred = parse_prediction(comp_by_id.get(rec["example_id"]))
        if pred is not None:
            n_format_valid += 1
        if pred == gold:
            n_correct += 1
        for lab in LABELS:
            if pred == lab and gold == lab:
                counts[lab]["tp"] += 1
            elif pred == lab and gold != lab:
                counts[lab]["fp"] += 1
            elif pred != lab and gold == lab:
                counts[lab]["fn"] += 1

    per = {}
    macro_p = macro_r = macro_f1 = 0.0
    weighted_p = weighted_r = weighted_f1 = 0.0
    total_support = sum(counts[l]["support"] for l in LABELS)

    micro_tp = sum(counts[l]["tp"] for l in LABELS)
    micro_fp = sum(counts[l]["fp"] for l in LABELS)
    micro_fn = sum(counts[l]["fn"] for l in LABELS)

    for lab in LABELS:
        p, r, f1 = prf(counts[lab]["tp"], counts[lab]["fp"], counts[lab]["fn"])
        per[lab] = {"precision": p, "recall": r, "f1": f1, "support": counts[lab]["support"]}
        macro_p += p
        macro_r += r
        macro_f1 += f1
        w = safe_div(counts[lab]["support"], total_support)
        weighted_p += w * p
        weighted_r += w * r
        weighted_f1 += w * f1

    macro_p /= len(LABELS)
    macro_r /= len(LABELS)
    macro_f1 /= len(LABELS)
    micro_p, micro_r, micro_f1 = prf(micro_tp, micro_fp, micro_fn)
    accuracy = safe_div(n_correct, total)

    report = {
        "task_id": task["task_id"],
        "split": args.split,
        "total_examples": total,
        "n_format_valid": n_format_valid,
        "format_valid_rate": safe_div(n_format_valid, total),
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
        "per_class_metrics": per,
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total})")
    print(f"Accuracy            : {report['accuracy']:.4f} ({n_correct}/{total})")
    print(f"Macro P/R/F1        : {report['macro_precision']:.4f} / {report['macro_recall']:.4f} / {report['macro_f1']:.4f}")
    print(f"Micro P/R/F1        : {report['micro_precision']:.4f} / {report['micro_recall']:.4f} / {report['micro_f1']:.4f}")
    print(f"Weighted P/R/F1     : {report['weighted_precision']:.4f} / {report['weighted_recall']:.4f} / {report['weighted_f1']:.4f}")
    print("=" * 100)

    out_path = Path(args.report_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OUT] Wrote report JSON: {out_path}")

if __name__ == "__main__":
    main()
