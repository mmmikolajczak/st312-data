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
    ap.add_argument("--include-gold", action="store_true")
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(f"data/australian_credit_uci_statlog/processed/australian_credit_{args.split}_requests.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    system_prompt = task["prompt_template"]["system"]
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for rec in load_jsonl(split_path):
            row = {
                "example_id": rec["example_id"],
                "task_id": task["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": render_user_prompt(rec)},
                ],
            }
            if args.include_gold:
                row["gold_label"] = rec["label"]["label"]
                row["gold"] = rec["label"]["gold"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT] {out_path}")
    print(f"[INFO] Source split: {split_path}")

if __name__ == "__main__":
    main()
