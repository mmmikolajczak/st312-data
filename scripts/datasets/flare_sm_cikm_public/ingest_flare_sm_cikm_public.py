from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HF_HOME_DIR = Path("/tmp/hfhome_cikm_wrapper")
HF_CACHE_DIR = HF_HOME_DIR / "hub"
os.environ.setdefault("HF_HOME", str(HF_HOME_DIR))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(HF_CACHE_DIR))
os.environ.setdefault("HF_HUB_CACHE", str(HF_CACHE_DIR))
os.environ.setdefault("HF_XET_CACHE", str(HF_HOME_DIR / "xet"))
os.environ.setdefault("XDG_CACHE_HOME", str(HF_HOME_DIR / "xdg"))

from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download


DATASET_ID = "flare_sm_cikm_public_v0"
SOURCE_REPO = "TheFinAI/flare-sm-cikm"
SOURCE_MIRROR = "ChanceFocus/flare-sm-cikm"
SOURCE_REVISION = "af627b4405e69e298ec45505c91dc17395be712b"
RAW_DIR = Path("data/flare_sm_cikm_public/raw")
PROCESSED_DIR = Path("data/flare_sm_cikm_public/processed")
REPORT_DIR = Path("reports/flare_sm_cikm_public")

RAW_SCHEMA_SUMMARY_PATH = REPORT_DIR / "raw_schema_summary.json"
INGEST_AUDIT_PATH = REPORT_DIR / "ingest_audit.json"
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "label_inventory.json"

SOURCE_FILES = {
    "README.md": "README.md",
    "train_parquet": "data/train-00000-of-00001-f71a7dda3fae0889.parquet",
    "valid_parquet": "data/valid-00000-of-00001-b105ab56855808e4.parquet",
    "test_parquet": "data/test-00000-of-00001-e1663a0932037903.parquet",
}

WRAPPER_DRIFT_NOTES = [
    "The original first-party CIKM18 release is publicly unrecoverable from the author repo plus linked Baidu Pan surface.",
    "This module therefore uses the accessible FinAI wrapper as the canonical public source surface.",
    "The wrapper page shows roughly 4.97k rows, while OpenFinLLM documentation cites 4,967 rows.",
    "OpenFinLLM documentation also introduces benchmark-layer wording drift on threshold semantics and ACC+MCC reporting relative to the original paper's ACC-only evaluation.",
]

TICKER_DATE_PATTERN = re.compile(r"\$([A-Za-z0-9_.-]+).*?\bat\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE | re.DOTALL)


def ensure_hf_env() -> None:
    os.environ.setdefault("HF_HOME", str(HF_HOME_DIR))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(HF_CACHE_DIR))
    os.environ.setdefault("HF_HUB_CACHE", str(HF_CACHE_DIR))
    os.environ.setdefault("HF_XET_CACHE", str(HF_HOME_DIR / "xet"))
    os.environ.setdefault("XDG_CACHE_HOME", str(HF_HOME_DIR / "xdg"))
    for path in [HF_HOME_DIR, HF_CACHE_DIR, HF_HOME_DIR / "xet", HF_HOME_DIR / "xdg"]:
        path.mkdir(parents=True, exist_ok=True)


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


def extract_ticker_and_target_date(query: str) -> tuple[str | None, str | None]:
    if not isinstance(query, str):
        return None, None
    match = TICKER_DATE_PATTERN.search(query)
    if not match:
        return None, None
    return match.group(1).upper(), match.group(2)


def split_context_text(text: str) -> tuple[str | None, str | None]:
    if not isinstance(text, str):
        return None, None
    parts = text.split("\n\n", 1)
    if len(parts) == 1:
        return text, None
    return parts[0], parts[1]


def copy_raw_file(repo_id: str, filename: str, destination_name: str) -> Path:
    cached_path = Path(
        hf_hub_download(
            repo_id=repo_id,
            repo_type="dataset",
            filename=filename,
            revision=SOURCE_REVISION,
            cache_dir=str(HF_CACHE_DIR),
        )
    )
    destination = RAW_DIR / destination_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cached_path, destination)
    return destination


def derive_label_mapping(dataset) -> tuple[dict[int, str], dict]:
    global_mapping: dict[int, str] = {}
    split_mapping_summary = {}
    for split, split_ds in dataset.items():
        answer_by_gold: dict[int, Counter] = defaultdict(Counter)
        for row in split_ds:
            answer_by_gold[int(row["gold"])][str(row["answer"])] += 1
        split_mapping = {}
        for gold_value, counts in sorted(answer_by_gold.items()):
            if len(counts) != 1:
                raise RuntimeError(f"Inconsistent answer/gold mapping in split {split}: {gold_value} -> {dict(counts)}")
            answer = next(iter(counts))
            split_mapping[gold_value] = {"answer": answer, "count": counts[answer]}
            global_existing = global_mapping.get(gold_value)
            if global_existing is not None and global_existing != answer:
                raise RuntimeError(f"Inconsistent gold mapping across splits for {gold_value}: {global_existing} vs {answer}")
            global_mapping[gold_value] = answer
        split_mapping_summary[split] = split_mapping

    if set(global_mapping.values()) != {"Rise", "Fall"}:
        raise RuntimeError(f"Unexpected global wrapper answer mapping: {global_mapping}")
    return global_mapping, split_mapping_summary


def build_processed_rows(dataset, label_mapping: dict[int, str]) -> tuple[dict[str, list[dict]], dict]:
    processed: dict[str, list[dict]] = {"train": [], "valid": [], "test": []}
    class_balance = {}
    parseability = {}
    split_field_sets = {}

    for split, split_ds in dataset.items():
        field_set_counter = Counter()
        ticker_parse_success = 0
        target_date_parse_success = 0
        price_block_parse_success = 0
        social_block_parse_success = 0

        for row in split_ds:
            gold_int = int(row["gold"])
            gold_label_text = label_mapping[gold_int]
            gold_label = 1 if gold_label_text == "Rise" else 0
            ticker, target_date = extract_ticker_and_target_date(row["query"])
            if ticker is not None:
                ticker_parse_success += 1
            if target_date is not None:
                target_date_parse_success += 1
            price_history_block, social_text_block = split_context_text(row["text"])
            if price_history_block:
                price_block_parse_success += 1
            if social_text_block:
                social_block_parse_success += 1

            record = {
                "example_id": str(row["id"]),
                "dataset_id": DATASET_ID,
                "split": split,
                "raw_id": str(row["id"]),
                "query": row["query"],
                "context_text": row["text"],
                "wrapper_answer_text": row["answer"],
                "wrapper_choices": list(row["choices"]),
                "wrapper_gold_int": gold_int,
                "gold_label_text": gold_label_text,
                "gold_label": gold_label,
                "ticker": ticker,
                "target_date": target_date,
                "price_history_block": price_history_block,
                "social_text_block": social_text_block,
                "source_repo": SOURCE_REPO,
                "source_revision": SOURCE_REVISION,
                "source_path": f"{split}_split_wrapper_row",
                "source_fields_present": sorted(row.keys()),
            }
            processed[split].append(record)
            field_set_counter[tuple(sorted(row.keys()))] += 1

        class_balance[split] = dict(sorted(Counter(row["gold_label_text"] for row in processed[split]).items()))
        parseability[split] = {
            "rows": len(processed[split]),
            "ticker_parse_success": ticker_parse_success,
            "target_date_parse_success": target_date_parse_success,
            "price_history_block_parse_success": price_block_parse_success,
            "social_text_block_parse_success": social_block_parse_success,
        }
        split_field_sets[split] = [
            {"fields": list(fields), "count": count}
            for fields, count in sorted(field_set_counter.items(), key=lambda item: item[0])
        ]

    audit = {
        "class_balance_by_split": class_balance,
        "parseability_by_split": parseability,
        "wrapper_field_sets_by_split": split_field_sets,
    }
    return processed, audit


def main() -> None:
    ensure_hf_env()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    info = api.repo_info(repo_id=SOURCE_REPO, repo_type="dataset", revision=SOURCE_REVISION)
    if info.sha != SOURCE_REVISION:
        raise RuntimeError(f"Resolved source revision {info.sha} does not match expected {SOURCE_REVISION}")

    source_files_present = {s.rfilename for s in info.siblings}
    for source_filename in SOURCE_FILES.values():
        if source_filename not in source_files_present:
            raise FileNotFoundError(f"Missing wrapper source file at pinned revision: {source_filename}")

    raw_files = {
        "README.md": copy_raw_file(SOURCE_REPO, SOURCE_FILES["README.md"], "README.md"),
        "train_parquet": copy_raw_file(SOURCE_REPO, SOURCE_FILES["train_parquet"], Path(SOURCE_FILES["train_parquet"]).name),
        "valid_parquet": copy_raw_file(SOURCE_REPO, SOURCE_FILES["valid_parquet"], Path(SOURCE_FILES["valid_parquet"]).name),
        "test_parquet": copy_raw_file(SOURCE_REPO, SOURCE_FILES["test_parquet"], Path(SOURCE_FILES["test_parquet"]).name),
    }

    dataset = load_dataset(SOURCE_REPO, revision=SOURCE_REVISION, cache_dir=str(HF_CACHE_DIR))
    label_mapping, split_mapping_summary = derive_label_mapping(dataset)
    processed, audit = build_processed_rows(dataset, label_mapping)

    for split, rows in processed.items():
        write_jsonl(PROCESSED_DIR / f"{split}.jsonl", rows)

    row_counts = {split: len(rows) for split, rows in processed.items()}
    total_rows = sum(row_counts.values())

    label_inventory = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "wrapper_gold_to_label_text": {str(k): v for k, v in sorted(label_mapping.items())},
        "canonical_label_to_id": {"Rise": 1, "Fall": 0},
        "wrapper_answer_gold_crosstab_by_split": split_mapping_summary,
        "notes": [
            "The wrapper gold-int mapping is derived empirically by cross-tabulating wrapper answer text against wrapper gold ids on every split.",
            "The original first-party CIKM18 release is publicly unrecoverable from the author repo plus linked Baidu Pan surface.",
        ],
    }
    write_json(LABEL_INVENTORY_PATH, label_inventory)

    raw_schema_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "source_mirror_reference": SOURCE_MIRROR,
        "accessible_surface_type": "finai_wrapper",
        "original_first_party_release_publicly_unrecoverable": True,
        "wrapper_split_preserved_exactly": True,
        "split_row_counts": row_counts,
        "total_rows": total_rows,
        "raw_columns": list(next(iter(dataset.values())).column_names),
        "wrapper_gold_mapping": {str(k): v for k, v in sorted(label_mapping.items())},
        "wrapper_choices_observed": sorted({tuple(row["wrapper_choices"]) for rows in processed.values() for row in rows}),
        "parseability_by_split": audit["parseability_by_split"],
        "drift_notes": WRAPPER_DRIFT_NOTES,
    }
    write_json(RAW_SCHEMA_SUMMARY_PATH, raw_schema_summary)

    ingest_audit = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "wrapper_answer_gold_mapping_consistent": True,
        "wrapper_answer_gold_crosstab_by_split": split_mapping_summary,
        "split_counts": row_counts,
        "class_balance_by_split": audit["class_balance_by_split"],
        "parseability_by_split": audit["parseability_by_split"],
        "rights_source_chain_caution_present": True,
        "wrapper_surface_drift_notes": WRAPPER_DRIFT_NOTES,
        "original_first_party_release_publicly_unrecoverable": True,
    }
    write_json(INGEST_AUDIT_PATH, ingest_audit)

    download_meta = {
        "source_dataset_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "source_mirror_reference": SOURCE_MIRROR,
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_paths": list(SOURCE_FILES.values()),
        "split_names": sorted(dataset.keys()),
        "split_row_counts_observed": row_counts,
        "file_sizes_bytes": {path.name: path.stat().st_size for path in raw_files.values()},
        "sha256_by_file": {path.name: sha256_file(path) for path in raw_files.values()},
        "notes": [
            "The original first-party CIKM18 release is publicly unrecoverable from the author repo and linked Baidu Pan surface.",
            "This module uses TheFinAI/flare-sm-cikm as the canonical accessible wrapper surface and preserves its split exactly.",
            *WRAPPER_DRIFT_NOTES,
        ],
    }
    write_json(DOWNLOAD_META_PATH, download_meta)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "published_splits": ["train", "valid", "test"],
        "wrapper_split_preserved_exactly": True,
        "row_counts": row_counts,
        "total_rows": total_rows,
        "class_balance_by_split": audit["class_balance_by_split"],
        "wrapper_gold_to_label_text": {str(k): v for k, v in sorted(label_mapping.items())},
        "original_first_party_release_publicly_unrecoverable": True,
        "publication_rights_caution": True,
    }
    write_json(INGEST_SUMMARY_PATH, ingest_summary)

    print(f"[DONE] Ingested {DATASET_ID}")
    print(f"[INFO] source_revision={SOURCE_REVISION}")
    print(f"[INFO] row_counts={row_counts}")


if __name__ == "__main__":
    main()
