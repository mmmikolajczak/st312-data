from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DATASET_ID = "ectsum_official_v0"
SOURCE_REPO_URL = "https://github.com/rajdeep345/ECTSum"
SOURCE_REPO_NAME = "rajdeep345/ECTSum"
SOURCE_COMMIT = "6909f1fc543104c1c60cf9de63e799f6620d1b0a"
RAW_DIR = Path("data/ectsum_official/raw")
PROCESSED_DIR = Path("data/ectsum_official/processed")
REPORT_DIR = Path("reports/ectsum_official")
TEMP_CLONE_DIR = Path("/tmp/ectsum_official_src")

SPLIT_SOURCE_DIRS = {
    "train": "data/final/train",
    "val": "data/final/val",
    "test": "data/final/test",
}
TOP_LEVEL_FILES = ["README.md", "LICENSE.txt", "evaluate.py", "prepare_data_ectbps_ext.py", "prepare_data_ectbps_para.py"]


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


def ensure_source_checkout() -> Path:
    if not TEMP_CLONE_DIR.exists():
        subprocess.run(["git", "clone", SOURCE_REPO_URL, str(TEMP_CLONE_DIR)], check=True)
    subprocess.run(["git", "-C", str(TEMP_CLONE_DIR), "fetch", "--all", "--tags"], check=True)
    subprocess.run(["git", "-C", str(TEMP_CLONE_DIR), "checkout", SOURCE_COMMIT], check=True)
    resolved = subprocess.run(
        ["git", "-C", str(TEMP_CLONE_DIR), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != SOURCE_COMMIT:
        raise RuntimeError(f"Resolved commit {resolved} does not match expected {SOURCE_COMMIT}")
    return TEMP_CLONE_DIR


def copy_preserved_source_tree(src_root: Path) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for rel in TOP_LEVEL_FILES:
        shutil.copy2(src_root / rel, RAW_DIR / rel)
    for split, rel_dir in SPLIT_SOURCE_DIRS.items():
        src_dir = src_root / rel_dir
        if not src_dir.exists():
            raise FileNotFoundError(f"Missing split directory: {rel_dir}")
        dst_dir = RAW_DIR / rel_dir
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def build_processed_row(split: str, filename: str, transcript_lines: list[str], summary_lines: list[str]) -> dict:
    stem = Path(filename).stem
    if not transcript_lines or not summary_lines:
        raise ValueError(f"Empty transcript or summary for {split}/{filename}")
    return {
        "example_id": f"{DATASET_ID}__{split}__{stem}",
        "dataset_id": DATASET_ID,
        "split": split,
        "source_filename": filename,
        "transcript_text": "\n".join(transcript_lines),
        "transcript_lines": transcript_lines,
        "reference_summary": "\n".join(summary_lines),
        "reference_bullets": summary_lines,
        "source_section": "prepared_remarks",
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "source_path_ect": f"data/final/{split}/ects/{filename}",
        "source_path_summary": f"data/final/{split}/gt_summaries/{filename}",
    }


def load_nonempty_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]


def main() -> None:
    src_root = ensure_source_checkout()
    copy_preserved_source_tree(src_root)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    processed_by_split: dict[str, list[dict]] = {}
    split_counts = {}
    audit = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "split_counts": {},
        "avg_transcript_words": {},
        "avg_transcript_lines": {},
        "avg_summary_words": {},
        "avg_summary_bullets": {},
        "empty_file_counts": {},
        "duplicate_filename_checks": {},
        "notes": [
            "The paper reports 2,425 cleaned transcript-summary pairs with a random 70/10/20 split.",
            "Source chain involves Motley Fool earnings call transcripts and Reuters article summaries.",
            "This module is carried under a private/internal publication assumption pending licensing review.",
        ],
    }

    all_example_ids = set()
    all_filenames_by_split = {}
    for split in ["train", "val", "test"]:
        ect_dir = RAW_DIR / "data" / "final" / split / "ects"
        sum_dir = RAW_DIR / "data" / "final" / split / "gt_summaries"
        if not ect_dir.exists() or not sum_dir.exists():
            raise FileNotFoundError(f"Missing preserved raw split directories for {split}")

        ect_files = sorted(p.name for p in ect_dir.iterdir() if p.is_file())
        sum_files = sorted(p.name for p in sum_dir.iterdir() if p.is_file())
        if ect_files != sum_files:
            raise ValueError(f"Transcript-summary filename mismatch in split {split}")
        all_filenames_by_split[split] = ect_files

        rows = []
        empty_count = 0
        transcript_words = transcript_lines_count = summary_words = summary_bullets = 0
        for filename in ect_files:
            transcript_path = ect_dir / filename
            summary_path = sum_dir / filename
            transcript_lines = load_nonempty_lines(transcript_path)
            summary_lines = load_nonempty_lines(summary_path)
            if not transcript_lines or not summary_lines:
                empty_count += 1
                continue
            row = build_processed_row(split, filename, transcript_lines, summary_lines)
            if row["example_id"] in all_example_ids:
                raise ValueError(f"Duplicate example_id: {row['example_id']}")
            all_example_ids.add(row["example_id"])
            rows.append(row)
            transcript_words += len(" ".join(transcript_lines).split())
            transcript_lines_count += len(transcript_lines)
            summary_words += len(" ".join(summary_lines).split())
            summary_bullets += len(summary_lines)

        if empty_count:
            raise ValueError(f"Encountered {empty_count} empty transcript/summary pairs in split {split}")
        processed_by_split[split] = rows
        split_counts[split] = len(rows)
        audit["split_counts"][split] = len(rows)
        audit["avg_transcript_words"][split] = transcript_words / len(rows)
        audit["avg_transcript_lines"][split] = transcript_lines_count / len(rows)
        audit["avg_summary_words"][split] = summary_words / len(rows)
        audit["avg_summary_bullets"][split] = summary_bullets / len(rows)
        audit["empty_file_counts"][split] = empty_count
        audit["duplicate_filename_checks"][split] = len(ect_files) != len(set(ect_files))

        write_jsonl(PROCESSED_DIR / f"{split}.jsonl", rows)

    cross_split_overlaps = {
        f"{left}__{right}": sorted(set(all_filenames_by_split[left]).intersection(all_filenames_by_split[right]))
        for left in ["train", "val", "test"]
        for right in ["train", "val", "test"]
        if left < right
    }
    audit["cross_split_duplicate_filenames"] = {k: v[:10] for k, v in cross_split_overlaps.items() if v}
    if any(cross_split_overlaps.values()):
        raise ValueError("Observed duplicate filenames across splits; expected split-level filename disjointness")

    raw_file_manifest = {}
    for path in sorted(p for p in RAW_DIR.rglob("*") if p.is_file()):
        rel = path.relative_to(RAW_DIR).as_posix()
        raw_file_manifest[rel] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    download_meta = {
        "source_repo": SOURCE_REPO_NAME,
        "source_repo_url": SOURCE_REPO_URL,
        "source_commit": SOURCE_COMMIT,
        "source_paths": TOP_LEVEL_FILES + list(SPLIT_SOURCE_DIRS.values()),
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": {path: meta["size_bytes"] for path, meta in raw_file_manifest.items()},
        "sha256_by_file": {path: meta["sha256"] for path, meta in raw_file_manifest.items()},
        "download_method": "git_clone_checkout_copy",
        "notes": [
            "The upstream repo has no tagged releases.",
            "This module is published under a private/internal assumption pending licensing review.",
            "Source texts derive from Motley Fool transcripts and Reuters summaries.",
        ],
    }
    write_json(RAW_DIR / "download_meta.json", download_meta)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "row_counts": split_counts,
        "total_rows": sum(split_counts.values()),
        "published_splits": ["train", "val", "test"],
        "label_inventory_omitted": True,
        "label_inventory_omitted_reason": "ECTSum is a summarization dataset and does not expose a categorical label inventory.",
        "private_scope_publication": True,
    }
    write_json(PROCESSED_DIR / "ingest_summary.json", ingest_summary)
    write_json(REPORT_DIR / "ingest_audit.json", audit)

    print(f"[DONE] Ingested {DATASET_ID}")
    print(f"[INFO] source_commit={SOURCE_COMMIT}")
    print(f"[INFO] split_counts={split_counts}")


if __name__ == "__main__":
    main()
