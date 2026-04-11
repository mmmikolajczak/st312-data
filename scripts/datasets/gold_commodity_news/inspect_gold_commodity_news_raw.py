import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

CANONICAL_PATH = Path("data/gold_commodity_news/raw/canonical/finalDataset_0208.csv")
DERIVATIVE_PATH = Path("data/gold_commodity_news/raw/derivative_reference/gold-dataset-sinha-khandait.csv")
REPORT_PATH = Path("reports/gold_commodity_news/raw_audit_summary.json")

LABEL_COLUMNS = [
    "Price or Not",
    "Direction Up",
    "Direction Constant",
    "Direction Down",
    "PastPrice",
    "FuturePrice",
    "PastNews",
    "FutureNews",
    "Asset Comparision",
]

DERIVATIVE_COLUMNS_EXPECTED = [
    "Dates",
    "URL",
    "News",
    "Price Direction Up",
    "Price Direction Constant",
    "Price Direction Down",
    "Asset Comparision",
    "Past Information",
    "Future Information",
    "Price Sentiment",
]


def normalize_url(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def normalize_news(x):
    if pd.isna(x):
        return ""
    return " ".join(str(x).split())


def malformed_date_preview(values, n=25):
    vals = [str(v) for v in values if pd.notna(v)]
    parsed = pd.to_datetime(pd.Series(vals), errors="coerce")
    bad = [v for v, p in zip(vals, parsed) if pd.isna(p)]
    return bad[:n], len(bad)


def leading_pattern_counts(values):
    c = Counter()
    for v in values:
        s = str(v)
        if s.startswith("0200-"):
            c["0200-"] += 1
        elif s.startswith("0201-"):
            c["0201-"] += 1
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            c["iso_like"] += 1
        else:
            c["other"] += 1
    return dict(c)


def main():
    if not CANONICAL_PATH.exists():
        raise SystemExit(f"Missing canonical raw file: {CANONICAL_PATH}")

    df = pd.read_csv(CANONICAL_PATH)

    missing_counts = {col: int(df[col].isna().sum()) for col in df.columns}
    exact_duplicate_rows = int(df.duplicated().sum())
    duplicated_headline_rows = int(df["News"].duplicated(keep=False).sum())
    duplicated_url_rows = int(df["URL"].duplicated(keep=False).sum())

    raw_date_preview, raw_bad_date_count = malformed_date_preview(df["Dates"].tolist())
    raw_date_patterns = leading_pattern_counts(df["Dates"].tolist())

    label_positive_counts = {col: int(df[col].fillna(0).astype(int).sum()) for col in LABEL_COLUMNS}
    all_zero_label_rows = int((df[LABEL_COLUMNS].fillna(0).astype(int).sum(axis=1) == 0).sum())

    price_child_cols = [
        "Direction Up",
        "Direction Constant",
        "Direction Down",
        "PastPrice",
        "FuturePrice",
    ]
    child_active = df[price_child_cols].fillna(0).astype(int).sum(axis=1) > 0

    price_parent_zero_child_active = int(((df["Price or Not"].fillna(0).astype(int) == 0) & child_active).sum())
    price_parent_one_child_inactive = int(((df["Price or Not"].fillna(0).astype(int) == 1) & (~child_active)).sum())
    news_labels_while_price_parent_one = int(
        (
            (df["Price or Not"].fillna(0).astype(int) == 1)
            & (
                (df["PastNews"].fillna(0).astype(int) == 1)
                | (df["FutureNews"].fillna(0).astype(int) == 1)
            )
        ).sum()
    )

    direction_sum_dist = (
        df[["Direction Up", "Direction Constant", "Direction Down"]]
        .fillna(0)
        .astype(int)
        .sum(axis=1)
        .value_counts()
        .sort_index()
        .to_dict()
    )

    summary = {
        "dataset_id": "gold_commodity_news_kaggle_default_v0",
        "canonical_raw": {
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "columns": list(df.columns),
            "missing_counts": missing_counts,
        },
        "duplicate_audit": {
            "exact_duplicate_rows": exact_duplicate_rows,
            "duplicated_headline_rows": duplicated_headline_rows,
            "duplicated_url_rows": duplicated_url_rows,
        },
        "date_audit": {
            "raw_unparseable_date_count": raw_bad_date_count,
            "leading_pattern_counts": raw_date_patterns,
            "raw_unparseable_date_preview": raw_date_preview,
        },
        "label_structure": {
            "label_positive_counts": label_positive_counts,
            "all_zero_label_rows": all_zero_label_rows,
            "price_parent_zero_child_active": price_parent_zero_child_active,
            "price_parent_one_child_inactive": price_parent_one_child_inactive,
            "news_labels_while_price_parent_one": news_labels_while_price_parent_one,
            "direction_flag_sum_distribution": {str(k): int(v) for k, v in direction_sum_dist.items()},
        },
    }

    if DERIVATIVE_PATH.exists():
        ddf = pd.read_csv(DERIVATIVE_PATH)
        summary["derivative_reference"] = {
            "exists": True,
            "shape": [int(ddf.shape[0]), int(ddf.shape[1])],
            "columns": list(ddf.columns),
            "columns_match_expected": list(ddf.columns) == DERIVATIVE_COLUMNS_EXPECTED,
        }
    else:
        summary["derivative_reference"] = {"exists": False}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 100)
    print("[CANONICAL RAW SUMMARY]")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("missing_counts:", missing_counts)
    print()
    print("[DUPLICATE AUDIT]")
    print("exact_duplicate_rows:", exact_duplicate_rows)
    print("duplicated_headline_rows:", duplicated_headline_rows)
    print("duplicated_url_rows:", duplicated_url_rows)
    print()
    print("[DATE AUDIT]")
    print("raw_unparseable_date_count:", raw_bad_date_count)
    print("leading_pattern_counts:", raw_date_patterns)
    print("raw_unparseable_date_preview:", raw_date_preview[:15])
    print()
    print("[LABEL POSITIVE COUNTS]")
    print(json.dumps(label_positive_counts, ensure_ascii=False, indent=2))
    print("all_zero_label_rows:", all_zero_label_rows)
    print("price_parent_zero_child_active:", price_parent_zero_child_active)
    print("price_parent_one_child_inactive:", price_parent_one_child_inactive)
    print("news_labels_while_price_parent_one:", news_labels_while_price_parent_one)
    print("direction_flag_sum_distribution:", {str(k): int(v) for k, v in direction_sum_dist.items()})
    print()
    if summary["derivative_reference"]["exists"]:
        print("[DERIVATIVE REFERENCE]")
        print(json.dumps(summary["derivative_reference"], ensure_ascii=False, indent=2))
        print()
    print(f"[DONE] Wrote raw audit summary: {REPORT_PATH}")


if __name__ == "__main__":
    main()
