from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/finqa_program_generation_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_text_block(lines: list[str]) -> str:
    return "\n".join(lines) if lines else "(none)"


def render_template(template: str, rec: dict, allowed_operations: str) -> str:
    return (
        template.replace("{{question}}", rec["question"])
        .replace("{{pre_text}}", render_text_block(rec["pre_text"]))
        .replace("{{table_serialized}}", rec["table_serialized"])
        .replace("{{post_text}}", render_text_block(rec["post_text"]))
        .replace("{{allowed_operations}}", allowed_operations)
    )


def default_out_path(split: str) -> Path:
    return Path(f"tasks/finqa_program_generation_v0/requests/{split}_requests.jsonl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument(
        "--out",
        type=str,
        default=None,
        help="Override the output path. Defaults to the canonical task request artifact path under tasks/finqa_program_generation_v0/requests/.",
    )
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)

    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]
    allowed_operations = ", ".join(task["dsl"]["operation_names"])

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
                    {"role": "user", "content": render_template(user_template, rec, allowed_operations)},
                ],
            }
            if args.include_gold:
                row["gold_program_tokens"] = rec["gold_program_tokens"]
                row["gold_execution_answer"] = rec["gold_execution_answer"]

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
