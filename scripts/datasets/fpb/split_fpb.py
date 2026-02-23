import argparse
import json
import random
from collections import defaultdict, Counter
from pathlib import Path

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="data/fpb/processed/fpb_allagree_clean.jsonl")
    ap.add_argument("--train-out", default="data/fpb/processed/fpb_allagree_train.jsonl")
    ap.add_argument("--test-out", default="data/fpb/processed/fpb_allagree_test.jsonl")
    ap.add_argument("--meta-out", default="data/fpb/processed/fpb_allagree_split_meta.json")
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    in_path = Path(args.in_path)
    train_out = Path(args.train_out)
    test_out = Path(args.test_out)
    meta_out = Path(args.meta_out)

    rng = random.Random(args.seed)

    # Group by label for stratification
    buckets = defaultdict(list)
    all_records = []
    for rec in load_jsonl(in_path):
        label = rec["label"]["sentiment"]
        buckets[label].append(rec)
        all_records.append(rec)

    label_counts = {k: len(v) for k, v in buckets.items()}
    total = sum(label_counts.values())

    # Shuffle each bucket deterministically, then split
    train_records = []
    test_records = []
    for label, recs in buckets.items():
        rng.shuffle(recs)
        n_test = int(round(len(recs) * args.test_frac))
        test_records.extend(recs[:n_test])
        train_records.extend(recs[n_test:])

    # Shuffle final splits (optional but nice)
    rng.shuffle(train_records)
    rng.shuffle(test_records)

    # Collect split stats
    train_counts = Counter(r["label"]["sentiment"] for r in train_records)
    test_counts = Counter(r["label"]["sentiment"] for r in test_records)

    meta = {
        "dataset_id": "fpb",
        "config": "allagree",
        "input_file": str(in_path),
        "seed": args.seed,
        "test_frac": args.test_frac,
        "total": total,
        "label_counts_total": dict(label_counts),
        "n_train": len(train_records),
        "n_test": len(test_records),
        "label_counts_train": dict(train_counts),
        "label_counts_test": dict(test_counts),
    }

    write_jsonl(train_out, train_records)
    write_jsonl(test_out, test_records)
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[DONE] Total: {total} | Train: {len(train_records)} | Test: {len(test_records)}")
    print(f"[INFO] Train label counts: {dict(train_counts)}")
    print(f"[INFO] Test  label counts: {dict(test_counts)}")
    print(f"[OUT]  {train_out}")
    print(f"[OUT]  {test_out}")
    print(f"[META] {meta_out}")

if __name__ == "__main__":
    main()
