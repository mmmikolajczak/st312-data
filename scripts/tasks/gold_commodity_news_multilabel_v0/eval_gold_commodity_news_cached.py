import argparse
import json
from pathlib import Path
from typing import Dict, Optional

TASK_SPEC_PATH = Path("tasks/gold_commodity_news_multilabel_v0/task_spec.json")

LABEL_KEYS = [
    "price_or_not_norm",
    "direction_up",
    "direction_constant",
    "direction_down",
    "past_price",
    "future_price",
    "past_news",
    "future_news",
    "asset_comparison",
]


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_output_text(row: dict) -> Optional[str]:
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
    if set(obj.keys()) != {"labels"}:
        return None
    labels = obj["labels"]
    if not isinstance(labels, dict):
        return None
    if set(labels.keys()) != set(LABEL_KEYS):
        return None

    parsed = {}
    for k in LABEL_KEYS:
        v = labels[k]
        if not isinstance(v, int) or v not in (0, 1):
            return None
        parsed[k] = int(v)
    return parsed


def gold_labels(rec: dict):
    raw = rec["label"]["labels_raw"]
    return {
        "price_or_not_norm": int(rec["label"]["price_or_not_norm"]),
        "direction_up": int(raw["Direction Up"]),
        "direction_constant": int(raw["Direction Constant"]),
        "direction_down": int(raw["Direction Down"]),
        "past_price": int(raw["PastPrice"]),
        "future_price": int(raw["FuturePrice"]),
        "past_news": int(raw["PastNews"]),
        "future_news": int(raw["FutureNews"]),
        "asset_comparison": int(rec["label"]["asset_comparison"]),
    }


def safe_div(a, b):
    return a / b if b else 0.0


def prf(tp, fp, fn):
    p = safe_div(tp, tp + fp)
    r = safe_div(tp, tp + fn)
    f1 = safe_div(2 * p * r, p + r)
    return p, r, f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)

    comp_by_id: Dict[str, str] = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        ex_id = row.get("example_id")
        out_text = extract_output_text(row)
        if isinstance(ex_id, str) and out_text is not None:
            comp_by_id[ex_id] = out_text

    per_label = {
        k: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        for k in LABEL_KEYS
    }

    total_examples = 0
    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_invalid = 0
    subset_exact = 0

    micro_tp = micro_fp = micro_fn = micro_tn = 0

    for rec in load_jsonl(split_path):
        total_examples += 1
        ex_id = rec["example_id"]
        gold = gold_labels(rec)

        out_text = comp_by_id.get(ex_id)
        if out_text is None:
            n_missing_completion += 1
            for k in LABEL_KEYS:
                g = gold[k]
                if g == 1:
                    per_label[k]["fn"] += 1
                    micro_fn += 1
                else:
                    per_label[k]["tn"] += 1
                    micro_tn += 1
            continue

        n_with_completion += 1
        pred = parse_prediction(out_text)
        if pred is None:
            n_invalid += 1
            for k in LABEL_KEYS:
                g = gold[k]
                if g == 1:
                    per_label[k]["fn"] += 1
                    micro_fn += 1
                else:
                    per_label[k]["tn"] += 1
                    micro_tn += 1
            continue

        n_format_valid += 1
        exact = 1
        for k in LABEL_KEYS:
            p = pred[k]
            g = gold[k]
            if p == 1 and g == 1:
                per_label[k]["tp"] += 1
                micro_tp += 1
            elif p == 1 and g == 0:
                per_label[k]["fp"] += 1
                micro_fp += 1
                exact = 0
            elif p == 0 and g == 1:
                per_label[k]["fn"] += 1
                micro_fn += 1
                exact = 0
            else:
                per_label[k]["tn"] += 1
                micro_tn += 1
        if exact == 1:
            subset_exact += 1

    per_label_metrics = {}
    macro_ps, macro_rs, macro_f1s, macro_accs = [], [], [], []
    for k in LABEL_KEYS:
        c = per_label[k]
        p, r, f1 = prf(c["tp"], c["fp"], c["fn"])
        acc = safe_div(c["tp"] + c["tn"], c["tp"] + c["fp"] + c["fn"] + c["tn"])
        per_label_metrics[k] = {
            "precision": p,
            "recall": r,
            "f1": f1,
            "accuracy": acc,
            "support_positive": c["tp"] + c["fn"],
            "counts": c,
        }
        macro_ps.append(p)
        macro_rs.append(r)
        macro_f1s.append(f1)
        macro_accs.append(acc)

    micro_p, micro_r, micro_f1 = prf(micro_tp, micro_fp, micro_fn)
    micro_acc = safe_div(micro_tp + micro_tn, micro_tp + micro_fp + micro_fn + micro_tn)

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
        "subset_accuracy": safe_div(subset_exact, total_examples),
        "macro_precision": sum(macro_ps) / len(macro_ps),
        "macro_recall": sum(macro_rs) / len(macro_rs),
        "macro_f1": sum(macro_f1s) / len(macro_f1s),
        "macro_accuracy": sum(macro_accs) / len(macro_accs),
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
        "micro_accuracy": micro_acc,
        "per_label_metrics": per_label_metrics,
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    print(f"Subset accuracy     : {report['subset_accuracy']:.4f} ({subset_exact}/{total_examples})")
    print(f"Macro P/R/F1        : {report['macro_precision']:.4f} / {report['macro_recall']:.4f} / {report['macro_f1']:.4f}")
    print(f"Micro P/R/F1        : {report['micro_precision']:.4f} / {report['micro_recall']:.4f} / {report['micro_f1']:.4f}")
    print("=" * 100)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")


if __name__ == "__main__":
    main()
