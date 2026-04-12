from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_user_prompt(template: str, text: str) -> str:
    return template.replace("{{data.text}}", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/flare_ma/processed/flare_ma_public_test.jsonl"),
    )
    parser.add_argument(
        "--task-spec",
        type=Path,
        default=Path("tasks/flare_ma_deal_completeness_v0/task_spec.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/flare_ma/processed/flare_ma_public_test_requests.jsonl"),
    )
    args = parser.parse_args()

    task_spec = json.loads(args.task_spec.read_text(encoding="utf-8"))
    system_prompt = task_spec["prompt_template"]["system"]
    user_template = task_spec["prompt_template"]["user"]

    args.out.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with args.source.open("r", encoding="utf-8") as in_f, args.out.open("w", encoding="utf-8") as out_f:
        for line in in_f:
            if not line.strip():
                continue
            ex = json.loads(line)
            request = {
                "example_id": ex["example_id"],
                "task_id": task_spec["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": render_user_prompt(user_template, ex["data"]["text"])},
                ],
                "metadata": {
                    "split": ex["split"],
                    "dataset_id": task_spec["dataset"]["dataset_id"],
                    "source_id": ex["source_id"],
                    "eval_only": True,
                },
            }
            out_f.write(json.dumps(request, ensure_ascii=False) + "\n")
            n_written += 1

    print("[DONE] Request build complete")
    print(f"[OUT] {args.out}")
    print(f"[N] {n_written}")


if __name__ == "__main__":
    main()
