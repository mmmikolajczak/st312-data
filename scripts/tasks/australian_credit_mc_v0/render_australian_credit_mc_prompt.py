import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/australian_credit_mc_v0/task_spec.json")

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def render_user_prompt(rec: dict) -> str:
    return (
        "Decide whether this credit application should be approved or rejected based only on the anonymized applicant attributes.\n\n"
        'Return JSON only with exactly one key: "label".\n'
        'The value must be exactly one of "Reject" or "Approve".\n\n'
        "Applicant attributes:\n"
        f"{rec['data']['text_render']}\n\n"
        "Choices:\n"
        "- Reject\n"
        "- Approve"
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "valid", "test"], required=True)
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

    for i, rec in enumerate(load_jsonl(split_path), start=1):
        if i > args.num:
            break
        print("\n" + "#" * 100)
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
        print(json.dumps({"label": rec["label"]["label"], "gold": rec["label"]["gold"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
