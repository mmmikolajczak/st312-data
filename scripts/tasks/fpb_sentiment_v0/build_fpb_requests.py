import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def render_user_template(template: str, record: dict) -> str:
    return template.replace("{{data.text}}", record["data"]["text"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-spec", default="tasks/fpb_sentiment_v0/task_spec.json")
    ap.add_argument("--split", choices=["train", "test"], default="test")
    ap.add_argument("--out", default=None, help="Output JSONL path. If omitted, auto-named in data/fpb/processed/")
    ap.add_argument("--limit", type=int, default=None, help="Optional limit for quick tests")
    ap.add_argument("--include-gold", action="store_true", help="Include gold label in output rows (debug only)")
    args = ap.parse_args()

    task_spec = load_json(Path(args.task_spec))
    dataset_info = task_spec["dataset"]
    split_key = "train_file" if args.split == "train" else "test_file"
    split_path = Path(dataset_info[split_key])

    system_prompt = task_spec["prompt_template"]["system"]
    user_template = task_spec["prompt_template"]["user"]

    if args.out is None:
        suffix = f"fpb_allagree_{args.split}_requests.jsonl"
        out_path = Path("data/fpb/processed") / suffix
    else:
        out_path = Path(args.out)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with out_path.open("w", encoding="utf-8") as f_out:
        for i, rec in enumerate(load_jsonl(split_path)):
            if args.limit is not None and i >= args.limit:
                break

            user_prompt = render_user_template(user_template, rec)

            row = {
                "example_id": rec["example_id"],
                "task_id": task_spec["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }

            # Helpful for debugging only (disable for training if you want strict separation)
            if args.include_gold:
                row["gold_label"] = rec["label"]["sentiment"]

            f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"[DONE] Wrote {n_written} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
