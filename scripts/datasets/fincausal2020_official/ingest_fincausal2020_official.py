import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path("data/fincausal2020_official/raw")
BASE = "https://raw.githubusercontent.com/yseop/YseopLab/develop/FNP_2020_FinCausal"

FILES = {
    "README.adoc": f"{BASE}/README.adoc",
    "data/README.adoc": f"{BASE}/data/README.adoc",
    "data/trial/fnp2020-fincausal-task1.csv": f"{BASE}/data/trial/fnp2020-fincausal-task1.csv",
    "data/trial/fnp2020-fincausal-task2.csv": f"{BASE}/data/trial/fnp2020-fincausal-task2.csv",
    "data/practice/fnp2020-fincausal2-task1.csv": f"{BASE}/data/practice/fnp2020-fincausal2-task1.csv",
    "data/practice/fnp2020-fincausal2-task2.csv": f"{BASE}/data/practice/fnp2020-fincausal2-task2.csv",
    "data/evaluation/task1_blind.csv": f"{BASE}/data/evaluation/task1_blind.csv",
    "data/evaluation/task2_blind.csv": f"{BASE}/data/evaluation/task2_blind.csv",
    "scoring/task1/task1_evaluate.py": f"{BASE}/scoring/task1/task1_evaluate.py",
    "scoring/task2/task2_evaluate.py": f"{BASE}/scoring/task2/task2_evaluate.py",
}

def download(url: str, dest: Path, force: bool = False) -> int:
    if dest.exists() and not force:
        return dest.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        data = response.read()
    dest.write_bytes(data)
    return len(data)

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

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    downloads = []

    for rel_path, url in FILES.items():
        dest = RAW_DIR / rel_path
        n_bytes = download(url, dest, force=args.force)
        downloads.append({
            "relative_path": rel_path,
            "url": url,
            "bytes": n_bytes,
        })
        print(f"[OK] {rel_path} -> {dest} ({n_bytes} bytes)")

    meta = {
        "dataset_id": "fincausal2020_official_v0",
        "source_kind": "official_yseoplab_repo_release",
        "official_repo_url": "https://github.com/yseop/YseopLab/tree/develop/FNP_2020_FinCausal",
        "paper_url": "https://aclanthology.org/2020.fnp-1.3.pdf",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "downloads": downloads,
        "files_present": summarize_files(),
        "notes": [
            "Official YseopLab release preserved under trial / practice / evaluation.",
            "Task 1 is semicolon-separated binary causal classification.",
            "Task 2 is semicolon-separated cause/effect extraction with possible multiple pairs per source section.",
            "Official scoring scripts were downloaded as reference implementations for evaluation semantics.",
        ],
    }
    meta_path = RAW_DIR / "fincausal2020_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {meta_path}")

if __name__ == "__main__":
    main()
