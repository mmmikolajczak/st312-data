from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi, get_hf_file_metadata, hf_hub_download, hf_hub_url
from huggingface_hub import __version__ as huggingface_hub_version


DATASET_ID = "flare_edtsum_public_test_v0"
SOURCE_REPO = "TheFinAI/flare-edtsum"
SOURCE_FILES = ["README.md", "data/test-00000-of-00001-f8ea79e581c9134b.parquet"]
EXPECTED_FIELDS = ["id", "query", "answer", "text"]
EXPECTED_ROWS = 2000
RAW_DIR = Path("data/flare_edtsum_public_test/raw")
PROCESSED_DIR = Path("data/flare_edtsum_public_test/processed")
REPORT_DIR = Path("reports/flare_edtsum_public_test")
HF_CACHE_DIR = Path(".hf_cache")

RAW_README_PATH = RAW_DIR / "README.md"
RAW_PARQUET_PATH = RAW_DIR / "test-00000-of-00001-f8ea79e581c9134b.parquet"
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
DOWNLOAD_META_INTERNAL_PATH = RAW_DIR / "download_meta_internal.json"
PROCESSED_TEST_PATH = PROCESSED_DIR / "test.jsonl"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
RAW_SCHEMA_SUMMARY_PATH = REPORT_DIR / "raw_schema_summary.json"
RIGHTS_STATUS_NOTE = (
    "This module is publicly published in the ST312 artifact store, but public_release_cleared remains false; "
    "upstream access is gated and redistribution / downstream reuse should be treated with caution pending rights review."
)


def configure_hf_cache() -> None:
    cache_root = HF_CACHE_DIR.resolve()
    os.environ.setdefault("HF_HOME", str(cache_root))
    os.environ.setdefault("HF_HUB_CACHE", str((cache_root / "hub").resolve()))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str((cache_root / "hub").resolve()))
    os.environ.setdefault("HF_XET_CACHE", str((cache_root / "xet").resolve()))
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def build_processed_row(source_revision: str, source_path: str, row: dict) -> dict:
    missing = [field for field in EXPECTED_FIELDS if field not in row]
    if missing:
        raise KeyError(f"Missing required fields: {missing}")

    raw_id = str(row["id"])
    raw_query = normalize_text(str(row["query"]))
    raw_answer = normalize_text(str(row["answer"]))
    raw_text = normalize_text(str(row["text"]))

    if not raw_id.strip():
        raise ValueError("Encountered blank upstream id")
    if not raw_query.strip():
        raise ValueError(f"{raw_id}: blank query after normalization")
    if not raw_text.strip():
        raise ValueError(f"{raw_id}: blank text after normalization")

    return {
        "example_id": raw_id,
        "dataset_id": DATASET_ID,
        "split": "test",
        "id": raw_id,
        "query": raw_query,
        "text": raw_text,
        "answer": raw_answer,
        "article_text": raw_text,
        "reference_headline": raw_answer,
        "task_target_type": "headline_generation",
        "source_dataset": SOURCE_REPO,
        "source_format": "gated_parquet_wrapper",
        "source_split": "test",
        "source_revision": source_revision,
        "source_path": source_path,
        "source_fields_present": EXPECTED_FIELDS,
    }


def main() -> None:
    configure_hf_cache()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    who = api.whoami()
    info = api.dataset_info(SOURCE_REPO)
    source_revision = info.sha
    sibling_names = sorted(s.rfilename for s in info.siblings)

    train_dev_candidates = [
        name for name in sibling_names if any(token in name.lower() for token in ["train", "dev", "valid", "validation"])
    ]
    if train_dev_candidates:
        raise RuntimeError(
            f"Unexpected train/dev-like files found in gated source: {train_dev_candidates}. Pause before changing eval-only policy."
        )

    downloaded_paths: dict[str, Path] = {}
    source_file_metadata: dict[str, dict] = {}
    for filename in SOURCE_FILES:
        resolved_url = hf_hub_url(SOURCE_REPO, filename, repo_type="dataset")
        file_metadata = get_hf_file_metadata(resolved_url)
        local_cached = Path(
            hf_hub_download(
                repo_id=SOURCE_REPO,
                repo_type="dataset",
                filename=filename,
                revision=source_revision,
                cache_dir=str(HF_CACHE_DIR),
            )
        )
        dst = RAW_DIR / Path(filename).name
        shutil.copy2(local_cached, dst)
        downloaded_paths[filename] = dst
        source_file_metadata[filename] = {
            "resolved_url": resolved_url,
            "etag": file_metadata.etag,
            "commit_hash": file_metadata.commit_hash,
            "size": file_metadata.size,
            "location": file_metadata.location,
        }

    raw_df = pd.read_parquet(RAW_PARQUET_PATH)
    if len(raw_df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {len(raw_df)}")
    field_names_seen = list(raw_df.columns)
    expected_field_set = set(EXPECTED_FIELDS)
    seen_field_set = set(field_names_seen)
    missing_fields = sorted(expected_field_set - seen_field_set)
    unexpected_fields = sorted(seen_field_set - expected_field_set)
    if missing_fields or unexpected_fields:
        raise ValueError(
            f"Expected required fields {EXPECTED_FIELDS}; missing={missing_fields or None}, unexpected={unexpected_fields or None}, "
            f"observed_order={field_names_seen}"
        )

    rows = raw_df.to_dict(orient="records")
    processed_rows = [build_processed_row(source_revision, RAW_PARQUET_PATH.name, row) for row in rows]

    seen_ids: set[str] = set()
    for row in processed_rows:
        if row["example_id"] in seen_ids:
            raise ValueError(f"Duplicate example_id: {row['example_id']}")
        seen_ids.add(row["example_id"])

    query_contains_text_count = sum(
        1 for row in processed_rows if row["text"] in row["query"]
    )
    query_answer_suffix_count = sum(
        1 for row in processed_rows if row["query"].rstrip().endswith("Answer:")
    )
    blank_reference_count = sum(1 for row in processed_rows if not row["reference_headline"].strip())

    raw_schema_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": source_revision,
        "container_format": "parquet",
        "row_count": len(processed_rows),
        "top_level_keys": field_names_seen,
        "field_types": {field: sorted({type(row[field]).__name__ for row in rows}) for field in field_names_seen},
        "query_contains_text_count": query_contains_text_count,
        "query_answer_suffix_count": query_answer_suffix_count,
        "duplicate_id_count": int(raw_df["id"].duplicated().sum()),
        "duplicate_full_row_count": int(raw_df.duplicated().sum()),
        "blank_reference_count": blank_reference_count,
        "blank_reference_policy": "preserve_and_score_as_released",
        "max_lengths": {
            "id": int(raw_df["id"].map(len).max()),
            "query": int(raw_df["query"].map(len).max()),
            "answer": int(raw_df["answer"].map(len).max()),
            "text": int(raw_df["text"].map(len).max()),
        },
        "sample_row": {key: rows[0][key] for key in field_names_seen},
        "notes": [
            "The gated wrapper exposes exactly id, query, answer, and text.",
            "The prompt-prefixed query field embeds the article text and usually terminates with an Answer: cue.",
            "The canonical processed artifact preserves those fields verbatim after minimal line-ending and trailing-whitespace normalization.",
            "ST312 adds article_text and reference_headline aliases to make the headline-generation semantics explicit.",
            "At least one upstream row has a blank reference answer; it is preserved rather than dropped to avoid silent row loss.",
            "No train or validation split is fabricated."
        ],
    }
    write_json(RAW_SCHEMA_SUMMARY_PATH, raw_schema_summary)
    write_jsonl(PROCESSED_TEST_PATH, processed_rows)

    download_meta = {
        "source_repo": SOURCE_REPO,
        "gated_access": True,
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": source_revision,
        "visible_upstream_file_list": sibling_names,
        "visible_upstream_split_metadata": info.cardData.get("dataset_info", {}).get("splits", []),
        "visible_upstream_features": info.cardData.get("dataset_info", {}).get("features", []),
        "download_method": "huggingface_hub_authenticated_download",
        "source_file_metadata": {
            name: {
                "resolved_url": metadata["resolved_url"],
                "etag": metadata["etag"],
                "commit_hash": metadata["commit_hash"],
                "size": metadata["size"],
            }
            for name, metadata in source_file_metadata.items()
        },
        "local_file_sizes_bytes": {name: path.stat().st_size for name, path in downloaded_paths.items()},
        "sha256_by_file": {name: sha256_file(path) for name, path in downloaded_paths.items()},
        "notes": [
            "Access required agreeing to contact sharing and non-commercial-use-only conditions.",
            "The raw parquet is treated as immutable after download.",
            RIGHTS_STATUS_NOTE
        ],
    }
    write_json(DOWNLOAD_META_PATH, download_meta)

    download_meta_internal = {
        **download_meta,
        "active_hf_account": who["name"],
        "local_raw_paths": {name: str(path) for name, path in downloaded_paths.items()},
        "source_file_metadata": source_file_metadata,
        "downloader_environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "huggingface_hub": huggingface_hub_version,
        },
        "notes": [
            "Internal local-only metadata artifact for operational debugging.",
            *download_meta["notes"],
        ],
    }
    write_json(DOWNLOAD_META_INTERNAL_PATH, download_meta_internal)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": source_revision,
        "split_policy": "public_test_only_eval_wrapper",
        "row_count": len(processed_rows),
        "published_splits": ["test"],
        "processed_file": str(PROCESSED_TEST_PATH),
        "raw_schema_report": str(RAW_SCHEMA_SUMMARY_PATH),
        "query_contains_text_count": query_contains_text_count,
        "query_answer_suffix_count": query_answer_suffix_count,
        "blank_reference_count": blank_reference_count,
        "blank_reference_policy": "preserve_and_score_as_released",
        "max_lengths": raw_schema_summary["max_lengths"],
        "notes": [
            "The module preserves upstream wrapper fields and adds canonical headline-generation aliases.",
            "The task target is headline generation over financial news article text.",
            "Blank upstream reference answers are preserved verbatim and surfaced in metadata rather than dropped.",
            "No train/dev split is fabricated.",
            RIGHTS_STATUS_NOTE,
        ],
    }
    write_json(INGEST_SUMMARY_PATH, ingest_summary)

    print(f"[DONE] Ingested {DATASET_ID}")
    print(f"[INFO] source_revision={source_revision}")
    print(f"[INFO] row_count={len(processed_rows)}")
    print(f"[OUT]  {PROCESSED_TEST_PATH}")
    print(f"[OUT]  {INGEST_SUMMARY_PATH}")
    print(f"[OUT]  {RAW_SCHEMA_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
