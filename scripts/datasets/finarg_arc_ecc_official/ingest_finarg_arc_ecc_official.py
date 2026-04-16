import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "Downloads" / "FinArg-1" / "ECC" / "Argument Relation"
FILES = {
    "train": ROOT / "train.json",
    "dev": ROOT / "dev.json",
    "test": ROOT / "test.json",
}
OUT_DIR = Path("data/finarg_arc_ecc_official/raw")
META_OUT = OUT_DIR / "finarg_arc_ecc_ingest_meta.json"

def copy_file(src: Path, dst: Path, force: bool = False) -> int:
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists() and not force:
        return dst.stat().st_size
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst.stat().st_size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).expanduser() if args.root else ROOT
    files = {k: root / f"{k}.json" for k in ["train", "dev", "test"]}

    copied = []
    for split, src in files.items():
        dst = OUT_DIR / f"{split}.json"
        n_bytes = copy_file(src, dst, force=args.force)
        copied.append({"split": split, "copied_to": str(dst), "bytes": n_bytes})
        print(f"[OK] {src} -> {dst} ({n_bytes} bytes)")

    meta = {
        "dataset_id": "finarg_arc_ecc_official_v0",
        "source_kind": "user_provided_local_release_copy",
        "source_root_description": "Local FinArg-1 ECC Argument Relation release copy",
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "copied_files": copied,
        "notes": [
            "Official ECC ARC train/dev/test split is preserved as released.",
            "Local files are JSON arrays of [arg1, arg2, label].",
            "Local package contains no README/LICENSE; licensing must be tracked from external provenance.",
        ],
    }
    META_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {META_OUT}")

if __name__ == "__main__":
    main()
