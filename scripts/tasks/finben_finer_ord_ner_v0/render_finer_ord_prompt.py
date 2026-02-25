import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/finben_finer_ord_ner_v0/task_spec.json")

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def render_template(t: str, rec: dict) -> str:
    tokens = rec["data"]["tokens"]
    tokens_lines = "\n".join(tokens)
    return t.replace("{{data.tokens_lines}}", tokens_lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--num", type=int, default=2)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]

    print("=" * 80)
    print(f"TASK ID: {task['task_id']}")
    print(f"SPLIT:   {args.split}")
    print(f"FILE:    {split_path}")
    print("=" * 80)
    print()

    for i, rec in enumerate(load_jsonl(split_path), start=1):
        if i > args.num:
            break
        user_prompt = render_template(user_template, rec)
        print("#" * 80)
        print(f"Example {i}")
        print(f"example_id: {rec['example_id']}")
        print(f"n_tokens:   {len(rec['data']['tokens'])}")
        print("-" * 80)
        print("[SYSTEM PROMPT]")
        print(system_prompt)
        print("-" * 80)
        print("[USER PROMPT]")
        print(user_prompt)
        print("-" * 80)
        print("[GOLD TAGS]")
        print(rec["label"]["tags"])
        print()

    print("=" * 80)
    print("Done.")
    print("=" * 80)

if __name__ == "__main__":
    main()
