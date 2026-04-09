import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional

TASK_SPEC_PATH = Path("tasks/fincausal2020_task1_sc_v0/task_spec.json")
OFFICIAL_SCORER = Path("data/fincausal2020_official/raw/scoring/task1/task1_evaluate.py")


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


def parse_prediction(pred_text: str):
    try:
        start = pred_text.find("{")
        end = pred_text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        obj = json.loads(pred_text[start:end + 1])
    except Exception:
        return None
    if not isinstance(obj, dict) or set(obj.keys()) != {"label"}:
        return None
    return obj["label"] if obj["label"] in [0, 1] else None


def parse_scores(score_path: Path):
    scores = {}
    with score_path.open("r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                scores[k.strip()] = float(v.strip())
    return scores


def sanitize_field(s: str) -> str:
    return s.replace("\r", " ").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["trial", "practice"], required=True)
    ap.add_argument("--completions", required=True)
    ap.add_argument("--report-out", default=None)
    args = ap.parse_args()

    if not OFFICIAL_SCORER.exists():
        raise SystemExit(f"Official scorer not found: {OFFICIAL_SCORER}")

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
    n_format_valid = 0
    n_missing_completion = 0
    n_invalid = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        ref_file = tmpdir / "ref.csv"
        pred_file = tmpdir / "pred.csv"
        score_file = tmpdir / "scores.txt"

        with ref_file.open("w", encoding="utf-8", newline="") as f_ref, pred_file.open("w", encoding="utf-8", newline="") as f_pred:
            ref_writer = csv.writer(f_ref, delimiter=";")
            pred_writer = csv.writer(f_pred, delimiter=";")

            ref_writer.writerow(["Index", "Text", "Gold"])
            pred_writer.writerow(["Index", "Text", "Gold"])

            for rec in load_jsonl(split_path):
                total_examples += 1
                raw_index = rec["meta"]["raw_index"]
                text = sanitize_field(rec["data"]["text"])
                gold = rec["label"]["gold"]

                out_text = comp_by_id.get(rec["example_id"])
                if out_text is None:
                    n_missing_completion += 1
                    pred_label = 0
                else:
                    n_with_completion += 1
                    parsed = parse_prediction(out_text)
                    if parsed is None:
                        n_invalid += 1
                        pred_label = 0
                    else:
                        n_format_valid += 1
                        pred_label = int(parsed)

                ref_writer.writerow([raw_index, text, gold])
                pred_writer.writerow([raw_index, text, pred_label])

        subprocess.run(
            [sys.executable, str(OFFICIAL_SCORER), "from-file", "--ref_file", str(ref_file), str(pred_file), str(score_file)],
            check=True,
        )

        scorer_scores = parse_scores(score_file)

    report = {
        "task_id": task["task_id"],
        "split": args.split,
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": total_examples,
        "completion_rows_read": n_completion_rows,
        "completion_coverage": n_with_completion / total_examples if total_examples else 0.0,
        "n_with_completion": n_with_completion,
        "n_missing_completion": n_missing_completion,
        "n_format_valid": n_format_valid,
        "n_invalid_or_unparseable": n_invalid,
        "format_valid_rate": n_format_valid / total_examples if total_examples else 0.0,
        "official_scores": scorer_scores,
    }

    print("=" * 100)
    print(f"Task: {report['task_id']} | Split: {report['split']}")
    print(f"Completion coverage : {report['completion_coverage']:.4f} ({n_with_completion}/{total_examples})")
    print(f"Format valid rate   : {report['format_valid_rate']:.4f} ({n_format_valid}/{total_examples})")
    for k, v in scorer_scores.items():
        print(f"{k}: {v:.6f}")
    print("=" * 100)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OUT] Wrote report JSON: {out_path}")


if __name__ == "__main__":
    main()
