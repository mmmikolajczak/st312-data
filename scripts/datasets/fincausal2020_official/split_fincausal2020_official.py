import json
from collections import Counter
from pathlib import Path

PROCESSED_DIR = Path("data/fincausal2020_official/processed")

TASK1_ALL_CLEAN_PATH = PROCESSED_DIR / "fincausal2020_task1_all_clean.jsonl"
TASK2_ALL_CLEAN_PATH = PROCESSED_DIR / "fincausal2020_task2_all_clean.jsonl"

TASK1_SPLIT_PATHS = {
    "trial": PROCESSED_DIR / "fincausal2020_task1_trial.jsonl",
    "practice": PROCESSED_DIR / "fincausal2020_task1_practice.jsonl",
    "evaluation": PROCESSED_DIR / "fincausal2020_task1_evaluation.jsonl",
}
TASK2_SPLIT_PATHS = {
    "trial": PROCESSED_DIR / "fincausal2020_task2_trial.jsonl",
    "practice": PROCESSED_DIR / "fincausal2020_task2_practice.jsonl",
    "evaluation": PROCESSED_DIR / "fincausal2020_task2_evaluation.jsonl",
}

SPLIT_META_PATH = PROCESSED_DIR / "fincausal2020_split_meta.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_split_files(src_path: Path, split_paths: dict, label_key: str):
    counts = Counter()
    with {k: v.open("w", encoding="utf-8") for k, v in split_paths.items()} as _:
        pass


def main():
    if not TASK1_ALL_CLEAN_PATH.exists():
        raise SystemExit(f"Missing {TASK1_ALL_CLEAN_PATH}")
    if not TASK2_ALL_CLEAN_PATH.exists():
        raise SystemExit(f"Missing {TASK2_ALL_CLEAN_PATH}")

    task1_counts = Counter()
    task2_counts = Counter()
    task2_gold_counts = Counter()

    task1_files = {k: v.open("w", encoding="utf-8") for k, v in TASK1_SPLIT_PATHS.items()}
    task2_files = {k: v.open("w", encoding="utf-8") for k, v in TASK2_SPLIT_PATHS.items()}

    try:
        for rec in load_jsonl(TASK1_ALL_CLEAN_PATH):
            split = rec["meta"]["split"]
            task1_files[split].write(json.dumps(rec, ensure_ascii=False) + "\n")
            task1_counts[split] += 1

        for rec in load_jsonl(TASK2_ALL_CLEAN_PATH):
            split = rec["meta"]["split"]
            task2_files[split].write(json.dumps(rec, ensure_ascii=False) + "\n")
            task2_counts[split] += 1
            if rec["label"]["has_gold"]:
                task2_gold_counts[split] += 1
    finally:
        for f in task1_files.values():
            f.close()
        for f in task2_files.values():
            f.close()

    split_meta = {
        "dataset_id": "fincausal2020_official_v0",
        "split_policy": {
            "type": "author_provided_split",
            "trial": "preserved",
            "practice": "preserved",
            "evaluation": "preserved_blind",
        },
        "task1_files": {k: str(v) for k, v in TASK1_SPLIT_PATHS.items()},
        "task2_files": {k: str(v) for k, v in TASK2_SPLIT_PATHS.items()},
        "task1_counts": dict(task1_counts),
        "task2_counts": dict(task2_counts),
        "task2_gold_counts": dict(task2_gold_counts),
    }

    SPLIT_META_PATH.write_text(json.dumps(split_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote task1 split files")
    for k, v in TASK1_SPLIT_PATHS.items():
        print(f"  - {k}: {v}")
    print(f"[DONE] Wrote task2 split files")
    for k, v in TASK2_SPLIT_PATHS.items():
        print(f"  - {k}: {v}")
    print(f"[DONE] Wrote split metadata: {SPLIT_META_PATH}")
    print(f"[INFO] Task 1 split counts: {dict(task1_counts)}")
    print(f"[INFO] Task 2 split counts: {dict(task2_counts)}")
    print(f"[INFO] Task 2 gold counts: {dict(task2_gold_counts)}")


if __name__ == "__main__":
    main()
