from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/flare_edtsum_headline_generation_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_user_prompt(template: str, rec: dict) -> str:
    return template.replace("{{article_text}}", rec["article_text"])


def main() -> None:
    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["test"], default="test")
    ap.add_argument("--num", type=int, default=2)
    args = ap.parse_args()

    split_path = Path(task["dataset"][f"{args.split}_file"])

    print("=" * 88)
    print(f"TASK ID: {task['task_id']}")
    print(f"SPLIT:   {args.split}")
    print(f"FILE:    {split_path}")
    print("=" * 88)
    print()

    for idx, rec in enumerate(load_jsonl(split_path), start=1):
        if idx > args.num:
            break
        print("#" * 88)
        print(f"Example {idx}")
        print(f"example_id: {rec['example_id']}")
        print(f"reference_headline: {rec['reference_headline']}")
        print("-" * 88)
        print("[SYSTEM PROMPT]")
        print(task["prompt_template"]["system"])
        print("-" * 88)
        print("[USER PROMPT]")
        print(render_user_prompt(task["prompt_template"]["user"], rec))
        print()

    print("=" * 88)
    print("Done.")
    print("=" * 88)


if __name__ == "__main__":
    main()
