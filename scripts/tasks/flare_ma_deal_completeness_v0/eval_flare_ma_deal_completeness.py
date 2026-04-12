from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef


ALLOWED = {"rumour", "complete"}


def normalize_label(value: str) -> str:
    return str(value).strip().lower()


def extract_label(obj) -> str | None:
    if obj is None:
        return None

    if isinstance(obj, str):
        text = obj.strip()
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            return extract_label(parsed)

        norm = normalize_label(text)
        return norm if norm in ALLOWED else None

    if isinstance(obj, dict):
        for key in ["label", "prediction", "response", "output_text", "completion"]:
            if key in obj:
                return extract_label(obj[key])

    return None


def load_gold(path: Path) -> dict[str, str]:
    gold = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            gold[ex["example_id"]] = normalize_label(ex["label"]["label"])
    return gold


def load_predictions(path: Path) -> dict[str, str | None]:
    preds = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            preds[row["example_id"]] = extract_label(row)
    return preds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gold = load_gold(args.gold)
    preds = load_predictions(args.predictions)

    y_true: list[str] = []
    y_pred: list[str] = []

    missing = 0
    invalid = 0

    for example_id, gold_label in gold.items():
        pred = preds.get(example_id)
        if pred is None:
            missing += 1
            continue
        if pred not in ALLOWED:
            invalid += 1
            continue
        y_true.append(gold_label)
        y_pred.append(pred)

    coverage_rate = len(y_true) / len(gold) if gold else 0.0
    format_valid_rate = len(y_true) / len(preds) if preds else 0.0

    report = {
        "task_id": "TA_MA_COMPLETENESS_FLARE_v0",
        "n_gold_examples": len(gold),
        "n_predictions_rows": len(preds),
        "n_scored_examples": len(y_true),
        "coverage_rate": coverage_rate,
        "format_valid_rate": format_valid_rate,
        "missing_predictions": missing,
        "invalid_predictions": invalid,
        "metrics": {},
        "notes": [
            "Eval-only benchmark wrapper over public TheFinAI/flare-ma test split.",
            "Primary metrics are accuracy, macro F1, and MCC.",
            "Binary F1 is also reported with 'complete' as the positive label.",
        ],
    }

    if y_true:
        report["metrics"] = {
            "accuracy": accuracy_score(y_true, y_pred),
            "macro_f1": f1_score(y_true, y_pred, average="macro"),
            "binary_f1_complete": f1_score(y_true, y_pred, pos_label="complete"),
            "mcc": matthews_corrcoef(y_true, y_pred),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("[DONE] Evaluation complete")
    print(f"[OUT] {args.out}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
