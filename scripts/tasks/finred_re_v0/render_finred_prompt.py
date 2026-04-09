import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/finred_re_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_template(t: str, rec: dict) -> str:
    return t.replace("{{data.text}}", rec["data"]["text"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--num", type=int, default=2)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]

    print("=" * 100)
    print(f"TASK ID: {task['task_id']}")
    print(f"SPLIT: {args.split}")
    print(f"FILE: {split_path}")
    print("=" * 100)
    print()

    for i, rec in enumerate(load_jsonl(split_path), start=1):
        if i > args.num:
            break
        user_prompt = render_template(user_template, rec)
        gold = [
            {
                "head": x["head"]["text"],
                "relation": x["relation"],
                "tail": x["tail"]["text"],
            }
            for x in rec["label"]["triplets"]
        ]
        print("#" * 100)
        print(f"Example {i}")
        print(f"example_id: {rec['example_id']}")
        print(f"n_triplets: {rec['label']['n_triplets']}")
        print("-" * 100)
        print("[SYSTEM PROMPT]")
        print(system_prompt)
        print("-" * 100)
        print("[USER PROMPT]")
        print(user_prompt)
        print("-" * 100)
        print("[GOLD TRIPLETS]")
        print(json.dumps(gold, ensure_ascii=False, indent=2))
        print()

    print("=" * 100)
    print("Done.")
    print("=" * 100)


if __name__ == "__main__":
    main()
