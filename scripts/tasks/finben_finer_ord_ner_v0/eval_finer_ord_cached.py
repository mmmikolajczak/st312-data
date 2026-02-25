import argparse
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from collections import Counter

from reward_finer_ord_ner import parse_prediction, reward_breakdown, bio_to_spans

NON_O = {"B-PER", "I-PER", "B-LOC", "I-LOC", "B-ORG", "I-ORG"}

TASK_SPEC_PATH = Path("tasks/finben_finer_ord_ner_v0/task_spec.json")

def safe_div(a, b):
    return a / b if b else 0.0

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def extract_output_text(row: dict) -> Optional[str]:
    # support a few common cached completion schemas
    for k in ["output_text", "completion", "response_text", "text"]:
        v = row.get(k)
        if isinstance(v, str):
            return v
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    completions_path = Path(args.completions)

    # completion rows -> map by example_id
    comp_by_id: Dict[str, str] = {}
    n_completion_rows = 0
    for row in load_jsonl(completions_path):
        n_completion_rows += 1
        ex_id = row.get("example_id")
        out_text = extract_output_text(row)
        if isinstance(ex_id, str) and out_text is not None:
            comp_by_id[ex_id] = out_text

    # aggregate metrics
    total_examples = 0
    total_tokens = 0

    n_with_completion = 0
    n_missing_completion = 0
    n_format_valid = 0
    n_invalid = 0

    exact_seq_correct = 0
    token_correct = 0

    # non-O micro (token-level)
    tp_non_o = 0
    fp_non_o = 0
    fn_non_o = 0

    # entity span metrics (NER standard)
    tp_span = 0
    fp_span = 0
    fn_span = 0

    # shaped reward averages
    sum_format_reward = 0.0
    sum_correctness_reward = 0.0
    sum_total_reward = 0.0

    for rec in load_jsonl(split_path):
        total_examples += 1
        ex_id = rec["example_id"]
        gold_tags: List[str] = rec["label"]["tags"]
        total_tokens += len(gold_tags)

        out_text = comp_by_id.get(ex_id)
        if out_text is None:
            n_missing_completion += 1

            # missing completion = zero reward
            # token correctness contributes 0
            # all gold non-O tokens are missed
            for g in gold_tags:
                if g in NON_O:
                    fn_non_o += 1

            # all gold spans are missed
            gold_spans = set(bio_to_spans(gold_tags))
            fn_span += len(gold_spans)
            continue

        n_with_completion += 1

        br = reward_breakdown(out_text, gold_tags)
        sum_format_reward += br["format_reward"]
        sum_correctness_reward += br["correctness_reward_industry"]
        sum_total_reward += br["total_reward"]

        pred_tags = parse_prediction(out_text, expected_len=len(gold_tags))
        if pred_tags is None:
            n_invalid += 1

            # invalid completion => count all gold entities/tokens as missed
            for g in gold_tags:
                if g in NON_O:
                    fn_non_o += 1

            gold_spans = set(bio_to_spans(gold_tags))
            fn_span += len(gold_spans)
            continue

        n_format_valid += 1

        # exact sequence acc
        if pred_tags == gold_tags:
            exact_seq_correct += 1

        # token accuracy + non-O micro counts
        for p, g in zip(pred_tags, gold_tags):
            if p == g:
                token_correct += 1
            if p in NON_O and g in NON_O:
                if p == g:
                    tp_non_o += 1
                else:
                    fp_non_o += 1
                    fn_non_o += 1
            elif p in NON_O and g not in NON_O:
                fp_non_o += 1
            elif p not in NON_O and g in NON_O:
                fn_non_o += 1

        # entity span metrics
        pred_spans = set(bio_to_spans(pred_tags))
        gold_spans = set(bio_to_spans(gold_tags))
        tp_span += len(pred_spans & gold_spans)
        fp_span += len(pred_spans - gold_spans)
        fn_span += len(gold_spans - pred_spans)

    coverage = safe_div(n_with_completion, total_examples)
    format_valid_rate = safe_div(n_format_valid, total_examples)
    exact_sequence_accuracy = safe_div(exact_seq_correct, total_examples)
    token_accuracy = safe_div(token_correct, total_tokens)

    # token-level non-O micro F1
    precision_non_o = safe_div(tp_non_o, tp_non_o + fp_non_o)
    recall_non_o = safe_div(tp_non_o, tp_non_o + fn_non_o)
    micro_f1_non_o = safe_div(2 * precision_non_o * recall_non_o, precision_non_o + recall_non_o)

    # entity span precision/recall/F1 (NER standard)
    entity_span_precision = safe_div(tp_span, tp_span + fp_span)
    entity_span_recall = safe_div(tp_span, tp_span + fn_span)
    entity_span_f1 = safe_div(
        2 * entity_span_precision * entity_span_recall,
        entity_span_precision + entity_span_recall
    )

    avg_format_reward = safe_div(sum_format_reward, total_examples)
    avg_correctness_reward = safe_div(sum_correctness_reward, total_examples)
    avg_total_reward = safe_div(sum_total_reward, total_examples)

    report = {
        "task_id": task["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": total_examples,
        "total_tokens": total_tokens,
        "completion_rows_read": n_completion_rows,
        "completion_coverage": coverage,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing_completion,
        "n_format_valid": n_format_valid,
        "n_invalid_or_unparseable": n_invalid,
        "format_valid_rate": format_valid_rate,
        "exact_sequence_accuracy": exact_sequence_accuracy,
        "token_accuracy": token_accuracy,
        "entity_span_precision": entity_span_precision,
        "entity_span_recall": entity_span_recall,
        "entity_span_f1": entity_span_f1,
        "micro_f1_non_o": micro_f1_non_o,
        "micro_non_o_counts": {"tp": tp_non_o, "fp": fp_non_o, "fn": fn_non_o},
        "entity_span_counts": {"tp": tp_span, "fp": fp_span, "fn": fn_span},
        "avg_format_reward": avg_format_reward,
        "avg_correctness_reward_industry": avg_correctness_reward,
        "avg_total_reward": avg_total_reward
    }

    print("=" * 80)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Gold file: {report['split_file']}")
    print(f"Completions: {report['completions_file']}")
    print("-" * 80)
    print(f"Total examples         : {total_examples}")
    print(f"Total tokens           : {total_tokens}")
    print(f"Completion coverage    : {coverage:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate      : {format_valid_rate:.4f} ({n_format_valid}/{total_examples})")
    print(f"Exact sequence acc     : {exact_sequence_accuracy:.4f} ({exact_seq_correct}/{total_examples})")
    print(f"Token accuracy         : {token_accuracy:.4f}")
    print(f"Entity span P/R/F1     : {entity_span_precision:.4f} / {entity_span_recall:.4f} / {entity_span_f1:.4f}")
    print(f"Micro F1 (non-O)       : {micro_f1_non_o:.4f}")
    print(f"Avg format reward      : {avg_format_reward:.4f}")
    print(f"Avg correctness reward : {avg_correctness_reward:.4f}")
    print(f"Avg total reward       : {avg_total_reward:.4f}")
    print("=" * 80)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")

if __name__ == "__main__":
    main()
