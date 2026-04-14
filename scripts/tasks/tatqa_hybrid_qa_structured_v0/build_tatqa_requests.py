from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/tatqa_hybrid_qa_structured_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def render_template(template: str, rec: dict, scale_values: str, answer_type_values: str, answer_from_values: str) -> str:
    return (
        template.replace("{{question}}", rec["question"])
        .replace("{{table_serialized}}", rec["table_serialized"])
        .replace("{{paragraphs_serialized}}", rec["paragraphs_serialized"])
        .replace("{{scale_values}}", scale_values)
        .replace("{{answer_type_values}}", answer_type_values)
        .replace("{{answer_from_values}}", answer_from_values)
    )


def default_out_path(split: str) -> Path:
    return Path(f"tasks/tatqa_hybrid_qa_structured_v0/requests/{split}_requests.jsonl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument(
        "--out",
        type=str,
        default=None,
        help="Override the output path. Defaults to the canonical task request artifact path under tasks/tatqa_hybrid_qa_structured_v0/requests/.",
    )
    args = ap.parse_args()

    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))
    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)
    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]
    scale_values = ", ".join(json.dumps(value, ensure_ascii=False) for value in task["output_schema"]["allowed_values"]["scale"])
    answer_type_values = ", ".join(task["output_schema"]["allowed_values"]["answer_type"])
    answer_from_values = ", ".join(task["output_schema"]["allowed_values"]["answer_from"])

    out_path.parent.mkdir(parents=True, exist_ok=True)

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
                    {
                        "role": "user",
                        "content": render_template(
                            user_template,
                            rec,
                            scale_values,
                            answer_type_values,
                            answer_from_values,
                        ),
                    },
                ],
            }
            if args.include_gold:
                row["gold_answer"] = rec["gold_answer"]
                row["gold_scale"] = rec["gold_scale"]
                row["gold_derivation"] = rec["gold_derivation"]
                row["gold_answer_type_norm"] = rec["gold_answer_type_norm"]
                row["gold_answer_from"] = rec["gold_answer_from"]
                row["gold_rel_paragraphs_raw"] = rec["gold_rel_paragraphs_raw"]
                row["gold_req_comparison"] = rec["gold_req_comparison"]

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    print(f"[DONE] Wrote {n} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
