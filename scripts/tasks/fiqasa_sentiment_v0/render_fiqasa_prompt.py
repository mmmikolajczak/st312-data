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
    ap.add_argument("--split", choices=["train", "valid", "test"], default="train")
    ap.add_argument("--num", type=int, default=3)
    args = ap.parse_args()

    task_spec = load_json(Path(args.task_spec))
    ds = task_spec["dataset"]

    split_key = f"{args.split}_file"
    split_path = Path(ds[split_key])

    system_prompt = task_spec["prompt_template"]["system"]
    user_template = task_spec["prompt_template"]["user"]

    print("=" * 80)
    print(f"TASK ID: {task_spec['task_id']}")
    print(f"SPLIT:   {args.split}")
    print(f"FILE:    {split_path}")
    print("=" * 80)

    for i, rec in enumerate(load_jsonl(split_path)):
        if i >= args.num:
            break

        rendered_user = render_user_template(user_template, rec)

        print("\n" + "#" * 80)
        print(f"Example {i+1}")
        print(f"example_id: {rec['example_id']}")
        print(f"gold_label: {rec['label']['sentiment']}")
        if "sentiment_score" in rec.get("label", {}):
            print(f"gold_score: {rec['label']['sentiment_score']}")
        print("-" * 80)
        print("[SYSTEM PROMPT]")
        print(system_prompt)
        print("-" * 80)
        print("[USER PROMPT]")
        print(rendered_user)

    print("\n" + "=" * 80)
    print("Done.")
    print("=" * 80)


if __name__ == "__main__":
    main()
