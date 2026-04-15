from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


DATASET_ID = "regulations_public_test_v0"
SOURCE_REPO = "TheFinAI/regulations"
RAW_DIR = Path("data/regulations_public_test/raw")
PROCESSED_DIR = Path("data/regulations_public_test/processed")
REPORT_DIR = Path("reports/regulations_public_test")

DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
RAW_SCHEMA_SUMMARY_PATH = REPORT_DIR / "raw_schema_summary.json"

EXPECTED_VISIBLE_FILES = ["README.md", "test_regulations.json"]
QUERY_PREFIX = "Please answer following questions. Question: "
HF_CACHE_DIR = Path("/tmp/hf_cache")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_processed_row(source_revision: str, source_path: str, row: dict) -> dict:
    required = ["id", "query", "answer", "text"]
    missing = [key for key in required if key not in row]
    if missing:
        raise KeyError(f"Missing required keys: {missing}")

    if not all(isinstance(row[key], str) and row[key].strip() for key in required):
        raise ValueError("All required fields must be non-empty strings")

    question = row["text"].strip()
    source_query = row["query"].strip()

    return {
        "example_id": row["id"].strip(),
        "dataset_id": DATASET_ID,
        "split": "test",
        "question": question,
        "reference_answer": row["answer"].strip(),
        "context": None,
        "source_title": None,
        "source_document": None,
        "source_section": None,
        "jurisdiction": None,
        "regulation_family": "EMIR" if "EMIR" in source_query or "EMIR" in question or "EMIR" in row["answer"] else None,
        "source_query": source_query,
        "source_repo": SOURCE_REPO,
        "source_revision": source_revision,
        "source_path": source_path,
        "source_fields_present": sorted(row.keys()),
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    who = api.whoami()
    info = api.repo_info(SOURCE_REPO, repo_type="dataset")
    source_revision = info.sha
    sibling_names = sorted(s.rfilename for s in info.siblings)

    train_dev_candidates = [name for name in sibling_names if any(token in name.lower() for token in ["train", "dev", "valid", "validation"])]
    if train_dev_candidates:
        raise RuntimeError(
            f"Unexpected train/dev-like files found in gated source: {train_dev_candidates}. Pause scope before changing eval-only policy."
        )

    downloaded = {}
    for filename in EXPECTED_VISIBLE_FILES:
        local = Path(
            hf_hub_download(
                repo_id=SOURCE_REPO,
                repo_type="dataset",
                filename=filename,
                cache_dir=str(HF_CACHE_DIR),
            )
        )
        dst = RAW_DIR / filename
        shutil.copy2(local, dst)
        downloaded[filename] = dst

    rows = load_jsonl(downloaded["test_regulations.json"])
    processed_rows = [build_processed_row(source_revision, "test_regulations.json", row) for row in rows]

    seen_ids = set()
    for row in processed_rows:
        if row["example_id"] in seen_ids:
            raise ValueError(f"Duplicate example_id: {row['example_id']}")
        seen_ids.add(row["example_id"])

    query_prefix_count = sum(1 for row in rows if row["query"].startswith(QUERY_PREFIX))
    extracted_question_match_count = sum(
        1
        for row in rows
        if row["query"].startswith(QUERY_PREFIX) and row["query"][len(QUERY_PREFIX) :].strip() == row["text"].strip()
    )

    raw_schema_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": source_revision,
        "container_format": "jsonl",
        "row_count": len(rows),
        "top_level_keys": sorted({key for row in rows for key in row.keys()}),
        "field_types": {key: sorted({type(row[key]).__name__ for row in rows}) for key in sorted({key for row in rows for key in row.keys()})},
        "query_prefix_count": query_prefix_count,
        "extracted_question_match_count": extracted_question_match_count,
        "sample_row": rows[0],
        "notes": [
            "The gated wrapper stores one JSON object per line rather than a JSON array.",
            "The wrapper exposes only id, query, answer, and text.",
            "No explicit context/source-document fields are present in the released wrapper.",
            "The canonical question field uses text; the prompt-prefixed query field is preserved as source_query metadata.",
        ],
    }
    write_json(RAW_SCHEMA_SUMMARY_PATH, raw_schema_summary)

    write_jsonl(PROCESSED_DIR / "test.jsonl", processed_rows)

    download_meta = {
        "source_repo": SOURCE_REPO,
        "gated_access": True,
        "active_hf_account": who["name"],
        "source_revision": source_revision,
        "source_paths": EXPECTED_VISIBLE_FILES,
        "source_display_urls": {
            name: f"https://huggingface.co/datasets/{SOURCE_REPO}/blob/{source_revision}/{name}"
            for name in EXPECTED_VISIBLE_FILES
        },
        "source_raw_urls": {
            name: f"https://huggingface.co/datasets/{SOURCE_REPO}/resolve/{source_revision}/{name}"
            for name in EXPECTED_VISIBLE_FILES
        },
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": {name: path.stat().st_size for name, path in downloaded.items()},
        "sha256_by_file": {name: sha256_file(path) for name, path in downloaded.items()},
        "download_method": "huggingface_hub_authenticated_download",
        "notes": [
            "The source dataset is gated and required authenticated access.",
            "No public train/dev files were found in the visible gated file tree at the pinned revision.",
            "This module is treated as eval-only test-only wrapper input.",
        ],
    }
    write_json(DOWNLOAD_META_PATH, download_meta)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": source_revision,
        "split_policy": "eval_only_test_only",
        "row_count": len(processed_rows),
        "published_splits": ["test"],
        "omitted_artifacts": ["label_inventory.json"],
        "omitted_artifacts_reason": "No meaningful categorical label inventory is present in the raw long-form QA wrapper.",
        "raw_schema_report": str(RAW_SCHEMA_SUMMARY_PATH),
        "query_prefix_count": query_prefix_count,
        "extracted_question_match_count": extracted_question_match_count,
    }
    write_json(INGEST_SUMMARY_PATH, ingest_summary)

    print(f"[DONE] Ingested {DATASET_ID}")
    print(f"[INFO] source_revision={source_revision}")
    print(f"[INFO] row_count={len(processed_rows)}")
    print(f"[OUT]  {PROCESSED_DIR / 'test.jsonl'}")
    print(f"[OUT]  {INGEST_SUMMARY_PATH}")
    print(f"[OUT]  {RAW_SCHEMA_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
