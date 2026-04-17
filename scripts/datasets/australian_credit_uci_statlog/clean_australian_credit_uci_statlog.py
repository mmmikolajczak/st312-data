import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path("data/australian_credit_uci_statlog/raw")
OUT_DIR = Path("data/australian_credit_uci_statlog/processed")
DAT_PATH = RAW_DIR / "australian.dat"

def parse_rows(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        toks = line.replace(",", " ").split()
        rows.append(toks)
    return rows

def render_feature_text(features: dict) -> str:
    return ", ".join(f"{k}={features[k]}" for k in [f"A{i}" for i in range(1, 15)])

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = parse_rows(DAT_PATH)

    if not rows:
        raise SystemExit("No rows parsed from australian.dat")

    if any(len(r) != 15 for r in rows):
        bad = [len(r) for r in rows if len(r) != 15][:10]
        raise SystemExit(f"Expected all rows to have 15 columns; bad examples: {bad}")

    raw_counts = Counter(r[-1] for r in rows)
    if set(raw_counts) != {"0", "1"}:
        raise SystemExit(f"Unexpected raw label set: {sorted(raw_counts)}")

    records = []
    norm_counts = Counter()

    for idx, row in enumerate(rows, start=1):
        raw_label = row[-1]
        label_id = int(raw_label)
        norm_counts[label_id] += 1

        feature_vals = row[:-1]
        features = {f"A{i+1}": feature_vals[i] for i in range(14)}
        text_render = render_feature_text(features)

        rec = {
            "example_id": f"australian_credit_{idx:06d}",
            "data": {
                "row_id": idx,
                "features": features,
                "text_render": text_render,
                "query": "Should this credit application be approved or rejected based on the anonymized applicant attributes?",
                "choices": ["Reject", "Approve"],
            },
            "label": {
                "raw_label": raw_label,
                "label_id": label_id,
                "label": "Approve" if label_id == 1 else "Reject",
                "gold": label_id,
                "answer": "Approve" if label_id == 1 else "Reject",
                "has_gold": True,
            },
            "meta": {
                "dataset_id": "australian_credit_uci_statlog_v0",
                "label_col_index": 14,
                "feature_order": [f"A{i}" for i in range(1, 15)],
                "uci_missing_value_doc_ambiguity": True,
                "source_row_order_preserved": True,
            },
        }
        records.append(rec)

    all_clean = OUT_DIR / "australian_credit_all_clean.jsonl"
    with all_clean.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    clean_meta = {
        "dataset_id": "australian_credit_uci_statlog_v0",
        "rows": len(records),
        "columns_total_raw": 15,
        "feature_count": 14,
        "label_col_index": 14,
        "raw_label_counts": dict(raw_counts),
        "normalized_label_counts": {"0": norm_counts[0], "1": norm_counts[1]},
        "raw_label_to_canonical": {"0": "Reject", "1": "Approve"},
        "label_normalization_rule": "binary_0_1_direct",
        "feature_missing_token_count": 0,
        "notes": [
            "Raw row order preserved.",
            "Raw labels are preserved separately from normalized labels.",
            "Attributes A1-A14 are anonymized and semantically opaque.",
            "UCI missing-value documentation ambiguity is preserved in metadata despite no literal '?' tokens in the downloaded .dat file."
        ],
    }
    clean_meta_path = OUT_DIR / "australian_credit_clean_meta.json"
    clean_meta_path.write_text(json.dumps(clean_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote all-clean JSONL: {all_clean}")
    print(f"[DONE] Wrote clean metadata: {clean_meta_path}")
    print("[INFO] rows:", len(records))
    print("[INFO] raw_label_counts:", dict(raw_counts))
    print("[INFO] normalized_label_counts:", {"0": norm_counts[0], "1": norm_counts[1]})

    print("=" * 100)
    print("[FIRST CLEAN EXAMPLE]")
    print(json.dumps(records[0], ensure_ascii=False, indent=2))
    print("=" * 100)

if __name__ == "__main__":
    main()
