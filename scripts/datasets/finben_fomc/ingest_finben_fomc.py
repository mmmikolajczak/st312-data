import json
from pathlib import Path
from datasets import load_dataset

HF_DATASET_ID = "TheFinAI/finben-fomc"

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n

def main():
    print(f"[LOAD] {HF_DATASET_ID}")
    ds = load_dataset(HF_DATASET_ID)

    meta = {
        "hf_dataset_id": HF_DATASET_ID,
        "splits": {},
        "columns_seen": set(),
    }

    for split_name in ds.keys():
        out_path = Path(f"data/fomc/raw/finben_fomc_{split_name}_raw.jsonl")
        rows = []
        for ex in ds[split_name]:
            row = {
                "_id": ex.get("id"),
                "query": ex.get("query"),
                "answer": ex.get("answer"),
                "text": ex.get("text"),
                "choices": ex.get("choices"),
                "gold": ex.get("gold"),
                "split": split_name,
                "source": HF_DATASET_ID,
            }
            rows.append(row)
            meta["columns_seen"].update(row.keys())

        n = write_jsonl(out_path, rows)
        meta["splits"][split_name] = {"n_rows": n, "out_file": str(out_path)}
        print(f"[DONE] {split_name}: {n} rows -> {out_path}")

    meta["columns_seen"] = sorted(meta["columns_seen"])
    meta_path = Path("data/fomc/raw/finben_fomc_raw_meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[META] {meta_path}")
    print("[OK] Raw ingestion complete.")

if __name__ == "__main__":
    main()
