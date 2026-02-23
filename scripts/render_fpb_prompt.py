import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def render_user_template(template: str, record: dict) -> str:
    # Minimal placeholder replacement for this task
    text_value = record["data"]["text"]
    return template.replace("{{data.text}}", text_value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--task-spec",
        default="tasks/fpb_sentiment_v0/task_spec.json",
        help="Path to task spec JSON"
    )
    ap.add_argument(
        "--split",
        choices=["train", "test"],
        default="train",
        help="Which split file from task_spec.dataset to preview"
    )
    ap.add_argument(
        "--num",
        type=int,
        default=3,
        help="How many examples to preview"
    )
    args = ap.parse_args()

    task_spec = load_json(Path(args.task_spec))
    dataset_info = task_spec["dataset"]

    split_file_key = "train_file" if args.split == "train" else "test_file"
    split_path = Path(dataset_info[split_file_key])

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
