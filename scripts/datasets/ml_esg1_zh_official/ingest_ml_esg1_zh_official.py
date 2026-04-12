from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from audit_dynamic_esg_release import build_ingest_audit  # noqa: E402
from download_dynamic_esg_release import (  # noqa: E402
    SOURCE_REPO,
    download_release_files,
    write_download_meta,
)
from validate_dynamic_esg_release import validate_and_build_rows  # noqa: E402


DATASET_ID = "ml_esg1_zh_official_v0"
RAW_DIR = Path("data/ml_esg1_zh_official/raw")
PROCESSED_DIR = Path("data/ml_esg1_zh_official/processed")
REPORTS_DIR = Path("reports/ml_esg1_zh_official")
SOURCE_PATHS = [
    "data/ML-ESG-1_Chinese/Train.json",
    "data/ML-ESG-1_Chinese/Dev.json",
    "data/ML-ESG-1_Chinese/Test.json",
]
SPLIT_TO_SOURCE = {
    "train": "data/ML-ESG-1_Chinese/Train.json",
    "dev": "data/ML-ESG-1_Chinese/Dev.json",
    "test": "data/ML-ESG-1_Chinese/Test.json",
}
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "label_inventory.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
AUDIT_PATH = REPORTS_DIR / "ingest_audit.json"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    download_meta, copied_files = download_release_files(RAW_DIR, SOURCE_PATHS)
    write_download_meta(DOWNLOAD_META_PATH, download_meta)

    processed_by_split = {}
    validation_summary_by_split = {}
    for split, source_path in SPLIT_TO_SOURCE.items():
        raw_path = copied_files[source_path]
        raw_rows = json.loads(raw_path.read_text(encoding="utf-8"))
        processed_rows, validation_summary = validate_and_build_rows(
            dataset_id=DATASET_ID,
            split=split,
            source_repo=SOURCE_REPO,
            source_commit=download_meta["source_commit"],
            source_path=source_path,
            rows=raw_rows,
        )
        processed_by_split[split] = processed_rows
        validation_summary_by_split[split] = validation_summary
        write_jsonl(PROCESSED_DIR / f"{split}.jsonl", processed_rows)

    audit = build_ingest_audit(processed_by_split, validation_summary_by_split)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    label_inventory = audit["label_inventory"]
    LABEL_INVENTORY_PATH.write_text(
        json.dumps(
            {
                "dataset_id": DATASET_ID,
                "source_repo": SOURCE_REPO,
                "source_commit": download_meta["source_commit"],
                "labels": label_inventory,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_commit": download_meta["source_commit"],
        "splits": audit["split_counts"],
        "label_inventory_size": audit["label_inventory_size"],
        "label_inventory": label_inventory,
        "headline_only": True,
        "official_split_preserved": True,
        "source_paths": SOURCE_PATHS,
        "download_meta_file": str(DOWNLOAD_META_PATH),
        "ingest_audit_file": str(AUDIT_PATH),
    }
    INGEST_SUMMARY_PATH.write_text(json.dumps(ingest_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("[DONE] ML-ESG-1 Chinese official ingest complete")
    print(f"[SOURCE_COMMIT] {download_meta['source_commit']}")
    print(f"[TRAIN] data/ml_esg1_zh_official/processed/train.jsonl ({len(processed_by_split['train'])} rows)")
    print(f"[DEV]   data/ml_esg1_zh_official/processed/dev.jsonl ({len(processed_by_split['dev'])} rows)")
    print(f"[TEST]  data/ml_esg1_zh_official/processed/test.jsonl ({len(processed_by_split['test'])} rows)")
    print(f"[LABELS] {audit['label_inventory_size']}")
    print(f"[AUDIT] {AUDIT_PATH}")


if __name__ == "__main__":
    main()
