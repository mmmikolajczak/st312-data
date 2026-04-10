import ast
import json
from collections import Counter
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/fnxl_sharma2023/raw/release")

SPLIT_FILES = {
    "train": RAW_DIR / "train.csv",
    "dev": RAW_DIR / "dev.csv",
    "test": RAW_DIR / "test.csv",
}
LABEL_COUNT_FILE = RAW_DIR / "allLabelCount.csv"
LABELS_JSON_FILE = RAW_DIR / "labels.json"

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


def parse_list_cell(x):
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        x = x.strip()
        if x == "":
            return []
        try:
            value = ast.literal_eval(x)
        except Exception as e:
            raise ValueError(f"Could not parse list cell: {x[:120]!r}") from e
        if isinstance(value, list):
            return value
        raise ValueError(f"Expected list cell, got {type(value)}")
    raise ValueError(f"Unsupported list-cell type: {type(x)}")


def positive_label_values(seq):
    out = []
    for x in seq:
        if isinstance(x, str):
            s = x.strip()
            if s == "" or s == "O" or s == "0":
                continue
            try:
                xi = int(s)
                if xi > 0:
                    out.append(xi)
            except ValueError:
                out.append(s)
        elif isinstance(x, (int, float)):
            xi = int(x)
            if xi > 0:
                out.append(xi)
    return out


def load_split(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def inspect_split(name: str, df: pd.DataFrame):
    unnamed_cols = [c for c in df.columns if str(c).startswith("Unnamed:")]
    missing_keep = [c for c in KEEP_COLUMNS if c not in df.columns]

    token_lengths = []
    positive_counts = 0
    used_labels = set()
    all_zero_rows = 0

    for _, row in df.iterrows():
        tokens = parse_list_cell(row["tokens"])
        ner_tags = parse_list_cell(row["ner_tags"])

        token_lengths.append(len(tokens))

        pos = positive_label_values(ner_tags)
        positive_counts += len(pos)
        used_labels.update(pos)
        if len(pos) == 0:
            all_zero_rows += 1

    print("=" * 100)
    print(f"[SPLIT] {name}")
    print(f"rows: {len(df)}")
    print(f"columns: {list(df.columns)}")
    print(f"unnamed_cols: {unnamed_cols}")
    print(f"missing_keep_columns: {missing_keep}")
    print(f"positive_labelled_numerals: {positive_counts}")
    print(f"distinct_positive_labels: {len(used_labels)}")
    print(f"all_zero_ner_rows: {all_zero_rows}")
    print(f"token_length_mean: {sum(token_lengths)/len(token_lengths):.4f}")
    print(f"token_length_max: {max(token_lengths)}")
    print(f"unique_companies: {df['company'].nunique(dropna=False)}")
    print(f"unique_files: {df['fileName'].nunique(dropna=False)}")
    print("[sample_row]")
    sample = df.iloc[0].to_dict()
    for k in ["sentence", "tokens", "ner_tags", "numerals-tags"]:
        if k in sample:
            sample[k] = str(sample[k])[:300]
    print(json.dumps(sample, ensure_ascii=False, indent=2)[:2500])
    print()

    return {
        "rows": int(len(df)),
        "unnamed_cols": unnamed_cols,
        "missing_keep_columns": missing_keep,
        "positive_labelled_numerals": int(positive_counts),
        "distinct_positive_labels": int(len(used_labels)),
        "all_zero_ner_rows": int(all_zero_rows),
        "token_length_mean": float(sum(token_lengths)/len(token_lengths)),
        "token_length_max": int(max(token_lengths)),
        "unique_companies": int(df["company"].nunique(dropna=False)),
        "unique_files": int(df["fileName"].nunique(dropna=False)),
        "company_set": set(df["company"].astype(str)),
        "file_set": set(df["fileName"].astype(str)),
        "used_labels": used_labels,
    }


def main():
    split_data = {}
    raw_dfs = {}
    for name, path in SPLIT_FILES.items():
        df = load_split(path)
        raw_dfs[name] = df
        split_data[name] = inspect_split(name, df)

    label_count_df = pd.read_csv(LABEL_COUNT_FILE)
    print("=" * 100)
    print("[LABEL INVENTORY]")
    print(f"allLabelCount rows: {len(label_count_df)}")
    print(f"columns: {list(label_count_df.columns)}")
    freq_col = None
    for c in label_count_df.columns:
        if str(c).lower() in {'count', 'labelcount', 'freq', 'frequency'}:
            freq_col = c
            break
    if freq_col is not None:
        print(f"frequency_col: {freq_col}")
        print(f"min_freq: {label_count_df[freq_col].min()}")
        print(f"max_freq: {label_count_df[freq_col].max()}")
    print("[head]")
    print(label_count_df.head(5).to_string(index=False))
    print()

    labels_json_info = {}
    if LABELS_JSON_FILE.exists():
        with LABELS_JSON_FILE.open("r", encoding="utf-8") as f:
            labels_json = json.load(f)
        labels_json_info["top_level_type"] = type(labels_json).__name__
        if isinstance(labels_json, dict):
            labels_json_info["top_level_keys"] = list(labels_json.keys())[:20]
            labels_json_info["dict_len"] = len(labels_json)
        elif isinstance(labels_json, list):
            labels_json_info["list_len"] = len(labels_json)
            labels_json_info["list_preview"] = labels_json[:10]
    print("=" * 100)
    print("[labels.json SUMMARY]")
    print(json.dumps(labels_json_info, ensure_ascii=False, indent=2))
    print()

    overlap = {}
    split_names = list(SPLIT_FILES.keys())
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            a, b = split_names[i], split_names[j]
            overlap[f"{a}__{b}"] = {
                "company_overlap_count": len(split_data[a]["company_set"] & split_data[b]["company_set"]),
                "file_overlap_count": len(split_data[a]["file_set"] & split_data[b]["file_set"]),
                "company_overlap_preview": sorted(list(split_data[a]["company_set"] & split_data[b]["company_set"]))[:10],
                "file_overlap_preview": sorted(list(split_data[a]["file_set"] & split_data[b]["file_set"]))[:10],
            }

    summary = {
        "dataset_id": "fnxl_sharma2023_v0",
        "split_summaries": {
            k: {
                kk: vv for kk, vv in v.items()
                if kk not in {"company_set", "file_set", "used_labels"}
            }
            for k, v in split_data.items()
        },
        "authoritative_label_inventory_size": int(len(label_count_df)),
        "release_split_overlap_audit": overlap,
        "notes": [
            "Original release split is audited here but will not be used as canonical evaluation if company/file leakage is confirmed.",
            "all_zero_ner_rows are retained in raw preservation but should be flagged in downstream cleaning metadata.",
        ],
    }
    out_path = Path("reports/fnxl_sharma2023/release_audit_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote release audit summary: {out_path}")

if __name__ == "__main__":
    main()
