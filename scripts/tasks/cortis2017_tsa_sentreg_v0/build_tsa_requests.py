import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/cortis2017_tsa_sentreg_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_template(template: str, rec: dict) -> str:
    out = template
    out = out.replace("{{data.title_normalized}}", rec["data"]["title_normalized"])
    out = out.replace("{{data.target_company_normalized}}", rec["data"]["target_company_normalized"])
    return out


def split_to_path(task_spec: dict, split: str) -> Path:
    ds = task_spec["dataset"]
    mapping = {
        "train": ds["train_file"],
        "trial": ds["dev_file"],
        "test_inputs": ds["test_inputs_file"],
        "test_scored": ds["test_scored_file"],
    }
    return Path(mapping[split])


def default_out_path(split: str) -> Path:
    return Path(f"data/cortis2017_tsa/processed/cortis2017_tsa_{split}_requests.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "trial", "test_inputs", "test_scored"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = split_to_path(task, args.split)
    if not split_path.exists():
        raise SystemExit(f"Missing split file: {split_path}")

    out_path = Path(args.out) if args.out else default_out_path(args.split)
    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]

    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for rec in load_jsonl(split_path):
            if args.limit is not None and n >= args.limit:
                break

            row = {
                "example_id": rec["example_id"],
                "task_id": task["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": render_template(user_template, rec)}
                ]
            }

            if args.include_gold and "label" in rec:
                row["gold_label"] = rec["label"]["sentiment_score"]

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
