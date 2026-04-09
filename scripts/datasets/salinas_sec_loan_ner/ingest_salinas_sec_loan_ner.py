import argparse
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

RAW_DIR = Path("data/salinas_sec_loan_ner/raw")
URLS = {
    "FIN5.txt": "https://huggingface.co/datasets/tner/fin/resolve/main/dataset/FIN5.txt",
    "FIN3.txt": "https://huggingface.co/datasets/tner/fin/resolve/main/dataset/FIN3.txt",
}


def download(url: str, dest: Path, force: bool = False) -> int:
    if dest.exists() and not force:
        return dest.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        data = response.read()
    dest.write_bytes(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    downloads = []
    for filename, url in URLS.items():
        dest = RAW_DIR / filename
        n_bytes = download(url, dest, force=args.force)
        downloads.append({
            "filename": filename,
            "url": url,
            "path": str(dest),
            "bytes": n_bytes,
        })
        print(f"[OK] {filename} -> {dest} ({n_bytes} bytes)")

    meta = {
        "dataset_id": "salinas_sec_loan_ner_v0",
        "source_kind": "preservation_mirror_download",
        "paper_url": "https://aclanthology.org/U15-1010.pdf",
        "original_release_url": "http://people.eng.unimelb.edu.au/tbaldwin/resources/finance-sec/",
        "mirror_repo": "tner/fin",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "downloads": downloads,
        "notes": [
            "HF mirror used for raw file retrieval.",
            "Canonical provenance points to Salinas Alvarado, Verspoor, and Baldwin (2015) and the original Melbourne release URL.",
        ],
    }
    meta_path = RAW_DIR / "salinas_sec_loan_ner_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {meta_path}")


if __name__ == "__main__":
    main()
