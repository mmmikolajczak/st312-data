import json
from pathlib import Path
from datasets import load_dataset

HF_DATASET_ID = "awinml/MultiFin"
CONFIG_NAME = "all_languages_highlevel"

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n

def main():
    print(f"[LOAD] dataset={HF_DATASET_ID} config={CONFIG_NAME}")
    ds = load_dataset(HF_DATASET_ID, CONFIG_NAME)

    meta = {
        "hf_dataset_id": HF_DATASET_ID,
        "config_name": CONFIG_NAME,
        "splits": {},
    }

    for split_name in ds.keys():
        out_path = Path(f"data/multifin/raw/multifin_highlevel_{split_name}_raw.jsonl")

        rows = []
        for i, ex in enumerate(ds[split_name]):
            row = {
                "raw": ex,
                "split": split_name,
                "source": HF_DATASET_ID,
                "config": CONFIG_NAME
            }
            rows.append(row)

        n = write_jsonl(out_path, rows)

        feature_names = list(ds[split_name].features.keys())
        meta["splits"][split_name] = {
            "n_rows": n,
            "out_file": str(out_path),
            "feature_names": feature_names,
        }

        print(f"[DONE] {split_name}: {n} rows -> {out_path}")
        print(f"[INFO] {split_name} features: {feature_names}")

    meta_path = Path("data/multifin/raw/multifin_highlevel_raw_meta.json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"[META] {meta_path}")
    print("[OK] Raw ingestion complete.")

if __name__ == "__main__":
    main()
