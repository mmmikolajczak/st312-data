import argparse
import json
from pathlib import Path
from typing import Dict, Optional

from reward_finred_re import (
    gold_triplet_set,
    pair_set,
    parse_prediction,
    reward_breakdown,
    f1_from_sets,
)

TASK_SPEC_PATH = Path("tasks/finred_re_v0/task_spec.json")


def safe_div(a, b):
    return a / b if b else 0.0


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
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

    triplet_tp = triplet_fp = triplet_fn = 0
    pair_tp = pair_fp = pair_fn = 0

    sum_format_reward = 0.0
    sum_correctness_reward = 0.0
    sum_total_reward = 0.0
    sum_pred_triplets = 0

    for rec in load_jsonl(split_path):
        total_examples += 1
        ex_id = rec["example_id"]
        gold_triplets = rec["label"]["triplets"]
        gold_set = gold_triplet_set(gold_triplets)

        out_text = comp_by_id.get(ex_id)
        if out_text is None:
            n_missing_completion += 1
            triplet_fn += len(gold_set)
            pair_fn += len(pair_set(gold_set))
            continue

        n_with_completion += 1
        br = reward_breakdown(out_text, gold_triplets)
        sum_format_reward += br["format_reward"]
        sum_correctness_reward += br["correctness_reward_industry"]
        sum_total_reward += br["total_reward"]

        pred_set = parse_prediction(out_text)
        if pred_set is None:
            n_invalid += 1
            triplet_fn += len(gold_set)
            pair_fn += len(pair_set(gold_set))
            continue

        n_format_valid += 1
        sum_pred_triplets += len(pred_set)

        if pred_set == gold_set:
            exact_set_correct += 1

        _, _, _, tp, fp, fn = f1_from_sets(pred_set, gold_set)
        triplet_tp += tp
        triplet_fp += fp
        triplet_fn += fn

        pred_pairs = pair_set(pred_set)
        gold_pairs = pair_set(gold_set)
        _, _, _, tp, fp, fn = f1_from_sets(pred_pairs, gold_pairs)
        pair_tp += tp
        pair_fp += fp
        pair_fn += fn

    triplet_precision = safe_div(triplet_tp, triplet_tp + triplet_fp)
    triplet_recall = safe_div(triplet_tp, triplet_tp + triplet_fn)
    triplet_f1 = safe_div(2 * triplet_precision * triplet_recall, triplet_precision + triplet_recall)

    pair_precision = safe_div(pair_tp, pair_tp + pair_fp)
    pair_recall = safe_div(pair_tp, pair_tp + pair_fn)
    pair_f1 = safe_div(2 * pair_precision * pair_recall, pair_precision + pair_recall)

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
        "exact_set_accuracy": safe_div(exact_set_correct, total_examples),
        "triplet_precision": triplet_precision,
        "triplet_recall": triplet_recall,
        "triplet_f1": triplet_f1,
        "entity_pair_precision": pair_precision,
        "entity_pair_recall": pair_recall,
        "entity_pair_f1": pair_f1,
        "triplet_counts": {"tp": triplet_tp, "fp": triplet_fp, "fn": triplet_fn},
        "entity_pair_counts": {"tp": pair_tp, "fp": pair_fp, "fn": pair_fn},
        "avg_predicted_triplets_on_valid": safe_div(sum_pred_triplets, n_format_valid),
        "avg_format_reward": safe_div(sum_format_reward, total_examples),
        "avg_correctness_reward_industry": safe_div(sum_correctness_reward, total_examples),
        "avg_total_reward": safe_div(sum_total_reward, total_examples),
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Gold file: {report['split_file']}")
    print(f"Completions: {report['completions_file']}")
    print("-" * 100)
    print(f"Total examples           : {report['total_examples']}")
    print(f"Completion coverage      : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate        : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    print(f"Exact set accuracy       : {report['exact_set_accuracy']:.4f} ({exact_set_correct}/{total_examples})")
    print(f"Triplet P/R/F1           : {triplet_precision:.4f} / {triplet_recall:.4f} / {triplet_f1:.4f}")
    print(f"Entity-pair P/R/F1       : {pair_precision:.4f} / {pair_recall:.4f} / {pair_f1:.4f}")
    print(f"Avg predicted triplets   : {report['avg_predicted_triplets_on_valid']:.4f}")
    print(f"Avg format reward        : {report['avg_format_reward']:.4f}")
    print(f"Avg correctness reward   : {report['avg_correctness_reward_industry']:.4f}")
    print(f"Avg total reward         : {report['avg_total_reward']:.4f}")
    print("=" * 100)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")


if __name__ == "__main__":
    main()
