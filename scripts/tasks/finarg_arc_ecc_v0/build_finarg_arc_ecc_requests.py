import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/finarg_arc_ecc_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_user_prompt(rec: dict) -> str:
    return (
        "Classify the relation between the two argument units as exactly one of "
        "\"support\", \"attack\", or \"other\".\n\n"
        "Return JSON only with exactly one key: \"label\".\n\n"
        "Argument 1:\n"
        f"{rec['data']['argument_1']}\n\n"
        "Argument 2:\n"
        f"{rec['data']['argument_2']}"
    )


def default_out_path(split: str) -> Path:
    return Path(f"data/finarg_arc_ecc_official/processed/finarg_arc_ecc_{split}_requests.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    system_prompt = task["prompt_template"]["system"]
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
                    {"role": "user", "content": render_user_prompt(rec)},
                ],
            }
            if args.include_gold:
                row["gold_label"] = rec["label"]["label"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT] {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
