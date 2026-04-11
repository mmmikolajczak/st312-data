import json
from collections import Counter
from pathlib import Path

import pandas as pd

RAW_CANONICAL = Path("data/gold_commodity_news/raw/canonical/finalDataset_0208.csv")
RAW_DERIVATIVE = Path("data/gold_commodity_news/raw/derivative_reference/gold-dataset-sinha-khandait.csv")
PROCESSED_DIR = Path("data/gold_commodity_news/processed")

CLEAN_CSV = PROCESSED_DIR / "gold_commodity_news_clean.csv"
CLEAN_JSONL = PROCESSED_DIR / "gold_commodity_news_clean.jsonl"
CLEAN_META = PROCESSED_DIR / "gold_commodity_news_clean_meta.json"

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
PRICE_CHILD_COLUMNS = [
    "Direction Up",
    "Direction Constant",
    "Direction Down",
    "PastPrice",
    "FuturePrice",
]


def normalize_url(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def normalize_news(x):
    if pd.isna(x):
        return ""
    return " ".join(str(x).split())


def repair_date_string(x: str):
    s = str(x).strip()
    if s.startswith("0200-"):
        return "2000-" + s[len("0200-"):]
    if s.startswith("0201-"):
        return "2001-" + s[len("0201-"):]
    return s


def duplicated_key_stats(series: pd.Series):
    vc = series.value_counts(dropna=False)
    distinct_duplicated_keys = int((vc > 1).sum())
    rows_involved = int(vc[vc > 1].sum())
    return distinct_duplicated_keys, rows_involved


def main():
    if not RAW_CANONICAL.exists():
        raise SystemExit(f"Missing canonical raw file: {RAW_CANONICAL}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(RAW_CANONICAL)
    raw["__source_row_number"] = range(1, len(raw) + 1)

    raw_exact_duplicates = int(raw.drop(columns="__source_row_number").duplicated().sum())

    headline_dup_keys, headline_dup_rows = duplicated_key_stats(raw["News"].map(normalize_news))
    url_dup_keys, url_dup_rows = duplicated_key_stats(raw["URL"].map(normalize_url))

    raw["date_raw"] = raw["Dates"].astype(str)
    raw["date_norm"] = raw["date_raw"].map(repair_date_string)
    raw["date_repair_applied"] = (raw["date_raw"] != raw["date_norm"]).astype(int)

    raw["date_parsed"] = pd.to_datetime(raw["date_norm"], errors="coerce")
    raw_bad_before = int(pd.to_datetime(raw["date_raw"], errors="coerce").isna().sum())
    raw_bad_after = int(raw["date_parsed"].isna().sum())
    date_repairs_applied = int(raw["date_repair_applied"].sum())

    raw["url_norm"] = raw["URL"].map(normalize_url)
    raw["news_norm"] = raw["News"].map(normalize_news)

    raw["price_or_not_norm"] = raw[PRICE_CHILD_COLUMNS].fillna(0).astype(int).max(axis=1)
    raw["asset_comparison"] = raw["Asset Comparision"].fillna(0).astype(int)

    raw["price_parent_zero_child_active"] = (
        (raw["Price or Not"].fillna(0).astype(int) == 0)
        & (raw["price_or_not_norm"] == 1)
    ).astype(int)

    raw["direction_flag_sum"] = (
        raw[["Direction Up", "Direction Constant", "Direction Down"]]
        .fillna(0).astype(int).sum(axis=1)
    )

    dedup_cols = [c for c in raw.columns if c != "__source_row_number"]
    clean = raw.drop_duplicates(subset=dedup_cols, keep="first").copy()

    removed_exact_duplicates = len(raw) - len(clean)

    clean["date_iso"] = clean["date_parsed"].dt.strftime("%Y-%m-%d")
    clean["date_parse_success"] = clean["date_parsed"].notna().astype(int)

    clean_records = []
    for i, row in enumerate(clean.to_dict(orient="records"), start=1):
        label_raw = {col: int(row[col]) for col in LABEL_COLUMNS}
        rec = {
            "example_id": f"gold_commodity_news_{i:06d}",
            "data": {
                "headline": row["News"],
                "headline_norm": row["news_norm"],
                "url": row["URL"],
                "url_norm": row["url_norm"],
                "date_raw": row["date_raw"],
                "date_norm": row["date_norm"],
                "date_iso": row["date_iso"],
            },
            "label": {
                "labels_raw": label_raw,
                "price_or_not_norm": int(row["price_or_not_norm"]),
                "asset_comparison": int(row["asset_comparison"]),
            },
            "meta": {
                "source": "daittan/gold-commodity-news-and-dimensions",
                "source_row_number": int(row["__source_row_number"]),
                "date_repair_applied": int(row["date_repair_applied"]),
                "date_parse_success": int(row["date_parse_success"]),
                "price_parent_zero_child_active": int(row["price_parent_zero_child_active"]),
                "direction_flag_sum": int(row["direction_flag_sum"]),
            },
        }
        clean_records.append(rec)

    clean.to_csv(CLEAN_CSV, index=False)

    with CLEAN_JSONL.open("w", encoding="utf-8") as f:
        for rec in clean_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": "gold_commodity_news_kaggle_default_v0",
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "raw_exact_duplicate_rows": raw_exact_duplicates,
        "clean_exact_duplicate_rows_removed": int(removed_exact_duplicates),
        "duplicate_audit": {
            "distinct_duplicated_headlines": headline_dup_keys,
            "rows_involved_in_duplicated_headlines": headline_dup_rows,
            "distinct_duplicated_urls": url_dup_keys,
            "rows_involved_in_duplicated_urls": url_dup_rows,
        },
        "date_audit": {
            "raw_unparseable_date_count": raw_bad_before,
            "deterministic_repair_rules": {
                "0200-": "2000-",
                "0201-": "2001-",
            },
            "date_repairs_applied": date_repairs_applied,
            "unparseable_after_repair": raw_bad_after,
            "parsed_success_after_repair_raw_rows": int(raw["date_parsed"].notna().sum()),
            "parsed_success_after_repair_clean_rows": int(clean["date_parse_success"].sum()),
        },
        "label_structure": {
            "raw_label_columns": LABEL_COLUMNS,
            "price_parent_zero_child_active_raw": int(raw["price_parent_zero_child_active"].sum()),
            "price_parent_one_child_inactive_raw": int(
                ((raw["Price or Not"].fillna(0).astype(int) == 1) & (raw["price_or_not_norm"] == 0)).sum()
            ),
            "all_zero_label_rows_raw": int((raw[LABEL_COLUMNS].fillna(0).astype(int).sum(axis=1) == 0).sum()),
            "direction_flag_sum_distribution_raw": {
                str(k): int(v) for k, v in raw["direction_flag_sum"].value_counts().sort_index().to_dict().items()
            },
        },
        "derived_fields": {
            "price_or_not_norm": "max(Direction Up, Direction Constant, Direction Down, PastPrice, FuturePrice)",
            "asset_comparison": "alias of raw Asset Comparision field",
            "date_norm": "deterministically repaired date string prior to parsing",
            "date_iso": "parsed ISO date after deterministic repair",
        },
        "derivative_reference_present": RAW_DERIVATIVE.exists(),
    }

    CLEAN_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote cleaned CSV: {CLEAN_CSV}")
    print(f"[DONE] Wrote cleaned JSONL: {CLEAN_JSONL}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META}")
    print(f"[INFO] raw_rows: {len(raw)}")
    print(f"[INFO] clean_rows: {len(clean)}")
    print(f"[INFO] exact_duplicate_rows_removed: {removed_exact_duplicates}")
    print(f"[INFO] raw_unparseable_date_count: {raw_bad_before}")
    print(f"[INFO] unparseable_after_repair: {raw_bad_after}")


if __name__ == "__main__":
    main()
