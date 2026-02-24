import json
from pathlib import Path

from datasets import load_dataset


HF_DATASET_ID = "TheFinAI/fiqa-sentiment-classification"


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    print(f"[LOAD] Loading dataset from Hugging Face: {HF_DATASET_ID}")
    ds = load_dataset(HF_DATASET_ID)

    # Some datasets use "validation" instead of "valid"; this makes the script robust.
    split_aliases = {
        "train": "train",
        "valid": "valid" if "valid" in ds else ("validation" if "validation" in ds else None),
        "test": "test",
    }

    for canonical_split, actual_split in split_aliases.items():
        if actual_split is None:
            raise RuntimeError(f"Could not find split for canonical '{canonical_split}' in dataset splits: {list(ds.keys())}")

        out_path = Path(f"data/fiqasa/raw/fiqasa_{canonical_split}_raw.jsonl")

        rows = []
        for ex in ds[actual_split]:
            rows.append({
                "_id": ex.get("_id"),
                "sentence": ex.get("sentence"),
                "target": ex.get("target"),
                "aspect": ex.get("aspect"),
                "score": ex.get("score"),
                "type": ex.get("type"),
                "split": canonical_split,
                "source": HF_DATASET_ID,
            })

        n = write_jsonl(out_path, rows)
        print(f"[DONE] {canonical_split}: wrote {n} rows -> {out_path}")

    print("[OK] FiQA raw ingestion complete.")


if __name__ == "__main__":
    main()
