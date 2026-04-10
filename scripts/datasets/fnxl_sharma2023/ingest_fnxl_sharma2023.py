import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FNXL_CANDIDATES = [
    Path.home() / "Downloads" / "FNXL data",
    Path.home() / "Downloads" / "FNXL",
]
DEFAULT_DATA_ROOT = Path.home() / "Downloads" / "Data"

RAW_DIR = Path("data/fnxl_sharma2023/raw/release")

REQUIRED = [
    "allLabelCount.csv",
    "train.csv",
    "dev.csv",
    "test.csv",
    "labels.json",
]
OPTIONAL = [
    "test.xlsx",
]


def resolve_fnxl_root(explicit_source_fnxl: str | None) -> Path:
    if explicit_source_fnxl:
        p = Path(explicit_source_fnxl).expanduser()
        if not p.exists():
            raise SystemExit(f"Explicit --source-fnxl does not exist: {p}")
        return p

    existing = [p for p in DEFAULT_FNXL_CANDIDATES if p.exists()]
    if not existing:
        raise SystemExit(
            "Could not resolve FNXL source directory. "
            "Pass --source-fnxl explicitly or place the release under one of: "
            + ", ".join(str(p) for p in DEFAULT_FNXL_CANDIDATES)
        )
    return existing[0]


def resolve_data_root(explicit_source_data: str | None) -> Path:
    if explicit_source_data:
        p = Path(explicit_source_data).expanduser()
        if not p.exists():
            raise SystemExit(f"Explicit --source-data does not exist: {p}")
        return p
    return DEFAULT_DATA_ROOT


def copy_file(src: Path, dst: Path, force: bool = False) -> int:
    if not src.exists():
        raise FileNotFoundError(f"Missing source file: {src}")
    if dst.exists() and not force:
        return dst.stat().st_size
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst.stat().st_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-fnxl", default=None, help="Path to local FNXL release directory")
    ap.add_argument("--source-data", default=None, help="Path to local auxiliary Data directory")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    source_fnxl = resolve_fnxl_root(args.source_fnxl)
    source_data = resolve_data_root(args.source_data)

    raw_dir = RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for name in REQUIRED + OPTIONAL:
        src = source_fnxl / name
        if not src.exists():
            if name in OPTIONAL:
                continue
            raise SystemExit(f"Required source file missing: {src}")
        dst = raw_dir / name
        n_bytes = copy_file(src, dst, force=args.force)
        copied.append({
            "source_filename": name,
            "copied_to": str(dst),
            "bytes": n_bytes,
            "required": name in REQUIRED,
        })
        print(f"[OK] {src} -> {dst} ({n_bytes} bytes)")

    auxiliary_downstream_files = [
        {
            "filename": "consolidated_xbrl_train.csv",
            "path": str(source_data / "consolidated_xbrl_train.csv"),
            "exists": (source_data / "consolidated_xbrl_train.csv").exists(),
            "role": "downstream_auxiliary_not_for_raw_ingestion",
        },
        {
            "filename": "consolidated_xbrl_test.csv",
            "path": str(source_data / "consolidated_xbrl_test.csv"),
            "exists": (source_data / "consolidated_xbrl_test.csv").exists(),
            "role": "downstream_auxiliary_not_for_raw_ingestion",
        },
    ]

    meta = {
        "dataset_id": "fnxl_sharma2023_v0",
        "source_kind": "user_provided_local_author_release_copy",
        "paper_title": "Financial Numeric Extreme Labelling: A Dataset and Benchmarking for XBRL Tagging",
        "source_resolution_policy": {
            "source_fnxl": "--source-fnxl if provided, else first existing candidate",
            "source_fnxl_candidates": [str(p) for p in DEFAULT_FNXL_CANDIDATES],
            "source_data": "--source-data if provided, else ~/Downloads/Data",
        },
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "copied_files": copied,
        "auxiliary_downstream_files": auxiliary_downstream_files,
        "notes": [
            "Canonical raw ingest source is the local FNXL train/dev/test release.",
            "allLabelCount.csv is treated as authoritative label inventory.",
            "labels.json is auxiliary only.",
            "consolidated_xbrl_* files are preserved only as provenance pointers and not used for raw ingestion.",
            "Original release split is preserved for provenance only; canonical pipeline split is rebuilt cleanly later.",
        ],
    }
    meta_path = raw_dir / "fnxl_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {meta_path}")


if __name__ == "__main__":
    main()
