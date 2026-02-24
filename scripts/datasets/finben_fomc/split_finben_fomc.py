import json
import random
from pathlib import Path
from collections import defaultdict, Counter

IN_PATH = Path("data/fomc/processed/finben_fomc_all_clean.jsonl")
TRAIN_PATH = Path("data/fomc/processed/finben_fomc_train.jsonl")
TEST_PATH = Path("data/fomc/processed/finben_fomc_test.jsonl")
META_PATH = Path("data/fomc/processed/finben_fomc_split_meta.json")

SEED = 42
TEST_FRAC = 0.20
LABEL_ORDER = ["dovish", "hawkish", "neutral"]

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    rows = []
    with IN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    by_label = defaultdict(list)
    for r in rows:
        y = r["label"]["stance"]
        by_label[y].append(r)

    rng = random.Random(SEED)
    train_rows = []
    test_rows = []

    per_label = {}

    for label in LABEL_ORDER:
        bucket = by_label.get(label, [])
        if not bucket:
            continue

        rng.shuffle(bucket)
        n = len(bucket)
        n_test = int(round(n * TEST_FRAC))
        if n_test < 1 and n >= 1:
            n_test = 1
        if n_test >= n and n > 1:
            n_test = n - 1

        test_part = bucket[:n_test]
        train_part = bucket[n_test:]

        for r in test_part:
            r["meta"]["split"] = "test"
        for r in train_part:
            r["meta"]["split"] = "train"

        test_rows.extend(test_part)
        train_rows.extend(train_part)

        per_label[label] = {
            "total": n,
            "train": len(train_part),
            "test": len(test_part)
        }

    # Optional stable order after split
    train_rows.sort(key=lambda r: r["example_id"])
    test_rows.sort(key=lambda r: r["example_id"])

    train_ids = {r["example_id"] for r in train_rows}
    test_ids = {r["example_id"] for r in test_rows}
    overlap = train_ids & test_ids
    if overlap:
        raise RuntimeError(f"Overlap detected between train/test: {len(overlap)}")

    if len(train_rows) + len(test_rows) != len(rows):
        raise RuntimeError("Split size mismatch")

    write_jsonl(TRAIN_PATH, train_rows)
    write_jsonl(TEST_PATH, test_rows)

    train_counts = Counter(r["label"]["stance"] for r in train_rows)
    test_counts = Counter(r["label"]["stance"] for r in test_rows)

    meta = {
        "dataset_id": "finben_fomc_v0",
        "config": "stratified_80_20_v0",
        "source_clean_file": str(IN_PATH),
        "seed": SEED,
        "test_fraction": TEST_FRAC,
        "n_total": len(rows),
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "label_counts_train": dict(train_counts),
        "label_counts_test": dict(test_counts),
        "per_label_split": per_label,
        "files": {
            "train": str(TRAIN_PATH),
            "test": str(TEST_PATH)
        }
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] train={len(train_rows)} -> {TRAIN_PATH}")
    print(f"[DONE] test ={len(test_rows)} -> {TEST_PATH}")
    print(f"[INFO] train counts: {dict(train_counts)}")
    print(f"[INFO] test counts:  {dict(test_counts)}")
    print(f"[META] {META_PATH}")
    print("[OK] Stratified split complete.")

if __name__ == "__main__":
    main()
