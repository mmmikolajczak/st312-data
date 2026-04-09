import json
from collections import Counter
from pathlib import Path

PROCESSED_DIR = Path("data/finred_official/processed")
ALL_CLEAN_PATH = PROCESSED_DIR / "finred_official_all_clean.jsonl"
TRAIN_PATH = PROCESSED_DIR / "finred_official_train.jsonl"
DEV_PATH = PROCESSED_DIR / "finred_official_dev.jsonl"
TEST_PATH = PROCESSED_DIR / "finred_official_test.jsonl"
SPLIT_META_PATH = PROCESSED_DIR / "finred_official_split_meta.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    if not ALL_CLEAN_PATH.exists():
        raise SystemExit(f"Missing all-clean file: {ALL_CLEAN_PATH}")

    counts = Counter()
    triplet_counts = Counter()

    out_files = {
        "train": TRAIN_PATH.open("w", encoding="utf-8"),
        "dev": DEV_PATH.open("w", encoding="utf-8"),
        "test": TEST_PATH.open("w", encoding="utf-8"),
    }

    try:
        for rec in load_jsonl(ALL_CLEAN_PATH):
            split = rec["meta"]["split"]
            if split not in out_files:
                raise ValueError(f"Unexpected split: {split}")
            out_files[split].write(json.dumps(rec, ensure_ascii=False) + "\n")
            counts[split] += 1
            triplet_counts[split] += rec["label"]["n_triplets"]
    finally:
        for f in out_files.values():
            f.close()

    split_meta = {
        "dataset_id": "finred_official_v0",
        "split_policy": {
            "type": "author_provided_split",
            "train": "preserved",
            "dev": "preserved",
            "test": "preserved",
        },
        "example_counts": dict(counts),
        "triplet_counts": dict(triplet_counts),
        "files": {
            "train": str(TRAIN_PATH),
            "dev": str(DEV_PATH),
            "test": str(TEST_PATH),
        },
    }
    SPLIT_META_PATH.write_text(json.dumps(split_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Train file: {TRAIN_PATH}")
    print(f"[DONE] Dev file:   {DEV_PATH}")
    print(f"[DONE] Test file:  {TEST_PATH}")
    print(f"[DONE] Split meta: {SPLIT_META_PATH}")
    print(f"[INFO] Example counts: {dict(counts)}")
    print(f"[INFO] Triplet counts: {dict(triplet_counts)}")


if __name__ == "__main__":
    main()
