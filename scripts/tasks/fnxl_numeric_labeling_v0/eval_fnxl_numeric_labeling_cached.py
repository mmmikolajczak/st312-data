import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional

TASK_SPEC_PATH = Path("tasks/fnxl_numeric_labeling_v0/task_spec.json")


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
    if set(obj.keys()) != {"mentions"}:
        return None
    mentions = obj["mentions"]
    if not isinstance(mentions, list):
        return None

    parsed = []
    seen_pairs = set()

    for item in mentions:
        if not isinstance(item, dict):
            return None
        if set(item.keys()) != {"token_index", "label_id"}:
            return None
        token_index = item["token_index"]
        label_id = item["label_id"]
        if not isinstance(token_index, int) or token_index < 0:
            return None
        if not isinstance(label_id, int) or not (1 <= label_id <= 2799):
            return None
        pair = (token_index, label_id)
        if pair in seen_pairs:
            return None
        seen_pairs.add(pair)
        parsed.append(pair)

    parsed.sort()
    return parsed


def gold_pairs(rec):
    return sorted((int(m["token_index"]), int(m["label_id"])) for m in rec["label"]["positive_mentions"])


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

    total_examples = 0
    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_invalid = 0
    exact_set_correct = 0

    micro_tp = micro_fp = micro_fn = 0
    label_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    invalid_examples = []

    for rec in load_jsonl(split_path):
        total_examples += 1
        ex_id = rec["example_id"]
        gold = gold_pairs(rec)
        gold_set = set(gold)

        out_text = comp_by_id.get(ex_id)
        if out_text is None:
            n_missing_completion += 1
            for _, label_id in gold:
                label_counts[label_id]["fn"] += 1
            micro_fn += len(gold_set)
            continue

        n_with_completion += 1
        pred = parse_prediction(out_text)
        if pred is None:
            n_invalid += 1
            invalid_examples.append(ex_id)
            for _, label_id in gold:
                label_counts[label_id]["fn"] += 1
            micro_fn += len(gold_set)
            continue

        n_format_valid += 1
        pred_set = set(pred)

        if pred == gold:
            exact_set_correct += 1

        tp = pred_set & gold_set
        fp = pred_set - gold_set
        fn = gold_set - pred_set

        micro_tp += len(tp)
        micro_fp += len(fp)
        micro_fn += len(fn)

        for _, label_id in tp:
            label_counts[label_id]["tp"] += 1
        for _, label_id in fp:
            label_counts[label_id]["fp"] += 1
        for _, label_id in fn:
            label_counts[label_id]["fn"] += 1

    micro_p, micro_r, micro_f1 = prf(micro_tp, micro_fp, micro_fn)

    active_labels = sorted(label_counts.keys())
    macro_ps = []
    macro_rs = []
    macro_f1s = []
    for label_id in active_labels:
        c = label_counts[label_id]
        p, r, f1 = prf(c["tp"], c["fp"], c["fn"])
        macro_ps.append(p)
        macro_rs.append(r)
        macro_f1s.append(f1)

    macro_p = sum(macro_ps) / len(macro_ps) if macro_ps else 0.0
    macro_r = sum(macro_rs) / len(macro_rs) if macro_rs else 0.0
    macro_f1 = sum(macro_f1s) / len(macro_f1s) if macro_f1s else 0.0

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
        "invalid_example_ids_preview": invalid_examples[:20],
        "format_valid_rate": safe_div(n_format_valid, total_examples),
        "exact_set_accuracy": safe_div(exact_set_correct, total_examples),
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "active_label_count_in_eval": len(active_labels),
        "micro_counts": {"tp": micro_tp, "fp": micro_fp, "fn": micro_fn},
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    print(f"Exact set accuracy  : {report['exact_set_accuracy']:.4f} ({exact_set_correct}/{total_examples})")
    print(f"Micro P/R/F1        : {micro_p:.4f} / {micro_r:.4f} / {micro_f1:.4f}")
    print(f"Macro P/R/F1        : {macro_p:.4f} / {macro_r:.4f} / {macro_f1:.4f}")
    print(f"Active label count  : {len(active_labels)}")
    print(f"Invalid preview     : {invalid_examples[:10]}")
    print("=" * 100)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")


if __name__ == "__main__":
    main()
