from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/flare_sm_cikm_stock_movement_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def default_out_path(split: str) -> Path:
    return Path(f"tasks/flare_sm_cikm_stock_movement_v0/requests/{split}_requests.jsonl")


def render_user_prompt(template: str, rec: dict) -> str:
    return template.replace("{{query}}", rec["query"]).replace("{{context_text}}", rec["context_text"])


def main() -> None:
    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "valid", "test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with out_path.open("w", encoding="utf-8") as handle:
        for rec in load_jsonl(split_path):
            if args.limit is not None and count >= args.limit:
                break
            row = {
                "example_id": rec["example_id"],
                "task_id": task["task_id"],
                "messages": [
                    {"role": "system", "content": task["prompt_template"]["system"]},
                    {"role": "user", "content": render_user_prompt(task["prompt_template"]["user"], rec)},
                ],
            }
            if args.include_gold:
                row["gold_label_text"] = rec["gold_label_text"]
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1

    print(f"[DONE] Wrote {count} request rows")
    print(f"[OUT]  {out_path}")


if __name__ == "__main__":
    main()
