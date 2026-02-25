import json
import random
from pathlib import Path
from collections import defaultdict, Counter

IN_PATH = Path("data/finer_ord/processed/finben_finer_ord_all_clean.jsonl")
TRAIN_PATH = Path("data/finer_ord/processed/finben_finer_ord_train.jsonl")
TEST_PATH = Path("data/finer_ord/processed/finben_finer_ord_test.jsonl")
META_PATH = Path("data/finer_ord/processed/finben_finer_ord_split_meta.json")

SEED = 42
TEST_FRAC = 0.2

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def sentence_signature(rec):
    return rec.get("meta", {}).get("label_signature", "UNKNOWN")

def token_label_counter(rows):
    c = Counter()
    for r in rows:
        c.update(r["label"]["tags"])
    return c

def main():
    rows = list(load_jsonl(IN_PATH))
    if not rows:
        raise RuntimeError("No rows found")

    by_sig = defaultdict(list)
    for r in rows:
        by_sig[sentence_signature(r)].append(r)

    rng = random.Random(SEED)
    train_rows, test_rows = [], []
    per_sig = {}

    for sig, group in sorted(by_sig.items()):
        group = list(group)
        rng.shuffle(group)
        n = len(group)

        if n == 1:
            n_test = 0
        else:
            n_test = int(round(n * TEST_FRAC))
            n_test = max(1, n_test)
            n_test = min(n_test, n - 1)

        test_part = group[:n_test]
        train_part = group[n_test:]

        for r in test_part:
            r.setdefault("meta", {})
            r["meta"]["split"] = "test"
        for r in train_part:
            r.setdefault("meta", {})
            r["meta"]["split"] = "train"

        test_rows.extend(test_part)
        train_rows.extend(train_part)

        per_sig[sig] = {"total": n, "train": len(train_part), "test": len(test_part)}

    train_rows.sort(key=lambda r: r["example_id"])
    test_rows.sort(key=lambda r: r["example_id"])

    train_ids = {r["example_id"] for r in train_rows}
    test_ids = {r["example_id"] for r in test_rows}
    overlap = train_ids & test_ids
    if overlap:
        raise RuntimeError(f"Overlap detected: {len(overlap)}")

    if len(train_rows) + len(test_rows) != len(rows):
        raise RuntimeError("Split size mismatch")

    write_jsonl(TRAIN_PATH, train_rows)
    write_jsonl(TEST_PATH, test_rows)

    train_sig_counts = Counter(sentence_signature(r) for r in train_rows)
    test_sig_counts = Counter(sentence_signature(r) for r in test_rows)

    train_token_counts = token_label_counter(train_rows)
    test_token_counts = token_label_counter(test_rows)

    meta = {
        "dataset_id": "finben_finer_ord_v0",
        "config": "stratified_80_20_v0",
        "source_clean_file": str(IN_PATH),
        "seed": SEED,
        "test_fraction": TEST_FRAC,
        "n_total": len(rows),
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "stratify_on": "meta.label_signature",
        "per_signature_split": per_sig,
        "sentence_signature_counts_train": dict(train_sig_counts),
        "sentence_signature_counts_test": dict(test_sig_counts),
        "token_label_counts_train": dict(train_token_counts),
        "token_label_counts_test": dict(test_token_counts),
        "files": {
            "train": str(TRAIN_PATH),
            "test": str(TEST_PATH)
        }
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] train={len(train_rows)} -> {TRAIN_PATH}")
    print(f"[DONE] test ={len(test_rows)} -> {TEST_PATH}")
    print(f"[INFO] sentence signatures train: {dict(train_sig_counts)}")
    print(f"[INFO] sentence signatures test : {dict(test_sig_counts)}")
    print(f"[INFO] token labels train: {dict(train_token_counts)}")
    print(f"[INFO] token labels test : {dict(test_token_counts)}")
    print(f"[META] {META_PATH}")
    print("[OK] Stratified split complete.")

if __name__ == "__main__":
    main()
