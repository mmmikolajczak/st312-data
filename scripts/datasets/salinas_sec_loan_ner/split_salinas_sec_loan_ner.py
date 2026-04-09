import json
from collections import Counter
from pathlib import Path

PROCESSED_DIR = Path("data/salinas_sec_loan_ner/processed")
ALL_CLEAN_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_all_clean.jsonl"
TRAIN_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_train.jsonl"
TEST_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_test.jsonl"
SPLIT_META_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_split_meta.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    if not ALL_CLEAN_PATH.exists():
        raise SystemExit(f"Missing all-clean file: {ALL_CLEAN_PATH}. Run cleaning first.")

    counts = Counter()
    token_counts = Counter()
    source_files_by_split = {"train": set(), "test": set()}

    with TRAIN_PATH.open("w", encoding="utf-8") as f_train, TEST_PATH.open("w", encoding="utf-8") as f_test:
        for rec in load_jsonl(ALL_CLEAN_PATH):
            split = rec["meta"]["canonical_split"]
            if split not in {"train", "test"}:
                raise ValueError(f"Unexpected canonical_split={split!r}")
            if split == "train":
                f_train.write(json.dumps(rec, ensure_ascii=False) + "\n")
            else:
                f_test.write(json.dumps(rec, ensure_ascii=False) + "\n")
            counts[split] += 1
            token_counts[split] += len(rec["data"]["tokens"])
            source_files_by_split[split].add(rec["meta"]["source_file"])

    if source_files_by_split["train"] != {"FIN5.txt"}:
        raise ValueError(f"Train split source mismatch: {source_files_by_split['train']}")
    if source_files_by_split["test"] != {"FIN3.txt"}:
        raise ValueError(f"Test split source mismatch: {source_files_by_split['test']}")

    split_meta = {
        "dataset_id": "salinas_sec_loan_ner_v0",
        "split_policy": {
            "type": "original_author_split",
            "train_source_files": ["FIN5.txt"],
            "test_source_files": ["FIN3.txt"],
            "dev_split_note": "Any internal dev split should be derived from FIN5 only.",
        },
        "example_counts": dict(counts),
        "token_counts": dict(token_counts),
        "source_files_by_split": {k: sorted(v) for k, v in source_files_by_split.items()},
    }
    SPLIT_META_PATH.write_text(json.dumps(split_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Train file: {TRAIN_PATH}")
    print(f"[DONE] Test file:  {TEST_PATH}")
    print(f"[DONE] Split meta: {SPLIT_META_PATH}")
    print(f"[INFO] Example counts: {dict(counts)}")


if __name__ == "__main__":
    main()
