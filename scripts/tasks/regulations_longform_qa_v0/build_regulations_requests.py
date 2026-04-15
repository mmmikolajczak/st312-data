from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/regulations_longform_qa_v0/task_spec.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def default_out_path(split: str) -> Path:
    return Path(f"tasks/regulations_longform_qa_v0/requests/{split}_requests.jsonl")


def render_user_prompt(template: str, rec: dict) -> str:
    source_metadata_lines = []
    for key, label in [
        ("source_title", "Source title"),
        ("source_document", "Source document"),
        ("source_section", "Source section"),
        ("jurisdiction", "Jurisdiction"),
        ("regulation_family", "Regulation family"),
    ]:
        value = rec.get(key)
        if isinstance(value, str) and value.strip():
            source_metadata_lines.append(f"{label}: {value}")
    source_metadata = "\n".join(source_metadata_lines) if source_metadata_lines else "(none)"
    context = rec["context"] if isinstance(rec.get("context"), str) and rec["context"].strip() else "(none)"
    return (
        template.replace("{{question}}", rec["question"])
        .replace("{{context}}", context)
        .replace("{{source_metadata}}", source_metadata)
    )


def main() -> None:
    task = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["test"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument(
        "--out",
        default=None,
        help="Override the output path. Defaults to the canonical task request artifact path under tasks/regulations_longform_qa_v0/requests/.",
    )
    args = ap.parse_args()

    split_path = Path(task["dataset"][f"{args.split}_file"])
    out_path = Path(args.out) if args.out else default_out_path(args.split)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    system_prompt = task["prompt_template"]["system"]
    user_template = task["prompt_template"]["user"]

    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for rec in load_jsonl(split_path):
            if args.limit is not None and count >= args.limit:
                break
            row = {
                "example_id": rec["example_id"],
                "task_id": task["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": render_user_prompt(user_template, rec)},
                ],
            }
            if args.include_gold:
                row["reference_answer"] = rec["reference_answer"]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1

    print(f"[DONE] Wrote {count} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")


if __name__ == "__main__":
    main()
