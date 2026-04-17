import argparse
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path("data/australian_credit_uci_statlog/raw")
DOWNLOADS = {
    "australian.dat": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/australian/australian.dat",
    "australian.doc": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/australian/australian.doc",
}

def download(url: str, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, dst.open("wb") as f:
        shutil.copyfileobj(r, f)

def copy_if_needed(src: Path, dst: Path, force: bool):
    if dst.exists() and not force:
        return
    shutil.copy2(src, dst)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download-from-uci", action="store_true")
    ap.add_argument("--source-dir", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    copied = []

    for name, url in DOWNLOADS.items():
        dst = RAW_DIR / name
        src = None

        if args.source_dir:
            candidate = Path(args.source_dir).expanduser() / name
            if candidate.exists():
                src = candidate
        else:
            candidate = Path.home() / "Downloads" / name
            if candidate.exists():
                src = candidate

        if src is not None:
            copy_if_needed(src, dst, args.force)
            print(f"[OK] {src} -> {dst} ({dst.stat().st_size} bytes)")
            copied.append({"name": name, "mode": "local_copy", "path": str(dst), "bytes": dst.stat().st_size})
        else:
            if not args.download_from_uci:
                raise SystemExit(f"Missing local source for {name}. Re-run with --download-from-uci or provide --source-dir.")
            download(url, dst)
            print(f"[OK] {url} -> {dst} ({dst.stat().st_size} bytes)")
            copied.append({"name": name, "mode": "download", "url": url, "path": str(dst), "bytes": dst.stat().st_size})

    meta = {
        "dataset_id": "australian_credit_uci_statlog_v0",
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_source": "UCI Statlog (Australian Credit Approval)",
        "doi": "10.24432/C59012",
        "source_license": "CC BY 4.0",
        "raw_files": copied,
        "notes": [
            "Raw UCI files are preserved unchanged.",
            "FLARE wrapper is downstream reference only, not canonical source.",
        ],
    }
    meta_path = RAW_DIR / "australian_credit_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {meta_path}")

if __name__ == "__main__":
    main()
