import argparse
import json
from pathlib import Path


PROC_DIR = Path("data/cortis2017_tsa/processed")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def ids(path: Path):
    return [row["example_id"] for row in load_jsonl(path)]


def min_max_labels(path: Path):
    values = []
    for row in load_jsonl(path):
        label = row.get("label", {}).get("sentiment_score")
        if label is not None:
            values.append(float(label))
    if not values:
        return None
    return {"min": min(values), "max": max(values), "n": len(values)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed-dir", default=str(PROC_DIR))
    args = ap.parse_args()

    proc_dir = Path(args.processed_dir)

    train_path = proc_dir / "cortis2017_tsa_train.jsonl"
    trial_path = proc_dir / "cortis2017_tsa_trial.jsonl"
    test_inputs_path = proc_dir / "cortis2017_tsa_test_inputs.jsonl"
    test_scored_path = proc_dir / "cortis2017_tsa_test_scored.jsonl"

    for path in (train_path, trial_path, test_inputs_path):
        if not path.exists():
            raise SystemExit(f"Missing processed split file: {path}")

    train_ids = set(ids(train_path))
    trial_ids = set(ids(trial_path))
    test_input_ids = set(ids(test_inputs_path))
    test_scored_ids = set(ids(test_scored_path)) if test_scored_path.exists() else set()

    meta = {
        "dataset_id": "cortis2017_tsa_v0",
        "split_policy": "official_preserved_train_trial_test",
        "counts": {
            "train": len(train_ids),
            "trial": len(trial_ids),
            "test_inputs": len(test_input_ids),
            "test_scored": len(test_scored_ids),
        },
        "overlap": {
            "train_trial": len(train_ids & trial_ids),
            "train_test_inputs": len(train_ids & test_input_ids),
            "trial_test_inputs": len(trial_ids & test_input_ids),
        },
        "test_scored_subset_of_test_inputs": test_scored_ids.issubset(test_input_ids),
        "label_ranges": {
            "train": min_max_labels(train_path),
            "trial": min_max_labels(trial_path),
            "test_scored": min_max_labels(test_scored_path) if test_scored_path.exists() else None
        },
        "paths": {
            "train": str(train_path),
            "trial": str(trial_path),
            "test_inputs": str(test_inputs_path),
            "test_scored": str(test_scored_path),
        }
    }

    if any(meta["overlap"].values()):
        raise SystemExit(f"Split overlap detected: {meta['overlap']}")

    meta_path = proc_dir / "cortis2017_tsa_split_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[DONE] Split validation complete")
    print(f"[META] {meta_path}")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
