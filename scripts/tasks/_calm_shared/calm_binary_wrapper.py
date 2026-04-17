from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_task_spec(task_spec_path: str | Path) -> dict:
    return json.loads(Path(task_spec_path).read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def allowed_labels(task_spec: dict) -> list[str]:
    return list(task_spec["output_schema"]["value_schema"]["label"]["enum"])


def extract_output_text(row: dict) -> str | None:
    for key in ["output_text", "completion", "response_text", "text"]:
        value = row.get(key)
        if isinstance(value, str):
            return value
    return None


def extract_json_object(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def inspect_prediction(text: str, labels: list[str]) -> dict:
    obj = extract_json_object(text)
    info = {
        "valid_json_object": isinstance(obj, dict),
        "valid_label_key": False,
        "nonempty_label": False,
        "label": None,
        "accepted_key": None,
    }
    if not isinstance(obj, dict):
        return info
    for key in ["label", "answer"]:
        value = obj.get(key)
        if isinstance(value, str):
            normalized = value.strip().lower()
            info["accepted_key"] = key
            if normalized:
                info["nonempty_label"] = True
            if normalized in labels and len(obj.keys()) == 1:
                info["valid_label_key"] = True
                info["label"] = normalized
                return info
    return info


def parse_prediction(text: str, labels: list[str]) -> dict | None:
    inspected = inspect_prediction(text, labels)
    if not inspected["valid_label_key"]:
        return None
    return {"label": inspected["label"], "_format_valid": True}


def format_reward(text: str, labels: list[str]) -> float:
    return 1.0 if inspect_prediction(text, labels)["valid_json_object"] else 0.0


def label_valid_reward(text: str, labels: list[str]) -> float:
    return 1.0 if inspect_prediction(text, labels)["valid_label_key"] else 0.0


def exact_match_reward(text: str, gold_label: str, labels: list[str]) -> float:
    parsed = parse_prediction(text, labels)
    if parsed is None:
        return 0.0
    return 1.0 if parsed["label"] == gold_label.strip().lower() else 0.0


def malformed_output_penalty(text: str, labels: list[str]) -> float:
    return 1.0 if parse_prediction(text, labels) is None else 0.0


def total_reward(text: str, gold_label: str, labels: list[str]) -> float:
    return (
        0.2 * format_reward(text, labels)
        + 0.2 * label_valid_reward(text, labels)
        + 0.6 * exact_match_reward(text, gold_label, labels)
    )


def render_user_prompt(row: dict, task_spec: dict) -> str:
    template = task_spec["prompt_template"]["user"]
    return (
        template.replace("{{feature_text}}", row["feature_text"])
        .replace("{{raw_query}}", row.get("query", ""))
        .replace("{{label_example}}", allowed_labels(task_spec)[0])
    )


def build_requests(task_spec_path: str | Path, split: str, out: str | Path | None = None, limit: int | None = None, include_gold: bool = False) -> Path:
    task_spec = load_task_spec(task_spec_path)
    split_path = Path(task_spec["dataset"][f"{split}_file"])
    task_folder = Path(task_spec_path).parent
    out_path = Path(out) if out else task_folder / "requests" / f"{split}_requests.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out_path.open("w", encoding="utf-8") as handle:
        for row in load_jsonl(split_path):
            if limit is not None and written >= limit:
                break
            request = {
                "example_id": row["example_id"],
                "task_id": task_spec["task_id"],
                "messages": [
                    {"role": "system", "content": task_spec["prompt_template"]["system"]},
                    {"role": "user", "content": render_user_prompt(row, task_spec)},
                ],
            }
            if include_gold:
                request["gold_label_text"] = row["label_normalized"]
            handle.write(json.dumps(request, ensure_ascii=False) + "\n")
            written += 1
    print(f"[DONE] Wrote {written} request rows")
    print(f"[OUT]  {out_path}")
    print(f"[INFO] Source split: {split_path}")
    return out_path


def compute_accuracy(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    return sum(int(g == p) for g, p in zip(y_true, y_pred)) / len(y_true)


def compute_macro_f1(y_true: list[int], y_pred: list[int], label_ids: list[int]) -> float:
    if not y_true:
        return 0.0
    f1s = []
    for label in label_ids:
        tp = sum(1 for g, p in zip(y_true, y_pred) if g == label and p == label)
        fp = sum(1 for g, p in zip(y_true, y_pred) if g != label and p == label)
        fn = sum(1 for g, p in zip(y_true, y_pred) if g == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(label_ids)


def compute_mcc(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    tp = sum(1 for g, p in zip(y_true, y_pred) if g == 1 and p == 1)
    tn = sum(1 for g, p in zip(y_true, y_pred) if g == 0 and p == 0)
    fp = sum(1 for g, p in zip(y_true, y_pred) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(y_true, y_pred) if g == 1 and p == 0)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denom == 0:
        return 0.0
    return (tp * tn - fp * fn) / denom


def per_class_metrics(y_true: list[int], y_pred: list[int], label_names: list[str]) -> dict:
    metrics = {}
    for label_id, label_name in enumerate(label_names):
        tp = sum(1 for g, p in zip(y_true, y_pred) if g == label_id and p == label_id)
        fp = sum(1 for g, p in zip(y_true, y_pred) if g != label_id and p == label_id)
        fn = sum(1 for g, p in zip(y_true, y_pred) if g == label_id and p != label_id)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        support = sum(1 for g in y_true if g == label_id)
        metrics[label_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    return metrics


def load_predictions(path: Path, expected_ids: set[str], labels: list[str]) -> tuple[dict[str, dict], dict]:
    pred_by_id: dict[str, dict] = {}
    duplicate_example_ids: set[str] = set()
    unknown_example_ids: set[str] = set()
    diagnostics = {
        "completion_rows_read": 0,
        "rows_missing_example_id": 0,
        "rows_missing_completion_text": 0,
        "duplicate_prediction_rows": 0,
        "duplicate_example_ids": [],
        "unknown_example_id_rows": 0,
        "unknown_example_ids": [],
        "duplicate_policy": "first_completion_wins_reported_duplicate",
    }
    for row in load_jsonl(path):
        diagnostics["completion_rows_read"] += 1
        example_id = row.get("example_id")
        output_text = extract_output_text(row)
        if not isinstance(example_id, str) or not example_id.strip():
            diagnostics["rows_missing_example_id"] += 1
            continue
        example_id = example_id.strip()
        if not isinstance(output_text, str) or not output_text.strip():
            diagnostics["rows_missing_completion_text"] += 1
            continue
        if example_id not in expected_ids:
            diagnostics["unknown_example_id_rows"] += 1
            unknown_example_ids.add(example_id)
            continue
        if example_id in pred_by_id:
            diagnostics["duplicate_prediction_rows"] += 1
            duplicate_example_ids.add(example_id)
            continue
        pred_by_id[example_id] = {
            "output_text": output_text,
            "inspection": inspect_prediction(output_text, labels),
        }
    diagnostics["duplicate_example_ids"] = sorted(duplicate_example_ids)
    diagnostics["unknown_example_ids"] = sorted(unknown_example_ids)
    return pred_by_id, diagnostics


def build_sanity_predictions(split_path: Path, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in load_jsonl(split_path):
            handle.write(
                json.dumps(
                    {"example_id": row["example_id"], "output_text": json.dumps({"label": row["label_normalized"]}, ensure_ascii=False)},
                    ensure_ascii=False,
                )
                + "\n"
            )
    return out_path


def evaluate(task_spec_path: str | Path, split: str, completions_path: Path, report_out: Path) -> dict:
    task_spec = load_task_spec(task_spec_path)
    labels = allowed_labels(task_spec)
    split_path = Path(task_spec["dataset"][f"{split}_file"])
    split_rows = list(load_jsonl(split_path))
    expected_ids = {row["example_id"] for row in split_rows}
    pred_by_id, diagnostics = load_predictions(completions_path, expected_ids, labels)

    rows_with_completion_text = 0
    rows_with_valid_json_object = 0
    rows_with_valid_label_key = 0
    rows_with_nonempty_label = 0
    y_true: list[int] = []
    y_pred: list[int] = []
    class_counts = {label: 0 for label in labels}
    confusion = {f"actual_{g}_pred_{p}": 0 for g in labels for p in labels}

    for row in split_rows:
        gold_label = row["label_normalized"]
        gold_id = row["label_id"]
        class_counts[gold_label] += 1
        pred = pred_by_id.get(row["example_id"])
        if pred is None:
            continue
        rows_with_completion_text += 1
        inspection = pred["inspection"]
        if inspection["valid_json_object"]:
            rows_with_valid_json_object += 1
        if inspection["nonempty_label"]:
            rows_with_nonempty_label += 1
        if not inspection["valid_label_key"]:
            continue
        rows_with_valid_label_key += 1
        pred_label = inspection["label"]
        pred_id = labels.index(pred_label)
        y_true.append(gold_id)
        y_pred.append(pred_id)
        confusion[f"actual_{gold_label}_pred_{pred_label}"] += 1

    report = {
        "task_id": task_spec["task_id"],
        "split": split,
        "variant": task_spec.get("default_eval_variant", "calm_family_default"),
        "split_file": str(split_path),
        "completions_file": str(completions_path),
        "total_examples": len(split_rows),
        "scored_examples": len(y_true),
        "completion_coverage": rows_with_completion_text / len(split_rows) if split_rows else 0.0,
        "format_valid_rate": rows_with_valid_label_key / len(split_rows) if split_rows else 0.0,
        "nonempty_label_rate": rows_with_nonempty_label / len(split_rows) if split_rows else 0.0,
        "rows_with_completion_text": rows_with_completion_text,
        "rows_with_valid_json_object": rows_with_valid_json_object,
        "rows_with_valid_label_key": rows_with_valid_label_key,
        "rows_with_nonempty_label": rows_with_nonempty_label,
        "accuracy": compute_accuracy(y_true, y_pred),
        "macro_f1": compute_macro_f1(y_true, y_pred, list(range(len(labels)))),
        "mcc": compute_mcc(y_true, y_pred),
        "class_counts": class_counts,
        "confusion_matrix": confusion,
        "per_class_metrics": per_class_metrics(y_true, y_pred, labels),
        **diagnostics,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def reward_cli(task_spec_path: str | Path, smoke_test: bool) -> None:
    task_spec = load_task_spec(task_spec_path)
    labels = allowed_labels(task_spec)
    if smoke_test:
        cases = [
            (json.dumps({"label": labels[0]}), labels[0]),
            (json.dumps({"label": labels[-1]}), labels[-1]),
            (json.dumps({"answer": labels[0]}), labels[0]),
            ('{"label":"invalid"}', labels[0]),
            ("not json", labels[0]),
        ]
        report = {"status": "ok", "task_id": task_spec["task_id"], "cases": []}
        for text, gold in cases:
            report["cases"].append(
                {
                    "input": text,
                    "gold": gold,
                    "parsed": parse_prediction(text, labels),
                    "inspected": inspect_prediction(text, labels),
                    "format_reward": format_reward(text, labels),
                    "label_valid_reward": label_valid_reward(text, labels),
                    "exact_match_reward": exact_match_reward(text, gold, labels),
                    "malformed_output_penalty": malformed_output_penalty(text, labels),
                    "total_reward": total_reward(text, gold, labels),
                }
            )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    raise SystemExit("Use --smoke-test for local parser/reward sanity checks.")


def reward_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-test", action="store_true")
    return ap


def eval_argparser(available_splits: list[str]) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=available_splits, default="test")
    ap.add_argument("--completions", default=None)
    ap.add_argument("--report-out", default=None)
    ap.add_argument("--sanity-gold", action="store_true")
    return ap
