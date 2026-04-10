import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FNXL_CANDIDATES = [
    Path("/Users/matti/Downloads/FNXL data"),
    Path("/Users/matti/Downloads/FNXL"),
]
SOURCE_DATA = Path("/Users/matti/Downloads/Data")

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
AUX_DOWNSTREAM = [
    SOURCE_DATA / "consolidated_xbrl_train.csv",
    SOURCE_DATA / "consolidated_xbrl_test.csv",
]


def resolve_fnxl_root() -> Path:
    existing = [p for p in SOURCE_FNXL_CANDIDATES if p.exists()]
    if not existing:
        raise SystemExit(
            "None of the expected FNXL roots exist: "
            + ", ".join(str(p) for p in SOURCE_FNXL_CANDIDATES)
        )
    return existing[0]


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
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    source_fnxl = resolve_fnxl_root()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    copied = []
    for name in REQUIRED + OPTIONAL:
        src = source_fnxl / name
        if not src.exists():
            if name in OPTIONAL:
                continue
            raise SystemExit(f"Required source file missing: {src}")
        dst = RAW_DIR / name
        n_bytes = copy_file(src, dst, force=args.force)
        copied.append({
            "source_path": str(src),
            "copied_to": str(dst),
            "bytes": n_bytes,
            "required": name in REQUIRED,
        })
        print(f"[OK] {src} -> {dst} ({n_bytes} bytes)")

    aux_info = []
    for p in AUX_DOWNSTREAM:
        aux_info.append({
            "path": str(p),
            "exists": p.exists(),
            "role": "downstream_auxiliary_not_for_raw_ingestion",
        })

    meta = {
        "dataset_id": "fnxl_sharma2023_v0",
        "source_kind": "local_author_release_copy",
        "paper_title": "Financial Numeric Extreme Labelling: A Dataset and Benchmarking for XBRL Tagging",
        "resolved_download_root_fnxl": str(source_fnxl),
        "candidate_download_roots_fnxl": [str(p) for p in SOURCE_FNXL_CANDIDATES],
        "download_root_data": str(SOURCE_DATA),
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "copied_files": copied,
        "auxiliary_downstream_files": aux_info,
        "notes": [
            "Canonical raw ingest source is local FNXL train/dev/test release.",
            "allLabelCount.csv is treated as authoritative label inventory.",
            "labels.json is auxiliary only.",
            "consolidated_xbrl_* files are preserved only as provenance pointers and not used for raw ingestion.",
            "Original release split is preserved for provenance only; canonical pipeline split will be rebuilt cleanly later.",
        ],
    }
    meta_path = RAW_DIR / "fnxl_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {meta_path}")


if __name__ == "__main__":
    main()
