from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


BENCHMARK_NODE_LABELS = {
    "agent",
    "cause",
    "co_quant",
    "location",
    "manner",
    "quant",
    "source",
    "theme",
    "time",
    "value",
    "whole",
}
BENCHMARK_EDGE_LABELS = {"analogy", "fact", "equivalence"}


def argmax_label(score_dict: dict[str, float]) -> tuple[str | None, float]:
    if not score_dict:
        return None, 0.0

    best_label = None
    best_score = float("-inf")

    for label, score in score_dict.items():
        label_ = None if label == "null" else label
        if score > best_score:
            best_label = label_
            best_score = float(score)

    return best_label, best_score


def surface_text_from_tokens(tokens: list[str]) -> str:
    return " ".join(tokens)


def normalize_raw_node(node: list[Any], tokens: list[str]) -> dict[str, Any]:
    span, label_scores, sign_scores, manner_scores = node
    label_argmax, label_score = argmax_label(label_scores)
    sign_argmax, _ = argmax_label(sign_scores)
    manner_argmax, _ = argmax_label(manner_scores)

    start, end = span
    return {
        "span": [int(start), int(end)],
        "token_start": int(start),
        "token_end": int(end),
        "text": " ".join(tokens[start:end]),
        "label_scores": label_scores,
        "sign_scores": sign_scores,
        "manner_scores": manner_scores,
        "label_argmax": label_argmax,
        "label_argmax_score": label_score,
        "sign_argmax": sign_argmax,
        "manner_argmax": manner_argmax,
    }


def normalize_raw_edge(edge: list[Any], tokens: list[str]) -> dict[str, Any]:
    source_span, target_span, label_scores = edge
    label_argmax, label_score = argmax_label(label_scores)

    s0, s1 = source_span
    t0, t1 = target_span

    return {
        "source_span": [int(s0), int(s1)],
        "target_span": [int(t0), int(t1)],
        "source_text": " ".join(tokens[s0:s1]),
        "target_text": " ".join(tokens[t0:t1]),
        "label_scores": label_scores,
        "label_argmax": label_argmax,
        "label_argmax_score": label_score,
    }


def build_benchmark_graph(
    raw_nodes: list[dict[str, Any]],
    raw_edges: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    benchmark_nodes: list[dict[str, Any]] = []
    benchmark_edges: list[dict[str, Any]] = []

    dropped_node_labels = Counter()
    raw_node_labels = Counter()
    benchmark_node_labels = Counter()
    raw_edge_labels = Counter()
    benchmark_edge_labels = Counter()

    span_to_node_id: dict[tuple[int, int], str] = {}
    duplicate_kept_spans = 0

    for raw_node in raw_nodes:
        label = raw_node["label_argmax"]
        if label is not None:
            raw_node_labels[label] += 1

        if label not in BENCHMARK_NODE_LABELS:
            if label is not None:
                dropped_node_labels[label] += 1
            continue

        span_key = (raw_node["token_start"], raw_node["token_end"])
        if span_key in span_to_node_id:
            duplicate_kept_spans += 1
            continue

        node_id = f"n{len(benchmark_nodes)}"
        span_to_node_id[span_key] = node_id

        node = {
            "node_id": node_id,
            "label": label,
            "token_start": raw_node["token_start"],
            "token_end": raw_node["token_end"],
            "span": raw_node["span"],
            "text": raw_node["text"],
        }

        if label == "value":
            if raw_node["sign_argmax"] in {"+", "-"}:
                node["sign"] = raw_node["sign_argmax"]
            if raw_node["manner_argmax"] is not None:
                node["manner"] = raw_node["manner_argmax"]

        benchmark_nodes.append(node)
        benchmark_node_labels[label] += 1

    for raw_edge in raw_edges:
        label = raw_edge["label_argmax"]
        if label is not None:
            raw_edge_labels[label] += 1

        if label not in BENCHMARK_EDGE_LABELS:
            continue

        source_span = tuple(raw_edge["source_span"])
        target_span = tuple(raw_edge["target_span"])

        if source_span not in span_to_node_id or target_span not in span_to_node_id:
            continue

        edge = {
            "edge_id": f"e{len(benchmark_edges)}",
            "source_id": span_to_node_id[source_span],
            "target_id": span_to_node_id[target_span],
            "label": label,
            "source_span": list(source_span),
            "target_span": list(target_span),
        }
        benchmark_edges.append(edge)
        benchmark_edge_labels[label] += 1

    benchmark_graph = {
        "nodes": benchmark_nodes,
        "edges": benchmark_edges,
    }
    benchmark_meta = {
        "mode": "author_benchmark_facing_prune_plus_argmax",
        "benchmark_node_labels": sorted(BENCHMARK_NODE_LABELS),
        "benchmark_edge_labels": sorted(BENCHMARK_EDGE_LABELS),
        "raw_node_label_counts": dict(sorted(raw_node_labels.items())),
        "raw_edge_label_counts": dict(sorted(raw_edge_labels.items())),
        "benchmark_node_label_counts": dict(sorted(benchmark_node_labels.items())),
        "benchmark_edge_label_counts": dict(sorted(benchmark_edge_labels.items())),
        "dropped_node_label_counts": dict(sorted(dropped_node_labels.items())),
        "duplicate_kept_spans_dropped": duplicate_kept_spans,
    }
    return benchmark_graph, benchmark_meta


def process_split(split: str, raw_path: Path, out_path: Path) -> dict[str, Any]:
    n_examples = 0
    aggregate_raw_node_labels = Counter()
    aggregate_raw_edge_labels = Counter()
    aggregate_benchmark_node_labels = Counter()
    aggregate_benchmark_edge_labels = Counter()
    aggregate_dropped_node_labels = Counter()
    duplicate_kept_spans_total = 0

    with raw_path.open("r", encoding="utf-8") as in_f, out_path.open("w", encoding="utf-8") as out_f:
        for line_idx, line in enumerate(in_f, start=1):
            if not line.strip():
                continue

            obj = json.loads(line)
            tokens = obj["tokens"]

            raw_nodes = [normalize_raw_node(node, tokens) for node in obj.get("nodes", [])]
            raw_edges = [normalize_raw_edge(edge, tokens) for edge in obj.get("edges", [])]

            benchmark_graph, benchmark_meta = build_benchmark_graph(
                raw_nodes=raw_nodes,
                raw_edges=raw_edges,
            )

            aggregate_raw_node_labels.update(benchmark_meta["raw_node_label_counts"])
            aggregate_raw_edge_labels.update(benchmark_meta["raw_edge_label_counts"])
            aggregate_benchmark_node_labels.update(benchmark_meta["benchmark_node_label_counts"])
            aggregate_benchmark_edge_labels.update(benchmark_meta["benchmark_edge_label_counts"])
            aggregate_dropped_node_labels.update(benchmark_meta["dropped_node_label_counts"])
            duplicate_kept_spans_total += benchmark_meta["duplicate_kept_spans_dropped"]

            example_id = f"lamm2018_tap_{split}_{line_idx:04d}"
            row = {
                "example_id": example_id,
                "split": split,
                "data": {
                    "tokens": tokens,
                    "sentence": surface_text_from_tokens(tokens),
                },
                "label": {
                    "raw_graph": {
                        "nodes": raw_nodes,
                        "edges": raw_edges,
                    },
                    "benchmark_graph": benchmark_graph,
                },
                "meta": {
                    "dataset_slug": "lamm2018_tap",
                    "source_format": "author_json_graph",
                    "source_file": raw_path.name,
                    "source_line_number": line_idx,
                    "benchmark_transform": benchmark_meta,
                    "publication": {
                        "status": "blocked_pending_licensing_review",
                        "redistribution_allowed": False,
                    },
                },
            }

            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_examples += 1

    return {
        "split": split,
        "source_json": str(raw_path),
        "out_path": str(out_path),
        "n_examples": n_examples,
        "raw_node_label_counts": dict(sorted(aggregate_raw_node_labels.items())),
        "raw_edge_label_counts": dict(sorted(aggregate_raw_edge_labels.items())),
        "benchmark_node_label_counts": dict(sorted(aggregate_benchmark_node_labels.items())),
        "benchmark_edge_label_counts": dict(sorted(aggregate_benchmark_edge_labels.items())),
        "dropped_node_label_counts": dict(sorted(aggregate_dropped_node_labels.items())),
        "duplicate_kept_spans_dropped": duplicate_kept_spans_total,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/lamm2018_tap/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/lamm2018_tap/processed"))
    args = parser.parse_args()

    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()
    processed_dir.mkdir(parents=True, exist_ok=True)

    split_summaries = []
    for split in ("train", "test"):
        summary = process_split(
            split=split,
            raw_path=raw_dir / f"{split}.json",
            out_path=processed_dir / f"lamm2018_tap_{split}.jsonl",
        )
        split_summaries.append(summary)

    all_path = processed_dir / "lamm2018_tap_all.jsonl"
    with all_path.open("w", encoding="utf-8") as out_f:
        for split in ("train", "test"):
            split_path = processed_dir / f"lamm2018_tap_{split}.jsonl"
            with split_path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line)

    split_meta = {
        "dataset_module_id": "lamm2018_tap_v0",
        "dataset_slug": "lamm2018_tap",
        "split_policy": {
            "type": "author_provided",
            "preserve_official_split": True,
        },
        "split_summaries": split_summaries,
        "all_path": str(all_path),
        "audit_notes": [
            "Processed from author JSON graphs, not XML.",
            "Raw release is preserved in label.raw_graph.",
            "Benchmark-facing graph is an author-benchmark-facing prune-plus-argmax view.",
            "Released test.json contains 97 examples; keep discrepancy visible versus the paper's 100-test description.",
            "Publication remains blocked pending licensing review.",
        ],
    }

    meta_path = processed_dir / "lamm2018_tap_split_meta.json"
    meta_path.write_text(json.dumps(split_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[DONE] Clean complete")
    print(f"[META] {meta_path}")
    for summary in split_summaries:
        print(f"[{summary['split']}] {summary}")


if __name__ == "__main__":
    main()
