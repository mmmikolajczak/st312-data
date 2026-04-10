import argparse
import json
import re
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/fnxl_numeric_labeling_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def numeric_candidate_indices(tokens):
    out = []
    for i, tok in enumerate(tokens):
        if re.search(r"\d", str(tok)):
            out.append(i)
    return out


def render_user_prompt(rec: dict) -> str:
    tokens = rec["data"]["tokens"]
    token_lines = "\n".join(f"{i}: {tok}" for i, tok in enumerate(tokens))
    candidate_idxs = numeric_candidate_indices(tokens)
    return (
        "Identify the positively labeled numeric tokens in this sentence and assign the correct FNXL label_id to each one.\n\n"
        "Return JSON only. Output only positively labeled numeric mentions. If none are present, return {\"mentions\": []}.\n\n"
        f"Sentence:\n{rec['data']['sentence']}\n\n"
        f"Numeric-like candidate token indices: {candidate_idxs}\n\n"
        f"Indexed tokens:\n{token_lines}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test"], required=True)
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
        gold = [
            {"token_index": m["token_index"], "label_id": m["label_id"], "token": m["token"]}
            for m in rec["label"]["positive_mentions"]
        ]
        print("#" * 100)
        print(f"Example {i}")
        print(f"example_id: {rec['example_id']}")
        print(f"n_positive_mentions: {rec['label']['n_positive_mentions']}")
        print("-" * 100)
        print("[SYSTEM PROMPT]")
        print(system_prompt)
        print("-" * 100)
        print("[USER PROMPT]")
        print(render_user_prompt(rec))
        print("-" * 100)
        print("[GOLD MENTIONS]")
        print(json.dumps(gold, ensure_ascii=False, indent=2))
        print()

    print("=" * 100)
    print("Done.")
    print("=" * 100)


if __name__ == "__main__":
    main()
