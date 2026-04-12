from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset


DATASET_ID = "TheFinAI/flare-mlesg"
DATASET_CONFIG = "default"
DATASET_SPLIT = "test"
EXPECTED_FIELDS = ["id", "query", "answer", "text", "choices", "gold"]
EXPECTED_ROWS = 300
EXPECTED_CHOICES = 33

RAW_DIR = Path("data/flare_mlesg/raw")
PROCESSED_DIR = Path("data/flare_mlesg/processed")
PROCESSED_JSONL = PROCESSED_DIR / "flare_mlesg_en_public_test.jsonl"
INGEST_META = RAW_DIR / "flare_mlesg_en_public_test_ingest_meta.json"


def label_inventory_sha256(labels: list[str]) -> str:
    payload = json.dumps(labels, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ds = load_dataset(DATASET_ID, DATASET_CONFIG, split=DATASET_SPLIT)
    if len(ds) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {len(ds)}")

    field_names_seen = list(ds.column_names)
    if field_names_seen != EXPECTED_FIELDS:
        raise ValueError(f"Expected field order {EXPECTED_FIELDS}, found {field_names_seen}")

    canonical_inventory: list[str] | None = None
    distinct_choice_inventories: set[tuple[str, ...]] = set()
    gold_min: int | None = None
    gold_max: int | None = None

    with PROCESSED_JSONL.open("w", encoding="utf-8") as out_f:
        for row in ds:
            row_dict = dict(row)
            if list(row_dict.keys()) != EXPECTED_FIELDS:
                raise ValueError(f"Unexpected row fields for {row_dict.get('id')}: {list(row_dict.keys())}")

            choices = list(row["choices"])
            if len(choices) != EXPECTED_CHOICES:
                raise ValueError(f"{row['id']}: expected {EXPECTED_CHOICES} choices, found {len(choices)}")

            gold = int(row["gold"])
            if gold < 0 or gold >= len(choices):
                raise ValueError(f"{row['id']}: gold index out of range: {gold}")

            answer = str(row["answer"])
            if answer != choices[gold]:
                raise ValueError(f"{row['id']}: answer != choices[gold]")

            inventory_tuple = tuple(choices)
            distinct_choice_inventories.add(inventory_tuple)
            if canonical_inventory is None:
                canonical_inventory = choices
            elif choices != canonical_inventory:
                raise ValueError(f"{row['id']}: observed a non-canonical choice inventory")

            gold_min = gold if gold_min is None else min(gold_min, gold)
            gold_max = gold if gold_max is None else max(gold_max, gold)

            canonical_row = {
                "example_id": str(row["id"]),
                "data": {
                    "text": str(row["text"])
                },
                "label": {
                    "issue": answer
                },
                "metadata": {
                    "source_dataset": DATASET_ID,
                    "language": "en",
                    "upstream_id": str(row["id"]),
                    "upstream_query": str(row["query"]),
                    "upstream_answer": answer,
                    "upstream_gold": gold,
                    "upstream_choices": choices,
                    "wrapper_type": "public_eval_only_finben_mirror"
                }
            }
            out_f.write(json.dumps(canonical_row, ensure_ascii=False) + "\n")

    if canonical_inventory is None:
        raise ValueError("No rows ingested")

    meta = {
        "dataset_id": "flare_mlesg_en_public_test_v0",
        "upstream_dataset_id": DATASET_ID,
        "upstream_config": DATASET_CONFIG,
        "upstream_split": DATASET_SPLIT,
        "row_count": EXPECTED_ROWS,
        "field_names_seen": field_names_seen,
        "canonical_label_inventory": canonical_inventory,
        "distinct_choice_inventory_count": len(distinct_choice_inventories),
        "gold_min": gold_min,
        "gold_max": gold_max,
        "label_inventory_sha256": label_inventory_sha256(canonical_inventory),
        "wrapper_label_count": len(canonical_inventory),
        "paper_issue_count_note": "The public wrapper exposes 33 labels, while the original ML-ESG paper describes a 35-issue task.",
        "processed_jsonl": str(PROCESSED_JSONL),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script_path": str(Path(__file__)),
        "notes": [
            "Eval-only public wrapper ingestion.",
            "No train or validation split is fabricated.",
            "The wrapper-level 33-label inventory is treated as canonical for this module."
        ]
    }
    INGEST_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("[DONE] Ingest complete")
    print(f"[PROCESSED] {PROCESSED_JSONL}")
    print(f"[META] {INGEST_META}")
    print(f"[N] {EXPECTED_ROWS}")
    print(f"[LABELS] {len(canonical_inventory)}")
    print(f"[LABEL_INVENTORY_SHA256] {meta['label_inventory_sha256']}")


if __name__ == "__main__":
    main()
