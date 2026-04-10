import ast
import json
from collections import Counter
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/fnxl_sharma2023/raw/release")
PROCESSED_DIR = Path("data/fnxl_sharma2023/processed")

SPLIT_FILES = {
    "train": RAW_DIR / "train.csv",
    "dev": RAW_DIR / "dev.csv",
    "test": RAW_DIR / "test.csv",
}
LABEL_COUNT_FILE = RAW_DIR / "allLabelCount.csv"
LABELS_JSON_FILE = RAW_DIR / "labels.json"

AGGREGATE_PATH = PROCESSED_DIR / "fnxl_release_raw_aggregate.jsonl"
CLEAN_META_PATH = PROCESSED_DIR / "fnxl_clean_meta.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "fnxl_label_inventory.json"

KEEP_COLUMNS = [
    "index",
    "sentence",
    "numerals-tags",
    "company",
    "docEndDate",
    "docType",
    "fileName",
    "year",
    "finer_masked_sentence",
    "finer_num_sentence",
    "finer_shape_sentence",
    "ner_tags",
    "tokens",
]


def parse_python_literal(x):
    if pd.isna(x):
        return None
    if isinstance(x, (list, dict)):
        return x
    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None
        return ast.literal_eval(s)
    return x


def positive_mentions(tokens, ner_tags):
    out = []
    seen = set()
    duplicate_exact_pair_count = 0

    for i, tag in enumerate(ner_tags):
        try:
            tag_int = int(tag)
        except Exception:
            continue
        if tag_int > 0:
            pair = (i, tag_int)
            if pair in seen:
                duplicate_exact_pair_count += 1
                continue
            seen.add(pair)
            out.append({
                "token_index": i,
                "token": tokens[i] if i < len(tokens) else None,
                "label_id": tag_int,
            })

    return out, duplicate_exact_pair_count


def normalize_company(x, file_name: str) -> str:
    if pd.isna(x):
        x = ""
    s = str(x).strip()
    if s == "":
        return f"__MISSING_COMPANY__::{file_name}"
    return s


def load_label_inventory():
    df = pd.read_csv(LABEL_COUNT_FILE, header=None)
    if df.shape[1] != 3:
        raise ValueError(f"Expected 3 columns in allLabelCount.csv, got shape {df.shape}")
    df.columns = ["rank", "label", "count"]
    df["rank"] = pd.to_numeric(df["rank"], errors="raise").astype(int)
    df["count"] = pd.to_numeric(df["count"], errors="raise").astype(int)
    return df


def load_labels_json_summary(authoritative_labels):
    if not LABELS_JSON_FILE.exists():
        return {"exists": False}

    with LABELS_JSON_FILE.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    base_labels = set()
    if isinstance(obj, dict):
        for k in obj.keys():
            if k == "O":
                continue
            if k.startswith("B-") or k.startswith("I-"):
                base_labels.add(k[2:])
            else:
                base_labels.add(k)

    return {
        "exists": True,
        "top_level_type": type(obj).__name__,
        "n_entries": len(obj) if hasattr(obj, "__len__") else None,
        "n_base_labels_from_labels_json": len(base_labels),
        "extra_base_labels_vs_authoritative_inventory": sorted(base_labels - authoritative_labels)[:50],
        "missing_base_labels_vs_authoritative_inventory": sorted(authoritative_labels - base_labels)[:50],
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    label_df = load_label_inventory()
    authoritative_labels = set(label_df["label"].astype(str))
    labels_json_summary = load_labels_json_summary(authoritative_labels)

    split_stats = {}
    aggregate_records = []

    release_company_sets = {}
    release_file_sets = {}

    global_label_counts = Counter()
    total_positive_mentions = 0
    total_duplicate_exact_pairs_removed = 0

    for split_name, path in SPLIT_FILES.items():
        if not path.exists():
            raise FileNotFoundError(path)

        df = pd.read_csv(path)
        unnamed_cols = [c for c in df.columns if str(c).startswith("Unnamed:")]
        df = df.drop(columns=unnamed_cols)

        missing_keep = [c for c in KEEP_COLUMNS if c not in df.columns]
        if missing_keep:
            raise ValueError(f"{split_name}: missing required columns: {missing_keep}")

        df = df[KEEP_COLUMNS].copy()

        rows = 0
        all_zero_rows = 0
        used_labels = set()
        pos_mentions = 0
        companies = set()
        files = set()
        split_duplicate_exact_pairs_removed = 0

        for local_row_idx, row in enumerate(df.to_dict(orient="records"), start=1):
            tokens = parse_python_literal(row["tokens"]) or []
            ner_tags = parse_python_literal(row["ner_tags"]) or []
            numerals_tags = parse_python_literal(row["numerals-tags"]) or {}

            if not isinstance(tokens, list):
                raise ValueError(f"{split_name} row {local_row_idx}: tokens not a list")
            if not isinstance(ner_tags, list):
                raise ValueError(f"{split_name} row {local_row_idx}: ner_tags not a list")
            if len(tokens) != len(ner_tags):
                raise ValueError(
                    f"{split_name} row {local_row_idx}: len(tokens)={len(tokens)} != len(ner_tags)={len(ner_tags)}"
                )

            file_name = str(row["fileName"])
            company_group_key = normalize_company(row["company"], file_name)
            mentions, dup_removed = positive_mentions(tokens, ner_tags)
            split_duplicate_exact_pairs_removed += dup_removed
            total_duplicate_exact_pairs_removed += dup_removed

            pos_ids = [m["label_id"] for m in mentions]

            if len(pos_ids) == 0:
                all_zero_rows += 1
            pos_mentions += len(pos_ids)
            used_labels.update(pos_ids)
            global_label_counts.update(pos_ids)
            total_positive_mentions += len(pos_ids)

            companies.add(company_group_key)
            files.add(file_name)

            rec = {
                "example_id": f"fnxl_release_{split_name}_{local_row_idx:06d}",
                "data": {
                    "sentence": row["sentence"],
                    "tokens": tokens,
                    "finer_masked_sentence": parse_python_literal(row["finer_masked_sentence"]) or [],
                    "finer_num_sentence": parse_python_literal(row["finer_num_sentence"]) or [],
                    "finer_shape_sentence": parse_python_literal(row["finer_shape_sentence"]) or [],
                },
                "label": {
                    "ner_tags": [int(x) for x in ner_tags],
                    "positive_mentions": mentions,
                    "n_positive_mentions": len(mentions),
                    "all_zero_ner": len(mentions) == 0,
                },
                "meta": {
                    "release_split": split_name,
                    "raw_index": row["index"],
                    "release_row_number": local_row_idx,
                    "company": None if pd.isna(row["company"]) else str(row["company"]),
                    "company_group_key": company_group_key,
                    "docEndDate": None if pd.isna(row["docEndDate"]) else str(row["docEndDate"]),
                    "docType": None if pd.isna(row["docType"]) else str(row["docType"]),
                    "fileName": file_name,
                    "year": None if pd.isna(row["year"]) else int(row["year"]),
                    "numerals_tags": numerals_tags,
                },
            }
            aggregate_records.append(rec)
            rows += 1

        split_stats[split_name] = {
            "rows": rows,
            "all_zero_ner_rows": all_zero_rows,
            "positive_labelled_numerals": pos_mentions,
            "distinct_positive_labels": len(used_labels),
            "unique_companies": len(companies),
            "unique_files": len(files),
            "dropped_unnamed_columns": unnamed_cols,
            "duplicate_exact_pairs_removed": split_duplicate_exact_pairs_removed,
        }
        release_company_sets[split_name] = companies
        release_file_sets[split_name] = files

    overlap = {}
    split_names = list(SPLIT_FILES.keys())
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            a, b = split_names[i], split_names[j]
            overlap[f"{a}__{b}"] = {
                "company_overlap_count": len(release_company_sets[a] & release_company_sets[b]),
                "file_overlap_count": len(release_file_sets[a] & release_file_sets[b]),
                "company_overlap_preview": sorted(list(release_company_sets[a] & release_company_sets[b]))[:10],
                "file_overlap_preview": sorted(list(release_file_sets[a] & release_file_sets[b]))[:10],
            }

    with AGGREGATE_PATH.open("w", encoding="utf-8") as f:
        for rec in aggregate_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    label_inventory_obj = {
        "dataset_id": "fnxl_sharma2023_v0",
        "authoritative_inventory_size": int(len(label_df)),
        "labels": [
            {
                "rank": int(r["rank"]),
                "label": str(r["label"]),
                "count": int(r["count"]),
            }
            for _, r in label_df.iterrows()
        ],
    }
    LABEL_INVENTORY_PATH.write_text(json.dumps(label_inventory_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    clean_meta = {
        "dataset_id": "fnxl_sharma2023_v0",
        "aggregate_rows": len(aggregate_records),
        "split_summaries": split_stats,
        "release_split_overlap_audit": overlap,
        "authoritative_label_inventory_size": int(len(label_df)),
        "authoritative_label_frequency_min": int(label_df["count"].min()),
        "authoritative_label_frequency_max": int(label_df["count"].max()),
        "labels_json_summary": labels_json_summary,
        "global_positive_mentions": int(total_positive_mentions),
        "global_distinct_used_labels": int(len(global_label_counts)),
        "total_duplicate_exact_pairs_removed": int(total_duplicate_exact_pairs_removed),
        "notes": [
            "Raw train/dev/test release was aggregated with release_split preserved.",
            "allLabelCount.csv was read as headerless authoritative inventory.",
            "Exact duplicate positive (token_index, label_id) pairs were removed during cleaning.",
            "Original release split exhibits leakage if company/file overlap counts above are non-zero.",
            "Canonical pipeline split will be rebuilt in a later step as company/file-disjoint train/test.",
        ],
    }
    CLEAN_META_PATH.write_text(json.dumps(clean_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote aggregate JSONL: {AGGREGATE_PATH}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META_PATH}")
    print(f"[DONE] Wrote authoritative label inventory: {LABEL_INVENTORY_PATH}")
    print(f"[INFO] aggregate_rows: {len(aggregate_records)}")
    print(f"[INFO] authoritative_label_inventory_size: {len(label_df)}")
    print(f"[INFO] global_positive_mentions: {total_positive_mentions}")
    print(f"[INFO] global_distinct_used_labels: {len(global_label_counts)}")
    print(f"[INFO] total_duplicate_exact_pairs_removed: {total_duplicate_exact_pairs_removed}")


if __name__ == "__main__":
    main()
