from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from datasets import load_dataset


DATASET_ID = "TheFinAI/flare-ma"
RAW_DIR = Path("data/flare_ma/raw")
PROCESSED_DIR = Path("data/flare_ma/processed")
RAW_JSONL = RAW_DIR / "flare_ma_hf_test_raw.jsonl"
PROCESSED_JSONL = PROCESSED_DIR / "flare_ma_public_test.jsonl"
INGEST_META = RAW_DIR / "flare_ma_ingest_meta.json"

ALLOWED_LABELS = {"rumour", "complete"}


def normalize_label(value: str) -> str:
    return str(value).strip().lower()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ds = load_dataset(DATASET_ID, split="test")

    label_counts = Counter()
    warnings: list[str] = []
    n_rows = 0

    with RAW_JSONL.open("w", encoding="utf-8") as raw_f, PROCESSED_JSONL.open("w", encoding="utf-8") as out_f:
        for idx, row in enumerate(ds):
            raw_f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

            source_id = str(row["id"])
            choices = [normalize_label(x) for x in row["choices"]]
            gold_index = int(row["gold"])
            gold_from_index = choices[gold_index]
            answer_norm = normalize_label(row["answer"])

            if answer_norm and answer_norm != gold_from_index:
                warnings.append(
                    f"{source_id}: answer='{answer_norm}' != choices[gold]='{gold_from_index}'; using choices[gold]."
                )

            if gold_from_index not in ALLOWED_LABELS:
                raise ValueError(f"{source_id}: unexpected gold label '{gold_from_index}'")

            example = {
                "example_id": f"flare_ma_test_{idx + 1:04d}",
                "source_id": source_id,
                "split": "test",
                "data": {
                    "text": row["text"],
                    "raw_query": row["query"],
                    "choices": choices,
                },
                "label": {
                    "label": gold_from_index,
                    "gold_index": gold_index,
                },
                "meta": {
                    "source_dataset": DATASET_ID,
                    "eval_only": True,
                    "public_artifact_only": True,
                    "artifact_split": "test",
                },
            }

            out_f.write(json.dumps(example, ensure_ascii=False) + "\n")
            label_counts[gold_from_index] += 1
            n_rows += 1

    meta = {
        "dataset_id": "flare_ma_public_test_v0",
        "source_dataset": DATASET_ID,
        "source_split": "test",
        "n_rows": n_rows,
        "raw_jsonl": str(RAW_JSONL),
        "processed_jsonl": str(PROCESSED_JSONL),
        "label_counts": dict(label_counts),
        "warnings": warnings,
        "notes": [
            "Public artifact is treated as eval-only benchmark input.",
            "No train/validation split is fabricated.",
            "Canonical label is choices[gold], not free-form answer text.",
        ],
    }

    INGEST_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("[DONE] Ingest complete")
    print(f"[RAW] {RAW_JSONL}")
    print(f"[PROCESSED] {PROCESSED_JSONL}")
    print(f"[META] {INGEST_META}")
    print(f"[N] {n_rows}")
    print(f"[LABEL_COUNTS] {dict(label_counts)}")
    if warnings:
        print("[WARNINGS]")
        for w in warnings[:10]:
            print(f" - {w}")
        if len(warnings) > 10:
            print(f" - ... ({len(warnings) - 10} more)")


if __name__ == "__main__":
    main()
