import argparse
import json
import math
from pathlib import Path

from reward_tsa_sentreg import parse_prediction


TASK_SPEC_PATH = Path("tasks/cortis2017_tsa_sentreg_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def safe_div(a, b):
    return a / b if b != 0 else 0.0


def sign_bucket(x: float, eps: float = 1e-12) -> int:
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def cosine_similarity(xs, ys):
    if len(xs) != len(ys):
        raise ValueError("Cosine inputs must have the same length")
    if not xs:
        return 0.0
    dot = sum(x * y for x, y in zip(xs, ys))
    nx = math.sqrt(sum(x * x for x in xs))
    ny = math.sqrt(sum(y * y for y in ys))
    if nx == 0.0 and ny == 0.0:
        return 1.0 if all(abs(x - y) <= 1e-12 for x, y in zip(xs, ys)) else 0.0
    if nx == 0.0 or ny == 0.0:
        return 0.0
    return dot / (nx * ny)


def rmse(errors):
    return math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0


def split_to_gold_path(task_spec: dict, split: str) -> Path:
    ds = task_spec["dataset"]
    mapping = {
        "train": ds["train_file"],
        "trial": ds["dev_file"],
        "test_scored": ds["test_scored_file"],
    }
    return Path(mapping[split])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "trial", "test_scored"], default="trial")
    ap.add_argument("--completions", required=True, help="JSONL with fields: example_id, output_text")
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    task_spec = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    gold_path = split_to_gold_path(task_spec, args.split)
    if not gold_path.exists():
        raise SystemExit(f"Missing gold split file: {gold_path}")

    gold_rows = list(load_jsonl(gold_path))
    gold_by_id = {row["example_id"]: row for row in gold_rows}

    comp_by_id = {}
    n_completion_rows = 0
    for rec in load_jsonl(Path(args.completions)):
        n_completion_rows += 1
        ex_id = rec.get("example_id")
        if ex_id is None:
            continue
        comp_by_id[ex_id] = rec.get("output_text")

    total = len(gold_rows)
    n_with_completion = 0
    n_format_valid = 0
    n_missing = 0
    n_invalid = 0

    gold_scores_valid = []
    pred_scores_valid = []
    abs_errors = []
    sign_hits = 0

    for row in gold_rows:
        ex_id = row["example_id"]
        gold = float(row["label"]["sentiment_score"])
        output_text = comp_by_id.get(ex_id)

        if output_text is None:
            n_missing += 1
            continue

        n_with_completion += 1
        pred = parse_prediction(output_text)
        if pred is None:
            n_invalid += 1
            continue

        n_format_valid += 1
        gold_scores_valid.append(gold)
        pred_scores_valid.append(pred)
        abs_errors.append(abs(pred - gold))
        if sign_bucket(pred) == sign_bucket(gold):
            sign_hits += 1

    coverage = safe_div(n_format_valid, total)
    cosine = cosine_similarity(gold_scores_valid, pred_scores_valid)
    weighted_cosine = cosine * coverage
    mae = sum(abs_errors) / len(abs_errors) if abs_errors else 0.0
    rmse_value = rmse([p - g for p, g in zip(pred_scores_valid, gold_scores_valid)])
    sign_accuracy = safe_div(sign_hits, n_format_valid)
    format_valid_rate = safe_div(n_format_valid, total)

    report = {
        "task_id": task_spec["task_id"],
        "split": args.split,
        "gold_file": str(gold_path),
        "completions_file": str(args.completions),
        "total_examples": total,
        "completion_rows_read": n_completion_rows,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing,
        "n_invalid_or_unparseable": n_invalid,
        "n_format_valid": n_format_valid,
        "coverage": coverage,
        "format_valid_rate": format_valid_rate,
        "cosine_similarity": cosine,
        "weighted_cosine_similarity": weighted_cosine,
        "mae": mae,
        "rmse": rmse_value,
        "sign_accuracy": sign_accuracy
    }

    print("=" * 80)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Gold file: {report['gold_file']}")
    print(f"Completions: {report['completions_file']}")
    print("-" * 80)
    print(f"Total examples              : {total}")
    print(f"Completion rows read        : {n_completion_rows}")
    print(f"Format-valid predictions    : {n_format_valid}/{total} ({format_valid_rate:.4f})")
    print(f"Coverage                    : {coverage:.4f}")
    print(f"Cosine similarity           : {cosine:.6f}")
    print(f"Weighted cosine similarity  : {weighted_cosine:.6f}")
    print(f"MAE                         : {mae:.6f}")
    print(f"RMSE                        : {rmse_value:.6f}")
    print(f"Sign accuracy               : {sign_accuracy:.6f}")
    print("=" * 80)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[OUT] {out_path}")


if __name__ == "__main__":
    main()
