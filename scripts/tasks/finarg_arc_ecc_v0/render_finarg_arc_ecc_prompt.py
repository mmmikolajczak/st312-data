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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--num", type=int, default=2)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    system_prompt = task["prompt_template"]["system"]

    print("=" * 100)
    print(f"TASK ID: {task['task_id']}")
    print(f"SPLIT: {args.split}")
    print(f"FILE: {split_path}")
    print("=" * 100)
    print()

    for i, rec in enumerate(load_jsonl(split_path), start=1):
        if i > args.num:
            break
        print("#" * 100)
        print(f"Example {i}")
        print(f"example_id: {rec['example_id']}")
        print("-" * 100)
        print("[SYSTEM PROMPT]")
        print(system_prompt)
        print("-" * 100)
        print("[USER PROMPT]")
        print(render_user_prompt(rec))
        print("-" * 100)
        print("[GOLD]")
        print(json.dumps(rec["label"], ensure_ascii=False, indent=2))
        print()

    print("=" * 100)
    print("Done.")
    print("=" * 100)


if __name__ == "__main__":
    main()
