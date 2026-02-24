import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def safe_str(x):
    if x is None:
        return ""
    return str(x)


def render_user_template(template: str, record: dict) -> str:
    data = record.get("data", {})
    out = template
    out = out.replace("{{data.text}}", safe_str(data.get("text")))
    out = out.replace("{{data.target}}", safe_str(data.get("target")))
    out = out.replace("{{data.aspect}}", safe_str(data.get("aspect")))
    out = out.replace("{{data.type}}", safe_str(data.get("type")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-spec", default="tasks/fiqasa_sentiment_v0/task_spec.json")
    ap.add_argument("--split", choices=["train", "valid", "test"], default="test")
    ap.add_argument("--out", default=None, help="Output JSONL path (optional)")
    ap.add_argument("--limit", type=int, default=None, help="Optional limit for preview/debug")
    ap.add_argument("--include-gold", action="store_true", help="Include gold label in rows (debug only)")
    args = ap.parse_args()

    task_spec = load_json(Path(args.task_spec))
    ds = task_spec["dataset"]

    split_key = f"{args.split}_file"
    split_path = Path(ds[split_key])

    system_prompt = task_spec["prompt_template"]["system"]
    user_template = task_spec["prompt_template"]["user"]

    if args.out is None:
        out_path = Path(f"data/fiqasa/processed/fiqasa_{args.split}_requests.jsonl")
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

            if args.include_gold:
                row["gold_label"] = rec["label"]["sentiment"]
                if "sentiment_score" in rec["label"]:
                    row["gold_score"] = rec["label"]["sentiment_score"]

            f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"[DONE] Wrote {n_written} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
