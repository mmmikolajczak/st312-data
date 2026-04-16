import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path("data/finarg_auc_ecc_official/raw")
OUT_DIR = Path("data/finarg_auc_ecc_official/processed")

FILES = {split: RAW_DIR / f"{split}.json" for split in ["train", "dev", "test"]}
ALL_CLEAN = OUT_DIR / "finarg_auc_ecc_all_clean.jsonl"
CLEAN_META = OUT_DIR / "finarg_auc_ecc_clean_meta.json"

LABEL_MAP = {
    0: "premise",
    1: "claim",
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_records = []
    split_counts = {}
    split_label_counts = {}
    total_counts = Counter()
    split_idx = Counter()

    for split, path in FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        split_counts[split] = len(data)
        label_counter = Counter()

        for row in data:
            if not (isinstance(row, list) and len(row) == 2):
                raise ValueError(f"Malformed AUC row in {path}: {row}")

            text, label_id = row
            if label_id not in LABEL_MAP:
                raise ValueError(f"Unexpected AUC label_id {label_id} in {path}")

            split_idx[split] += 1
            ex_id = f"finarg_auc_ecc_{split}_{split_idx[split]:06d}"
            label = LABEL_MAP[label_id]
            label_counter[label] += 1
            total_counts[label] += 1

            rec = {
                "example_id": ex_id,
                "data": {
                    "text": str(text),
                },
                "label": {
                    "label_id": int(label_id),
                    "label": label,
                    "has_gold": True,
                },
                "meta": {
                    "task_family": "argument_unit_classification",
                    "domain": "earnings_conference_calls",
                    "split": split,
                    "source_file": path.name,
                },
            }
            all_records.append(rec)

        split_label_counts[split] = dict(label_counter)

    with ALL_CLEAN.open("w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": "finarg_auc_ecc_official_v0",
        "split_counts": split_counts,
        "split_label_counts": split_label_counts,
        "global_label_counts": dict(total_counts),
        "label_mapping": {"0": "premise", "1": "claim"},
        "official_split_preserved": True,
        "known_release_issue": {
            "cross_split_exact_sentence_overlap_count": 1,
            "cross_split_exact_sentence_overlap_preview": [
                "So we're very happy with that."
            ],
        },
        "output_files": {
            "all_clean": str(ALL_CLEAN),
            "clean_meta": str(CLEAN_META),
        },
    }
    CLEAN_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote all-clean JSONL: {ALL_CLEAN}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META}")
    print(f"[INFO] Split counts: {split_counts}")
    print(f"[INFO] Global label counts: {dict(total_counts)}")


if __name__ == "__main__":
    main()
