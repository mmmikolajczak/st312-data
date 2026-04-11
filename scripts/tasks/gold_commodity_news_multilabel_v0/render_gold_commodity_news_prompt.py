import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/gold_commodity_news_multilabel_v0/task_spec.json")

LABEL_KEYS = [
    "price_or_not_norm",
    "direction_up",
    "direction_constant",
    "direction_down",
    "past_price",
    "future_price",
    "past_news",
    "future_news",
    "asset_comparison",
]


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def label_dict_from_record(rec: dict):
    raw = rec["label"]["labels_raw"]
    return {
        "price_or_not_norm": int(rec["label"]["price_or_not_norm"]),
        "direction_up": int(raw["Direction Up"]),
        "direction_constant": int(raw["Direction Constant"]),
        "direction_down": int(raw["Direction Down"]),
        "past_price": int(raw["PastPrice"]),
        "future_price": int(raw["FuturePrice"]),
        "past_news": int(raw["PastNews"]),
        "future_news": int(raw["FutureNews"]),
        "asset_comparison": int(rec["label"]["asset_comparison"]),
    }


def render_user_prompt(rec: dict) -> str:
    return (
        "Classify this gold-market news headline across all 9 binary dimensions.\n\n"
        "Return JSON only with exactly one key: \"labels\".\n\n"
        "Headline:\n"
        f"{rec['data']['headline']}"
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
        gold = label_dict_from_record(rec)
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
        print("[GOLD LABELS]")
        print(json.dumps(gold, ensure_ascii=False, indent=2))
        print()

    print("=" * 100)
    print("Done.")
    print("=" * 100)


if __name__ == "__main__":
    main()
