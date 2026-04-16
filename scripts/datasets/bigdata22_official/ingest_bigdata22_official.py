from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


DATASET_ID = "bigdata22_official_v0"
SOURCE_REPO_URL = "https://github.com/deeptrade-public/slot"
SOURCE_REPO_NAME = "deeptrade-public/slot"
SOURCE_COMMIT = "1c1a25671d4c81f5fcd45607447225862c308dd5"
PAPER_TITLE = "Accurate Stock Movement Prediction with Self-supervised Learning from Sparse Noisy Tweets(BigData22).pdf"
RAW_DIR = Path("data/bigdata22_official/raw")
PROCESSED_DIR = Path("data/bigdata22_official/processed")
REPORT_DIR = Path("reports/bigdata22_official")
TEMP_CLONE_DIR = Path("/tmp/slot_src")

PAPER_WINDOW_START = date(2019, 7, 5)
PAPER_WINDOW_END = date(2020, 6, 30)
PAPER_WINDOW_DAYS = (PAPER_WINDOW_END - PAPER_WINDOW_START).days + 1
TRAIN_SPLIT_FRACTION = 0.7
VALID_SPLIT_FRACTION = 0.1

LABEL_THRESHOLD_POLICY = "rise if return >= 0.55%; fall if return <= -0.5%; neutral band excluded"
PAPER_PRICE_FEATURE_COLUMNS = [
    "c_open",
    "c_high",
    "c_low",
    "n_close",
    "n_adj_close",
    "adj_sum_5",
    "adj_sum_10",
    "adj_sum_15",
    "adj_sum_20",
    "adj_sum_25",
    "adj_sum_30",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_source_checkout() -> Path:
    if not TEMP_CLONE_DIR.exists():
        subprocess.run(["git", "clone", SOURCE_REPO_URL, str(TEMP_CLONE_DIR)], check=True)
    subprocess.run(["git", "-C", str(TEMP_CLONE_DIR), "fetch", "--all", "--tags"], check=True)
    subprocess.run(["git", "-C", str(TEMP_CLONE_DIR), "checkout", SOURCE_COMMIT], check=True)
    resolved = subprocess.run(
        ["git", "-C", str(TEMP_CLONE_DIR), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if resolved != SOURCE_COMMIT:
        raise RuntimeError(f"Resolved commit {resolved} does not match expected {SOURCE_COMMIT}")
    return TEMP_CLONE_DIR


def copy_top_level_release_files(src_root: Path) -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    copied = {}
    for rel in ["README.md", PAPER_TITLE, "data.zip"]:
        src = src_root / rel
        if not src.exists():
            raise FileNotFoundError(f"Missing required source file: {rel}")
        dst = RAW_DIR / rel
        shutil.copy2(src, dst)
        copied[rel] = dst
    license_paths = sorted(src_root.glob("LICENSE*"))
    for license_path in license_paths:
        dst = RAW_DIR / license_path.name
        shutil.copy2(license_path, dst)
        copied[license_path.name] = dst
    return copied


def extract_archive(zip_path: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(destination)


def summarize_zip_tree(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as zf:
        names = [name for name in zf.namelist() if name and not name.endswith("/")]
    root_counts = Counter(Path(name).parts[0] for name in names)
    return {
        "file_count_by_root": dict(sorted(root_counts.items())),
        "sample_paths": names[:50],
    }


def load_price_rows(price_path: Path) -> list[dict]:
    with price_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty price csv: {price_path}")
    return rows


def load_tweets(tweet_path: Path | None, tweet_date: str) -> list[dict]:
    if tweet_path is None or not tweet_path.exists():
        return []
    tweets = []
    for line in tweet_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            text = parsed.get("text", "")
        except json.JSONDecodeError:
            text = line
        text = " ".join(str(text).split())
        if text:
            tweets.append({"date": tweet_date, "text": text})
    return tweets


def count_nonempty_lines(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def expected_label_from_return(adjusted_close_return: float) -> int:
    if adjusted_close_return >= 0.0055:
        return 1
    if adjusted_close_return <= -0.005:
        return -1
    return 0


def build_split_policy(target_dates: list[str]) -> tuple[dict[str, str], dict]:
    total_dates = len(target_dates)
    train_date_count = int(total_dates * TRAIN_SPLIT_FRACTION)
    valid_date_count = int(total_dates * VALID_SPLIT_FRACTION)
    test_date_count = total_dates - train_date_count - valid_date_count
    if min(train_date_count, valid_date_count, test_date_count) <= 0:
        raise ValueError(f"Invalid split date counts derived from {total_dates} target dates")

    train_dates = target_dates[:train_date_count]
    valid_dates = target_dates[train_date_count : train_date_count + valid_date_count]
    test_dates = target_dates[train_date_count + valid_date_count :]
    split_map = {target_date: "train" for target_date in train_dates}
    split_map.update({target_date: "valid" for target_date in valid_dates})
    split_map.update({target_date: "test" for target_date in test_dates})
    summary = {
        "official_split_files_present": False,
        "split_reconstruction_is_st312_derived": True,
        "paper_only_claim": "chronological_split_without_published_cut_dates",
        "reconstruction_basis": "target_trading_dates",
        "reconstruction_strategy": "chronological_70_10_20_partition_over_sorted_unique_target_trading_dates_after_excluding_neutral_band",
        "paper_window_start": PAPER_WINDOW_START.isoformat(),
        "paper_window_end": PAPER_WINDOW_END.isoformat(),
        "target_trading_dates_total": total_dates,
        "split_target_trading_date_counts": {
            "train": len(train_dates),
            "valid": len(valid_dates),
            "test": len(test_dates),
        },
        "split_target_trading_date_ranges": {
            "train": {"min": train_dates[0], "max": train_dates[-1]},
            "valid": {"min": valid_dates[0], "max": valid_dates[-1]},
            "test": {"min": test_dates[0], "max": test_dates[-1]},
        },
        "notes": [
            "The official archive does not ship split files or split boundary notes.",
            "The paper states only that the split is chronological; it does not publish cut dates.",
            "ST312 therefore derives the train/valid/test split over sorted unique target trading dates within the paper window after excluding neutral-band rows.",
        ],
    }
    return split_map, summary


def current_adjusted_close(row: dict) -> float:
    return float(row["closing_price_for_label"])


def serialize_history_row(row: dict) -> dict:
    return {
        "date": row["date"],
        "c_open": float(row["c_open"]),
        "c_high": float(row["c_high"]),
        "c_low": float(row["c_low"]),
        "n_close": float(row["n_close"]),
        "n_adj_close": float(row["n_adj_close"]),
        "adj_sum_5": float(row["adj_sum_5"]),
        "adj_sum_10": float(row["adj_sum_10"]),
        "adj_sum_15": float(row["adj_sum_15"]),
        "adj_sum_20": float(row["adj_sum_20"]),
        "adj_sum_25": float(row["adj_sum_25"]),
        "adj_sum_30": float(row["adj_sum_30"]),
        "adjusted_close_price": current_adjusted_close(row),
    }


def render_price_history(rows: list[dict]) -> str:
    header = [
        "date",
        "c_open",
        "c_high",
        "c_low",
        "n_close",
        "n_adj_close",
        "adj_sum_5",
        "adj_sum_10",
        "adj_sum_15",
        "adj_sum_20",
        "adj_sum_25",
        "adj_sum_30",
        "adjusted_close_price",
    ]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row[column]) for column in header))
    return "\n".join(lines)


def render_tweets(tweets: list[dict]) -> str:
    if not tweets:
        return "[no local tweets available for the history end date]"
    return "\n".join(f"{tweet['date']}: {tweet['text']}" for tweet in tweets)


def build_processed_row(
    ticker: str,
    row_idx: int,
    rows: list[dict],
    tweet_root: Path,
) -> dict | None:
    row = rows[row_idx]
    target_date = date.fromisoformat(row["date"])
    if target_date < PAPER_WINDOW_START or target_date > PAPER_WINDOW_END:
        return None

    raw_label = int(row["label"])
    if raw_label == 0:
        return None
    if row_idx < 30:
        raise ValueError(f"Insufficient history for {ticker} {row['date']}: need 30 prior rows")

    prev_row = rows[row_idx - 1]
    history_end_date = prev_row["date"]
    history_rows = [serialize_history_row(hist_row) for hist_row in rows[row_idx - 30 : row_idx]]
    tweet_path = tweet_root / history_end_date
    tweets = load_tweets(tweet_path if tweet_path.exists() else None, history_end_date)

    current_price = current_adjusted_close(row)
    prev_price = current_adjusted_close(prev_row)
    adjusted_close_return = (current_price / prev_price) - 1.0

    canonical_label = 1 if raw_label == 1 else 0
    canonical_label_text = "Rise" if raw_label == 1 else "Fall"

    return {
        "example_id": f"{DATASET_ID}__{ticker}__{row['date']}",
        "dataset_id": DATASET_ID,
        "ticker": ticker,
        "target_date": row["date"],
        "history_end_date": history_end_date,
        "price_history_rows": history_rows,
        "price_history_text": render_price_history(history_rows),
        "tweets": tweets,
        "tweets_text": render_tweets(tweets),
        "gold_label": canonical_label,
        "gold_label_text": canonical_label_text,
        "original_release_label": raw_label,
        "adjusted_close_return": adjusted_close_return,
        "adjusted_close_price_target": current_price,
        "adjusted_close_price_prev": prev_price,
        "label_threshold_policy": LABEL_THRESHOLD_POLICY,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "source_path": f"bigdata22/price/{ticker}.csv",
        "source_tweet_path": f"bigdata22/tweet/{ticker}/{history_end_date}" if tweet_path.exists() else None,
        "source_fields_present": sorted(set(row.keys()) | {"tweet.text"}),
    }


def build_processed_rows(raw_extract_root: Path) -> tuple[dict[str, list[dict]], dict]:
    price_dir = raw_extract_root / "bigdata22" / "price"
    tweet_dir = raw_extract_root / "bigdata22" / "tweet"
    if not price_dir.exists() or not tweet_dir.exists():
        raise FileNotFoundError("Expected bigdata22 price/tweet directories are missing from extracted archive")

    price_files = sorted(price_dir.glob("*.csv"))
    if len(price_files) != 50:
        raise ValueError(f"Expected 50 BigData22 price CSVs, found {len(price_files)}")

    processed = {"train": [], "valid": [], "test": []}
    provisional_rows = []
    paper_window_label_counts = Counter()
    paper_window_ticker_row_counts = Counter()
    paper_window_total_rows = 0
    paper_window_with_local_tweets = 0
    source_field_sets = Counter()
    missing_tweet_by_split = Counter()
    tweets_per_split = Counter()
    paper_window_tweet_line_counts_by_ticker = Counter()
    duplicate_ids = set()
    seen_ids = set()
    threshold_total_checked = 0
    threshold_consistent = 0
    threshold_mismatches = []

    for price_path in price_files:
        ticker = price_path.stem
        rows = load_price_rows(price_path)
        ticker_tweet_root = tweet_dir / ticker
        if ticker_tweet_root.exists():
            for tweet_path in sorted(p for p in ticker_tweet_root.iterdir() if p.is_file()):
                try:
                    tweet_date = date.fromisoformat(tweet_path.name)
                except ValueError:
                    continue
                if PAPER_WINDOW_START <= tweet_date <= PAPER_WINDOW_END:
                    paper_window_tweet_line_counts_by_ticker[ticker] += count_nonempty_lines(tweet_path)
        for row_idx in range(len(rows)):
            row = rows[row_idx]
            target = date.fromisoformat(row["date"])
            if PAPER_WINDOW_START <= target <= PAPER_WINDOW_END:
                paper_window_total_rows += 1
                paper_window_label_counts[str(int(row["label"]))] += 1
                paper_window_ticker_row_counts[ticker] += 1
                if row_idx > 0:
                    current_price = current_adjusted_close(row)
                    prev_price = current_adjusted_close(rows[row_idx - 1])
                    adjusted_close_return = (current_price / prev_price) - 1.0
                    expected_label = expected_label_from_return(adjusted_close_return)
                    raw_label = int(row["label"])
                    threshold_total_checked += 1
                    if expected_label == raw_label:
                        threshold_consistent += 1
                    elif len(threshold_mismatches) < 10:
                        threshold_mismatches.append(
                            {
                                "ticker": ticker,
                                "target_date": row["date"],
                                "raw_label": raw_label,
                                "expected_label": expected_label,
                                "adjusted_close_return": adjusted_close_return,
                                "current_adjusted_close": current_price,
                                "previous_adjusted_close": prev_price,
                            }
                        )
            processed_row = build_processed_row(ticker, row_idx, rows, ticker_tweet_root)
            if processed_row is None:
                continue
            if processed_row["example_id"] in seen_ids:
                duplicate_ids.add(processed_row["example_id"])
            seen_ids.add(processed_row["example_id"])
            provisional_rows.append(processed_row)
            source_field_sets[tuple(processed_row["source_fields_present"])] += 1

    if duplicate_ids:
        raise ValueError(f"Duplicate example ids found: {sorted(list(duplicate_ids))[:5]}")

    target_dates = sorted({row["target_date"] for row in provisional_rows})
    split_map, split_policy = build_split_policy(target_dates)
    for row in provisional_rows:
        split = split_map[row["target_date"]]
        row["split"] = split
        processed[split].append(row)
        if row["tweets"]:
            paper_window_with_local_tweets += 1
            tweets_per_split[split] += len(row["tweets"])
        else:
            missing_tweet_by_split[split] += 1

    for split in processed:
        processed[split].sort(key=lambda row: (row["target_date"], row["ticker"]))

    audit = {
        "paper_window_total_stock_dates": paper_window_total_rows,
        "paper_window_calendar_days": PAPER_WINDOW_DAYS,
        "paper_window_trading_dates_with_non_neutral_examples": len(target_dates),
        "paper_window_trading_rows_per_ticker": {
            "min": min(paper_window_ticker_row_counts.values()),
            "max": max(paper_window_ticker_row_counts.values()),
            "counts_by_ticker": dict(sorted(paper_window_ticker_row_counts.items())),
        },
        "paper_window_label_counts": dict(sorted(paper_window_label_counts.items())),
        "paper_window_non_neutral_examples": sum(len(rows) for rows in processed.values()),
        "paper_window_examples_with_local_tweets": paper_window_with_local_tweets,
        "paper_window_tweet_line_counts": {
            "total": sum(paper_window_tweet_line_counts_by_ticker.values()),
            "counts_by_ticker": dict(sorted(paper_window_tweet_line_counts_by_ticker.items())),
        },
        "source_field_sets_observed": [
            {"fields": list(fields), "count": count}
            for fields, count in source_field_sets.items()
        ],
        "missing_local_tweet_examples_by_split": dict(sorted(missing_tweet_by_split.items())),
        "tweet_line_counts_by_split": dict(sorted(tweets_per_split.items())),
        "split_policy": split_policy,
        "label_threshold_consistency_audit": {
            "total_checked_rows": threshold_total_checked,
            "threshold_consistent_rows": threshold_consistent,
            "mismatch_count": threshold_total_checked - threshold_consistent,
            "mismatch_examples": threshold_mismatches,
            "neutral_band_treatment": "Expected label 0 is treated as the paper-defined neutral band and is excluded from the canonical binary task.",
            "note": "This audit compares the raw release label against the label implied by the reconstructed adjusted-close return and the paper thresholds.",
        },
    }
    return processed, audit


def main() -> None:
    src_root = ensure_source_checkout()
    copied_files = copy_top_level_release_files(src_root)
    archive_path = copied_files["data.zip"]
    raw_extract_root = RAW_DIR / "extracted"
    extract_archive(archive_path, raw_extract_root)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    processed, audit = build_processed_rows(raw_extract_root)
    split_counts = {split: len(rows) for split, rows in processed.items()}
    class_counts = {
        split: dict(sorted(Counter(row["gold_label_text"] for row in rows).items()))
        for split, rows in processed.items()
    }
    for split, rows in processed.items():
        write_jsonl(PROCESSED_DIR / f"{split}.jsonl", rows)

    label_inventory = {
        "dataset_id": DATASET_ID,
        "labels": [
            {"canonical_id": 1, "text": "Rise", "original_release_label": 1},
            {"canonical_id": 0, "text": "Fall", "original_release_label": -1},
        ],
        "neutral_band_policy": "Rows with original label 0 are excluded from the canonical binary task.",
        "label_threshold_policy": LABEL_THRESHOLD_POLICY,
    }
    write_json(PROCESSED_DIR / "label_inventory.json", label_inventory)

    zip_summary = summarize_zip_tree(archive_path)
    price_sample_rows = load_price_rows(raw_extract_root / "bigdata22" / "price" / "AAPL.csv")[:3]
    split_policy = audit["split_policy"]
    observed_target_trading_dates = audit["paper_window_trading_dates_with_non_neutral_examples"]
    raw_schema_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "archive_contains_multiple_families": len(zip_summary["file_count_by_root"]) > 1,
        "archive_top_level_families": sorted(zip_summary["file_count_by_root"].keys()),
        "archive_file_count_by_root": zip_summary["file_count_by_root"],
        "bigdata22_only_canonical_scope_for_this_module": True,
        "explicit_split_files_present": False,
        "labels_materialized_in_release": True,
        "price_row_columns": list(price_sample_rows[0].keys()),
        "tweet_line_schema": {"text": "string json per line"},
        "split_reconstruction_note": "The official archive does not ship split files or boundary dates. The paper states only that the split is chronological, so ST312 derives a documented train/valid/test reconstruction over sorted unique target trading dates inside the paper window after excluding neutral-band rows.",
        "paper_window": {
            "start_date": PAPER_WINDOW_START.isoformat(),
            "end_date": PAPER_WINDOW_END.isoformat(),
            "calendar_days": PAPER_WINDOW_DAYS,
            "trading_rows_per_ticker": audit["paper_window_trading_rows_per_ticker"],
            "observed_non_neutral_target_trading_dates": audit["paper_window_trading_dates_with_non_neutral_examples"],
            "observed_tweet_line_counts": audit["paper_window_tweet_line_counts"],
        },
        "split_policy": {
            "split_reconstruction_is_st312_derived": split_policy["split_reconstruction_is_st312_derived"],
            "reconstruction_basis": split_policy["reconstruction_basis"],
            "paper_only_claim": split_policy["paper_only_claim"],
            "reconstruction_strategy": split_policy["reconstruction_strategy"],
            "split_target_trading_date_counts": split_policy["split_target_trading_date_counts"],
            "split_target_trading_date_ranges": split_policy["split_target_trading_date_ranges"],
        },
        "non_canonical_wrapper_note": {
            "wrapper_family": "FinBen/OpenFinLLM derived prompt surface",
            "note": "Derived wrappers may exist, but this canonical ingest and audit are computed only from the official slot release archive."
        },
    }
    write_json(REPORT_DIR / "raw_schema_summary.json", raw_schema_summary)

    audit_report = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "split_counts": split_counts,
        "class_counts_by_split": class_counts,
        "split_target_date_ranges": {
            split: {
                "min": rows[0]["target_date"] if rows else None,
                "max": rows[-1]["target_date"] if rows else None,
            }
            for split, rows in processed.items()
        },
        "release_window_notes": [
            "The official archive contains extra dates outside the paper benchmark window; ST312 restricts the canonical BigData22 module to the paper window 2019-07-05 through 2020-06-30.",
            f"The paper's 362-day figure matches the inclusive calendar span of the benchmark window; the release yields {observed_target_trading_dates} non-neutral target trading dates in that same window.",
            "The official archive does not ship split files, so ST312 derives a chronological split reconstruction over sorted unique target trading dates and documents that policy explicitly in this audit.",
        ],
        **audit,
    }
    write_json(REPORT_DIR / "ingest_audit.json", audit_report)

    raw_file_manifest = {}
    for path in sorted(p for p in RAW_DIR.rglob("*") if p.is_file()):
        rel = path.relative_to(RAW_DIR).as_posix()
        raw_file_manifest[rel] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    license_files = sorted(path.name for path in RAW_DIR.glob("LICENSE*"))
    download_meta = {
        "source_repo": SOURCE_REPO_NAME,
        "source_repo_url": SOURCE_REPO_URL,
        "source_commit": SOURCE_COMMIT,
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "archive_filename": "data.zip",
        "archive_sha256": sha256_file(archive_path),
        "source_paths": ["README.md", PAPER_TITLE, "data.zip"],
        "file_sizes_bytes": {path: meta["size_bytes"] for path, meta in raw_file_manifest.items()},
        "sha256_by_file": {path: meta["sha256"] for path, meta in raw_file_manifest.items()},
        "extracted_file_tree_summary": zip_summary,
        "license_files_found": license_files,
        "download_method": "git_clone_checkout_copy_zip_extract",
        "notes": [
            "The public repo surface is lightweight; schema and evaluator fidelity partly rely on the paper PDF bundled in the repo.",
            "The archive contains BigData22 together with ACL18 and CIKM18; this module canonically ingests only BigData22 while preserving the full extracted archive for provenance.",
            "The release does not ship explicit split files or boundary dates; ST312 reconstructs a chronological split over the official paper window and documents that reconstruction explicitly.",
            "Publication carries an upstream rights caution because the repo surface does not expose a clear dataset redistribution license for the tweets and market data.",
        ],
    }
    write_json(RAW_DIR / "download_meta.json", download_meta)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "paper_window_start": PAPER_WINDOW_START.isoformat(),
        "paper_window_end": PAPER_WINDOW_END.isoformat(),
        "published_splits": ["train", "valid", "test"],
        "row_counts": split_counts,
        "class_counts_by_split": class_counts,
        "total_rows": sum(split_counts.values()),
        "split_policy": split_policy,
        "label_inventory_file": "data/bigdata22_official/processed/label_inventory.json",
        "publication_rights_caution": True,
    }
    write_json(PROCESSED_DIR / "ingest_summary.json", ingest_summary)

    print(f"[DONE] Ingested {DATASET_ID}")
    print(f"[INFO] source_commit={SOURCE_COMMIT}")
    print(f"[INFO] split_counts={split_counts}")


if __name__ == "__main__":
    main()
