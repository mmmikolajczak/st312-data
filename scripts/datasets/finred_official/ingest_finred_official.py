import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path("data/finred_official/raw")
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1-k5H79NkqzLkkF4KcndqxAPojnBbmqa4?usp=sharing"


def ensure_gdown():
    if importlib.util.find_spec("gdown") is None:
        raise SystemExit(
            "gdown is required for Google Drive folder download. "
            "Install it with: python -m pip install gdown"
        )


def run_download(force: bool) -> None:
    ensure_gdown()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Download the whole folder into RAW_DIR.
    cmd = [
        sys.executable, "-m", "gdown",
        "--folder",
        DRIVE_FOLDER_URL,
        "-O", str(RAW_DIR),
    ]
    if force:
        # gdown will overwrite as needed; we simply rerun.
        pass

    print("[INFO] Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def summarize_files():
    files = []
    for p in sorted(RAW_DIR.rglob("*")):
        if p.is_file():
            files.append({
                "relative_path": str(p.relative_to(RAW_DIR)),
                "bytes": p.stat().st_size,
            })
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    run_download(force=args.force)

    meta = {
        "dataset_id": "finred_official_v0",
        "source_kind": "official_repo_google_drive_release",
        "official_repo_url": "https://github.com/soummyaah/FinRED",
        "official_drive_folder_url": DRIVE_FOLDER_URL,
        "paper_url": "https://arxiv.org/pdf/2306.03736",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": summarize_files(),
        "notes": [
            "Author release downloaded from official Google Drive folder linked in the official repository README.",
            "Train/dev/test split is preserved from the author release.",
            "Train/dev are weakly supervised via distant supervision; paper states test data were manually annotated for evaluation.",
        ],
    }

    meta_path = RAW_DIR / "finred_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote ingest metadata: {meta_path}")
    print("[INFO] Downloaded files:")
    for row in meta["files"]:
        print(f"  - {row['relative_path']} ({row['bytes']} bytes)")


if __name__ == "__main__":
    main()
