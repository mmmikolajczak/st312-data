import json
import hashlib
from pathlib import Path
from collections import Counter

RAW_FILES = {
    "train": Path("data/multifin/raw/multifin_highlevel_train_raw.jsonl"),
    "validation": Path("data/multifin/raw/multifin_highlevel_validation_raw.jsonl"),
    "test": Path("data/multifin/raw/multifin_highlevel_test_raw.jsonl"),
}

OUT_FILES = {
    "train": Path("data/multifin/processed/multifin_highlevel_train_clean.jsonl"),
    "validation": Path("data/multifin/processed/multifin_highlevel_validation_clean.jsonl"),
    "test": Path("data/multifin/processed/multifin_highlevel_test_clean.jsonl"),
}

META_PATH = Path("data/multifin/processed/multifin_highlevel_clean_meta.json")

ALLOWED_LABELS = {
    "Technology",
    "Industry",
    "Tax & Accounting",
    "Finance",
    "Government & Controls",
    "Business & Management",
}

def stable_id(source: str, upstream_id: str, text: str, label: str) -> str:
    h = hashlib.sha256()
    h.update(source.encode("utf-8"))
    h.update(b"\n")
    h.update(upstream_id.encode("utf-8"))
    h.update(b"\n")
    h.update(text.encode("utf-8"))
    h.update(b"\n")
    h.update(label.encode("utf-8"))
    return h.hexdigest()[:16]

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    overall_counts = Counter()
    split_meta = {}

    for split, in_path in RAW_FILES.items():
        rows_out = []
        counts = Counter()
        n_in = 0

        for rec in load_jsonl(in_path):
            n_in += 1
            raw = rec["raw"]

            text = str(raw["text"]).strip()
            label = str(raw["label"]).strip()
            lang = str(raw["lang"]).strip()
            upstream_id = str(raw["id"]).strip()

            if not text:
                raise ValueError(f"Empty text in split={split}, row={n_in}")
            if label not in ALLOWED_LABELS:
                raise ValueError(f"Unexpected label '{label}' in split={split}, row={n_in}")

            ex_id = stable_id(rec["source"], upstream_id, text, label)

            out = {
                "example_id": ex_id,
                "dataset_id": "multifin_highlevel_v0",
                "config": "all_languages_highlevel",
                "data": {
                    "text": text,
                    "language": lang
                },
                "label": {
                    "topic": label
                },
                "meta": {
                    "source": rec["source"],
                    "upstream_id": upstream_id,
                    "upstream_split": split,
                    "hf_config": rec["config"]
                }
            }

            rows_out.append(out)
            counts[label] += 1
            overall_counts[label] += 1

        write_jsonl(OUT_FILES[split], rows_out)

        split_meta[split] = {
            "n_in": n_in,
            "n_out": len(rows_out),
            "label_counts": dict(counts),
            "out_file": str(OUT_FILES[split])
        }

        print(f"[DONE] {split}: read {n_in}, wrote {len(rows_out)} -> {OUT_FILES[split]}")
        print(f"[INFO] {split} label counts: {dict(counts)}")

    meta = {
        "dataset_id": "multifin_highlevel_v0",
        "config": "all_languages_highlevel",
        "source_dataset": "awinml/MultiFin",
        "splits": split_meta,
        "overall_label_counts": dict(overall_counts),
        "allowed_labels": sorted(ALLOWED_LABELS),
        "split_policy": "preserve_upstream_train_validation_test"
    }

    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"[META] {META_PATH}")
    print("[OK] Cleaning complete.")

if __name__ == "__main__":
    main()
