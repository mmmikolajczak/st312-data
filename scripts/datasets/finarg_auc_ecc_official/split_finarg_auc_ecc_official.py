import json
from pathlib import Path

IN_PATH = Path("data/finarg_auc_ecc_official/processed/finarg_auc_ecc_all_clean.jsonl")
OUT_DIR = Path("data/finarg_auc_ecc_official/processed")

SPLIT_FILES = {
    "train": OUT_DIR / "finarg_auc_ecc_train.jsonl",
    "dev": OUT_DIR / "finarg_auc_ecc_dev.jsonl",
    "test": OUT_DIR / "finarg_auc_ecc_test.jsonl",
}
SPLIT_META = OUT_DIR / "finarg_auc_ecc_split_meta.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    buckets = {"train": [], "dev": [], "test": []}
    for rec in load_jsonl(IN_PATH):
        split = rec["meta"]["split"]
        buckets[split].append(rec)

    for split, path in SPLIT_FILES.items():
        with path.open("w", encoding="utf-8") as f:
            for rec in buckets[split]:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[DONE] {split}: {path} ({len(buckets[split])} rows)")

    split_meta = {
        "dataset_id": "finarg_auc_ecc_official_v0",
        "split_policy": {
            "type": "author_provided_split",
            "train": "preserved",
            "dev": "preserved",
            "test": "preserved",
        },
        "files": {k: str(v) for k, v in SPLIT_FILES.items()},
        "counts": {k: len(v) for k, v in buckets.items()},
    }
    SPLIT_META.write_text(json.dumps(split_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote split metadata: {SPLIT_META}")


if __name__ == "__main__":
    main()
