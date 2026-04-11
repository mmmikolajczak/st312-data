from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_NODE_LABELS = {
    "agent", "cause", "co_quant", "location", "manner",
    "quant", "source", "theme", "time", "value", "whole",
}
ALLOWED_EDGE_LABELS = {"analogy", "equivalence", "fact"}


@dataclass(frozen=True)
class Node:
    label: str
    token_start: int
    token_end: int


@dataclass(frozen=True)
class Triple:
    src_label: str
    src_start: int
    src_end: int
    edge_label: str
    dst_label: str
    dst_start: int
    dst_end: int


def overlap_len(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def node_overlap_score(a: Node, b: Node) -> float:
    if a.label != b.label:
        return 0.0
    ov = overlap_len(a.token_start, a.token_end, b.token_start, b.token_end)
    if ov == 0:
        return 0.0
    len_a = max(1, a.token_end - a.token_start)
    len_b = max(1, b.token_end - b.token_start)
    return 2.0 * ov / (len_a + len_b)


def triple_overlap_score(a: Triple, b: Triple) -> float:
    if a.edge_label != b.edge_label:
        return 0.0
    if a.src_label != b.src_label or a.dst_label != b.dst_label:
        return 0.0

    ov_src = overlap_len(a.src_start, a.src_end, b.src_start, b.src_end)
    ov_dst = overlap_len(a.dst_start, a.dst_end, b.dst_start, b.dst_end)
    if ov_src == 0 or ov_dst == 0:
        return 0.0

    len_src_a = max(1, a.src_end - a.src_start)
    len_src_b = max(1, b.src_end - b.src_start)
    len_dst_a = max(1, a.dst_end - a.dst_start)
    len_dst_b = max(1, b.dst_end - b.dst_start)

    src_score = 2.0 * ov_src / (len_src_a + len_src_b)
    dst_score = 2.0 * ov_dst / (len_dst_a + len_dst_b)
    return 0.5 * (src_score + dst_score)


def greedy_match(pred_items: list[Any], gold_items: list[Any], score_fn) -> int:
    candidates = []
    for i, pred in enumerate(pred_items):
        for j, gold in enumerate(gold_items):
            score = score_fn(pred, gold)
            if score > 0:
                candidates.append((score, i, j))

    candidates.sort(reverse=True)

    used_pred = set()
    used_gold = set()
    matches = 0

    for _, i, j in candidates:
        if i in used_pred or j in used_gold:
            continue
        used_pred.add(i)
        used_gold.add(j)
        matches += 1

    return matches


def prf(matches: int, n_pred: int, n_gold: int) -> dict[str, float]:
    precision = matches / n_pred if n_pred else 0.0
    recall = matches / n_gold if n_gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def graph_to_nodes_and_triples(graph: dict[str, Any]) -> tuple[list[Node], list[Triple]]:
    nodes_by_id = {}
    for node in graph.get("nodes", []):
        nodes_by_id[node["node_id"]] = Node(
            label=node["label"],
            token_start=int(node["token_start"]),
            token_end=int(node["token_end"]),
        )

    triples = []
    for edge in graph.get("edges", []):
        src_id = edge["source_id"]
        dst_id = edge["target_id"]
        if src_id not in nodes_by_id or dst_id not in nodes_by_id:
            continue

        src = nodes_by_id[src_id]
        dst = nodes_by_id[dst_id]

        triples.append(
            Triple(
                src_label=src.label,
                src_start=src.token_start,
                src_end=src.token_end,
                edge_label=edge["label"],
                dst_label=dst.label,
                dst_start=dst.token_start,
                dst_end=dst.token_end,
            )
        )

    return list(nodes_by_id.values()), triples


def parse_prediction(row: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(row.get("prediction"), dict):
        return row["prediction"]

    if isinstance(row.get("parsed_output"), dict):
        return row["parsed_output"]

    if isinstance(row.get("content"), str):
        try:
            return json.loads(row["content"])
        except json.JSONDecodeError:
            return None

    if isinstance(row.get("response"), dict):
        for key in ("prediction", "parsed_output"):
            if isinstance(row["response"].get(key), dict):
                return row["response"][key]
        if isinstance(row["response"].get("content"), str):
            try:
                return json.loads(row["response"]["content"])
            except json.JSONDecodeError:
                return None

    return None


def normalize_prediction_graph(pred: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(pred, dict):
        raise ValueError("Prediction must be a dict.")

    nodes = pred.get("nodes")
    edges = pred.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("Prediction must contain list-valued nodes and edges.")

    normalized_nodes = []
    id_map = {}

    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError("Node must be an object.")
        for key in ("id", "label", "token_start", "token_end"):
            if key not in node:
                raise ValueError(f"Missing node key: {key}")

        label = node["label"]
        if label not in ALLOWED_NODE_LABELS:
            raise ValueError(f"Invalid node label: {label}")

        node_id = str(node["id"])
        internal_id = f"n{idx}"
        id_map[node_id] = internal_id

        token_start = int(node["token_start"])
        token_end = int(node["token_end"])
        if token_end <= token_start:
            raise ValueError("Node token span must be non-empty.")

        normalized_nodes.append(
            {
                "node_id": internal_id,
                "label": label,
                "token_start": token_start,
                "token_end": token_end,
            }
        )

    normalized_edges = []
    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError("Edge must be an object.")
        for key in ("source_id", "target_id", "label"):
            if key not in edge:
                raise ValueError(f"Missing edge key: {key}")

        label = edge["label"]
        if label not in ALLOWED_EDGE_LABELS:
            raise ValueError(f"Invalid edge label: {label}")

        src = id_map.get(str(edge["source_id"]))
        dst = id_map.get(str(edge["target_id"]))
        if src is None or dst is None:
            continue

        normalized_edges.append(
            {
                "edge_id": f"e{idx}",
                "source_id": src,
                "target_id": dst,
                "label": label,
            }
        )

    return {"nodes": normalized_nodes, "edges": normalized_edges}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/lamm2018_tap/lamm2018_tap_graph_eval.json"),
    )
    args = parser.parse_args()

    gold_by_id = {}
    with args.gold.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                gold_by_id[row["example_id"]] = row

    pred_by_id = {}
    with args.predictions.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            example_id = row.get("example_id") or row.get("custom_id")
            if example_id is not None:
                pred_by_id[example_id] = row

    n_eval = len(gold_by_id)
    covered = 0
    valid = 0

    total_pred_nodes_non_value = 0
    total_gold_nodes_non_value = 0
    total_node_matches_non_value = 0

    total_pred_triples = 0
    total_gold_triples = 0
    total_triple_matches = 0

    exact_graph_match = 0

    for example_id, gold_row in gold_by_id.items():
        pred_row = pred_by_id.get(example_id)
        if pred_row is None:
            continue

        covered += 1

        pred_obj = parse_prediction(pred_row)
        if pred_obj is None:
            continue

        try:
            pred_graph = normalize_prediction_graph(pred_obj)
        except Exception:
            continue

        valid += 1

        gold_graph = gold_row["label"]["benchmark_graph"]

        gold_nodes, gold_triples = graph_to_nodes_and_triples(gold_graph)
        pred_nodes, pred_triples = graph_to_nodes_and_triples(pred_graph)

        gold_nodes_non_value = [n for n in gold_nodes if n.label != "value"]
        pred_nodes_non_value = [n for n in pred_nodes if n.label != "value"]

        node_matches = greedy_match(pred_nodes_non_value, gold_nodes_non_value, node_overlap_score)
        triple_matches = greedy_match(pred_triples, gold_triples, triple_overlap_score)

        total_pred_nodes_non_value += len(pred_nodes_non_value)
        total_gold_nodes_non_value += len(gold_nodes_non_value)
        total_node_matches_non_value += node_matches

        total_pred_triples += len(pred_triples)
        total_gold_triples += len(gold_triples)
        total_triple_matches += triple_matches

        gold_node_set = {(n.label, n.token_start, n.token_end) for n in gold_nodes}
        pred_node_set = {(n.label, n.token_start, n.token_end) for n in pred_nodes}
        gold_triple_set = {
            (t.src_label, t.src_start, t.src_end, t.edge_label, t.dst_label, t.dst_start, t.dst_end)
            for t in gold_triples
        }
        pred_triple_set = {
            (t.src_label, t.src_start, t.src_end, t.edge_label, t.dst_label, t.dst_start, t.dst_end)
            for t in pred_triples
        }

        if gold_node_set == pred_node_set and gold_triple_set == pred_triple_set:
            exact_graph_match += 1

    report = {
        "task_id": "TA_GRAPH_TAP_LAMM2018_v0",
        "n_gold_examples": len(gold_by_id),
        "coverage_rate": covered / n_eval if n_eval else 0.0,
        "valid_prediction_rate": valid / n_eval if n_eval else 0.0,
        "node_metrics_excluding_value": prf(
            total_node_matches_non_value,
            total_pred_nodes_non_value,
            total_gold_nodes_non_value,
        ),
        "triple_metrics_overlap": prf(
            total_triple_matches,
            total_pred_triples,
            total_gold_triples,
        ),
        "exact_graph_match_rate": exact_graph_match / n_eval if n_eval else 0.0,
        "notes": [
            "Primary local metric is overlap-based triple F1.",
            "Node-only metric excludes value nodes.",
            "This is a local smoke evaluator, not an official-scorer wrapper."
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[DONE] Evaluation complete")
    print(f"[OUT] {args.out}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
