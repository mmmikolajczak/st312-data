import json
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

RAW_DIR = Path("data/finarg_auc_ecc_official/raw")
REPORT_OUT = Path("reports/finarg_auc_ecc_official/raw_audit_summary.json")
FILES = {split: RAW_DIR / f"{split}.json" for split in ["train", "dev", "test"]}

def norm_text(x):
    return " ".join(str(x).split())

def digest(obj):
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    split_counts = {}
    split_label_counts = {}
    global_counts = Counter()
    text_to_splits = defaultdict(set)
    exact_to_splits = defaultdict(set)

    for split, path in FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        split_counts[split] = len(data)
        c = Counter()
        malformed = 0
        for row in data:
            if not (isinstance(row, list) and len(row) == 2):
                malformed += 1
                continue
            sent, lab = row
            c[lab] += 1
            global_counts[lab] += 1
            text_to_splits[norm_text(sent)].add(split)
            exact_to_splits[digest(row)].add(split)
        split_label_counts[split] = dict(c)
        print(f"{split}: rows={len(data)} labels={dict(c)} malformed={malformed}")

    cross_split_text_overlap = {
        txt: sorted(list(splits))
        for txt, splits in text_to_splits.items()
        if len(splits) > 1
    }
    cross_split_exact_overlap = {
        ex: sorted(list(splits))
        for ex, splits in exact_to_splits.items()
        if len(splits) > 1
    }

    summary = {
        "dataset_id": "finarg_auc_ecc_official_v0",
        "split_counts": split_counts,
        "split_label_counts": split_label_counts,
        "global_label_counts": dict(global_counts),
        "inferred_label_mapping": {
            "0": "premise",
            "1": "claim"
        },
        "cross_split_text_overlap_count": len(cross_split_text_overlap),
        "cross_split_exact_example_overlap_count": len(cross_split_exact_overlap),
        "cross_split_text_overlap_preview": list(cross_split_text_overlap.items())[:10],
    }
    REPORT_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[AUC TOTAL]")
    print("split_counts =", split_counts)
    print("global_label_counts =", dict(global_counts))
    print("cross_split_text_overlap_count =", len(cross_split_text_overlap))
    print("cross_split_exact_example_overlap_count =", len(cross_split_exact_overlap))
    print("cross_split_text_overlap_preview =", list(cross_split_text_overlap.items())[:10])
    print(f"[DONE] Wrote raw audit summary: {REPORT_OUT}")

if __name__ == "__main__":
    main()
