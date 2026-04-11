from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_NODES = [
    "agent", "cause", "co_quant", "location", "manner",
    "quant", "source", "theme", "time", "value", "whole",
]
ALLOWED_EDGES = ["analogy", "equivalence", "fact"]


def render_user_prompt(example: dict, task_spec: dict) -> str:
    sentence = example["data"]["sentence"]
    tokens = example["data"]["tokens"]
    token_lines = "\n".join(f"{tok_id}: {tok}" for tok_id, tok in enumerate(tokens))

    template = task_spec["prompt_template"]["user"]
    rendered = template
    rendered = rendered.replace("{{data.sentence}}", sentence)
    rendered = rendered.replace("{{token_lines}}", token_lines)
    rendered = rendered.replace("{{allowed_node_labels}}", str(ALLOWED_NODES))
    rendered = rendered.replace("{{allowed_edge_labels}}", str(ALLOWED_EDGES))
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/lamm2018_tap/processed/lamm2018_tap_test.jsonl"),
    )
    parser.add_argument(
        "--task-spec",
        type=Path,
        default=Path("tasks/lamm2018_tap_graph_v0/task_spec.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/lamm2018_tap/processed/lamm2018_tap_test_requests.jsonl"),
    )
    args = parser.parse_args()

    task_spec = json.loads(args.task_spec.read_text(encoding="utf-8"))
    system_prompt = task_spec["prompting"]["system_prompt"]

    args.out.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with args.source.open("r", encoding="utf-8") as in_f, args.out.open("w", encoding="utf-8") as out_f:
        for line in in_f:
            if not line.strip():
                continue
            example = json.loads(line)
            request = {
                "example_id": example["example_id"],
                "task_id": task_spec["task_id"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": render_user_prompt(example, task_spec)},
                ],
                "metadata": {
                    "split": example["split"],
                    "dataset_module_id": task_spec["dataset_module_id"],
                    "benchmark_mode": example["meta"]["benchmark_transform"]["mode"],
                },
            }
            out_f.write(json.dumps(request, ensure_ascii=False) + "\n")
            n_written += 1

    print("[DONE] Request build complete")
    print(f"[OUT] {args.out}")
    print(f"[N] {n_written}")


if __name__ == "__main__":
    main()
