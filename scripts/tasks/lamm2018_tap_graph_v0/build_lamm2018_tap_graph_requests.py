from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_user_prompt(example: dict) -> str:
    sentence = example["data"]["sentence"]
    tokens = example["data"]["tokens"]

    token_lines = [f"{tok_id}: {tok}" for tok_id, tok in enumerate(tokens)]

    allowed_nodes = [
        "agent", "cause", "co_quant", "location", "manner",
        "quant", "source", "theme", "time", "value", "whole",
    ]
    allowed_edges = ["analogy", "equivalence", "fact"]

    return (
        "Sentence:\n"
        f"{sentence}\n\n"
        "Tokens:\n"
        + "\n".join(token_lines)
        + "\n\n"
        "Return a JSON object with this exact top-level shape:\n"
        "{\n"
        '  "nodes": [\n'
        '    {"id": "n0", "label": "value", "token_start": 7, "token_end": 10}\n'
        "  ],\n"
        '  "edges": [\n'
        '    {"source_id": "n0", "target_id": "n1", "label": "fact"}\n'
        "  ]\n"
        "}\n\n"
        f"Allowed node labels: {allowed_nodes}\n"
        f"Allowed edge labels: {allowed_edges}\n\n"
        "Rules:\n"
        "- token_end is exclusive\n"
        "- labels must be lowercase\n"
        "- return JSON only\n"
        "- do not include explanations\n"
    )


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
        default=Path("data/lamm2018_tap/processed/lamm2018_tap_graph_test_requests.jsonl"),
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
                    {"role": "user", "content": render_user_prompt(example)},
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
