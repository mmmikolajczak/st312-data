import json
from pathlib import Path

RAW_DIR = Path("data/finred_official/raw")

def preview_text_file(path: Path, n: int = 3):
    print("=" * 100)
    print(f"[FILE] {path.relative_to(RAW_DIR)}")
    print("-" * 100)
    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                print(f"{i:>3}: {line.rstrip()}")
                if i >= n:
                    break
    except UnicodeDecodeError:
        print("[BINARY OR NON-UTF8 FILE]")
    print()

def main():
    files = sorted([p for p in RAW_DIR.rglob("*") if p.is_file()])
    print(f"[INFO] Total files under raw/: {len(files)}")
    for p in files:
        print(f"  - {p.relative_to(RAW_DIR)}")
    print()

    interesting = []
    for p in files:
        name = p.name.lower()
        if (
            name.endswith(".sent")
            or name.endswith(".tup")
            or name.endswith(".pointer")
            or name == "relations.txt"
        ):
            interesting.append(p)

    print(f"[INFO] Interesting released files: {len(interesting)}")
    for p in interesting:
        print(f"  - {p.relative_to(RAW_DIR)}")
    print()

    for p in interesting:
        preview_text_file(p, n=5)

    meta_path = RAW_DIR / "finred_ingest_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        print("=" * 100)
        print("[INGEST META SUMMARY]")
        print(json.dumps({
            "dataset_id": meta["dataset_id"],
            "n_files": len(meta["files"]),
            "sample_files": meta["files"][:10],
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
