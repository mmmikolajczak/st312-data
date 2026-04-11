import argparse
import json
from pathlib import Path

TASK_SPEC_PATH = Path("tasks/gold_commodity_news_multilabel_v0/task_spec.json")


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


def default_out_path(split: str) -> Path:
    return Path(f"data/gold_commodity_news/processed/gold_commodity_news_{split}_requests.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    system_prompt = task["prompt_template"]["system"]
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
                    {"role": "user", "content": render_user_prompt(rec)},
                ],
            }
            if args.include_gold:
                row["gold_labels"] = label_dict_from_record(rec)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT] {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
