from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATASET_ID = "stocknet_acl18_paper_v0"
SOURCE_REPO_NAME = "yumoxu/stocknet-dataset"
SOURCE_REPO_URL = "https://github.com/yumoxu/stocknet-dataset"
SOURCE_COMMIT = "330708b5ddc359961078bef469f43f48992fd6e4"
PAPER_CITATION = "Xu & Cohen (ACL 2018)"
TEMP_CLONE_DIR = Path("/tmp/stocknet_acl18_source")

RAW_DIR = Path("data/stocknet_acl18_paper/raw")
SOURCE_SNAPSHOT_DIR = RAW_DIR / "source_snapshot"
RAW_DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
RAW_SOURCE_CHECKSUMS_PATH = RAW_DIR / "source_snapshot_checksums.sha256"
PROCESSED_DIR = Path("data/stocknet_acl18_paper/processed")
REPORT_DIR = Path("reports/stocknet_acl18_paper")
RAW_SCHEMA_SUMMARY_PATH = REPORT_DIR / "raw_schema_summary.json"
RECONSTRUCTION_AUDIT_PATH = REPORT_DIR / "reconstruction_audit.json"
TRAIN_PATH = PROCESSED_DIR / "train.jsonl"
DEV_PATH = PROCESSED_DIR / "dev.jsonl"
TEST_PATH = PROCESSED_DIR / "test.jsonl"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"

TRAIN_START = "2014-01-01"
TRAIN_END = "2015-08-01"
DEV_START = "2015-08-01"
DEV_END = "2015-10-01"
TEST_START = "2015-10-01"
TEST_END = "2016-01-01"
CALENDAR_LAG_DAYS = 5
NEUTRAL_BAND_LOWER = -0.005
NEUTRAL_BAND_UPPER = 0.0055
EXPECTED_SPLIT_COUNTS = {"train": 20339, "dev": 2555, "test": 3720}
EXPECTED_TOTAL = 26614
UPSTREAM_RIGHTS_NOTE = (
    "Original source repository is MIT-licensed. The released corpus includes tweet-derived content collected "
    "under Twitter's official license and price data sourced from Yahoo Finance; downstream users should review "
    "applicable platform/source terms before reuse."
)
RECONSTRUCTION_POLICY_NOTE = (
    "Exact paper counts are reproducible from the official StockNet release when preserving the paper's split "
    "boundaries, 5-day alignment, and asymmetric thresholding. A stricter hard tweet-presence filter would drop "
    "the release to 18,695 samples across every official dataset snapshot, so ST312 treats that line in the paper "
    "as a documented source inconsistency rather than a canonical retention rule."
)


@dataclass
class PriceRow:
    date: datetime.date
    movement_percent: float
    open_norm: float
    high_norm: float
    low_norm: float
    close_norm: float
    volume: float
    raw_open: float | None
    raw_high: float | None
    raw_low: float | None
    raw_close: float | None
    raw_adj_close: float | None
    raw_volume: float | None


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


def iso_date(d: datetime.date) -> str:
    return d.isoformat()


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
        raise RuntimeError(f"Resolved StockNet source commit {resolved} does not match expected {SOURCE_COMMIT}")
    return TEMP_CLONE_DIR


def copy_source_snapshot(src_root: Path) -> None:
    if SOURCE_SNAPSHOT_DIR.exists():
        shutil.rmtree(SOURCE_SNAPSHOT_DIR)
    SOURCE_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for rel in ["README.md", "LICENSE", "StockTable", "appendix_table_of_target_stocks.pdf", "price", "tweet"]:
        src = src_root / rel
        dst = SOURCE_SNAPSHOT_DIR / rel
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def write_source_checksums(snapshot_root: Path) -> dict[str, str]:
    rel_to_sha: dict[str, str] = {}
    lines = []
    for path in sorted(p for p in snapshot_root.rglob("*") if p.is_file()):
        rel = path.relative_to(snapshot_root).as_posix()
        digest = sha256_file(path)
        rel_to_sha[rel] = digest
        lines.append(f"{digest}  {rel}")
    RAW_SOURCE_CHECKSUMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_SOURCE_CHECKSUMS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rel_to_sha


def load_preprocessed_tweets(tweet_file: Path) -> list[str]:
    if not tweet_file.exists():
        return []
    texts: list[str] = []
    with tweet_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            raw_text = msg.get("text", "")
            if isinstance(raw_text, list):
                text = " ".join(str(token) for token in raw_text).strip()
            else:
                text = " ".join(str(raw_text).split())
            if text:
                texts.append(text)
    return texts


def split_for_target_date(target_date: str) -> str | None:
    if TRAIN_START <= target_date < TRAIN_END:
        return "train"
    if DEV_START <= target_date < DEV_END:
        return "dev"
    if TEST_START <= target_date < TEST_END:
        return "test"
    return None


def label_int_from_movement(movement_percent: float) -> int:
    return 0 if movement_percent <= 1e-7 else 1


def label_text(label_int: int) -> str:
    return "Rise" if label_int == 1 else "Fall"


def raw_price_dict(row: PriceRow) -> dict:
    return {
        "date": iso_date(row.date),
        "open": row.raw_open,
        "high": row.raw_high,
        "low": row.raw_low,
        "close": row.raw_close,
        "adj_close": row.raw_adj_close,
        "volume": row.raw_volume,
    }


def preprocessed_price_dict(row: PriceRow) -> dict:
    return {
        "date": iso_date(row.date),
        "movement_percent": row.movement_percent,
        "open_norm": row.open_norm,
        "high_norm": row.high_norm,
        "low_norm": row.low_norm,
        "close_norm": row.close_norm,
        "volume": row.volume,
    }


def load_stock_price_rows(snapshot_root: Path, symbol: str) -> list[PriceRow]:
    raw_rows: dict[str, dict] = {}
    with (snapshot_root / "price" / "raw" / f"{symbol}.csv").open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw_rows[row["Date"]] = row

    rows: list[PriceRow] = []
    with (snapshot_root / "price" / "preprocessed" / f"{symbol}.txt").open("r", encoding="utf-8") as handle:
        for line in handle:
            date_str, movement_percent, open_norm, high_norm, low_norm, close_norm, volume = line.strip().split("\t")
            raw_row = raw_rows.get(date_str, {})
            rows.append(
                PriceRow(
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    movement_percent=float(movement_percent),
                    open_norm=float(open_norm),
                    high_norm=float(high_norm),
                    low_norm=float(low_norm),
                    close_norm=float(close_norm),
                    volume=float(volume),
                    raw_open=float(raw_row["Open"]) if raw_row.get("Open") not in {None, "null"} else None,
                    raw_high=float(raw_row["High"]) if raw_row.get("High") not in {None, "null"} else None,
                    raw_low=float(raw_row["Low"]) if raw_row.get("Low") not in {None, "null"} else None,
                    raw_close=float(raw_row["Close"]) if raw_row.get("Close") not in {None, "null"} else None,
                    raw_adj_close=float(raw_row["Adj Close"]) if raw_row.get("Adj Close") not in {None, "null"} else None,
                    raw_volume=float(raw_row["Volume"]) if raw_row.get("Volume") not in {None, "null"} else None,
                )
            )
    rows.sort(key=lambda row: row.date)
    return rows


def build_sample(symbol: str, rows: list[PriceRow], target_index: int, tweet_root: Path) -> tuple[dict | None, str]:
    target_row = rows[target_index]
    target_date = iso_date(target_row.date)
    split = split_for_target_date(target_date)
    if split is None:
        return None, "outside_split_window"

    lag_window_start = target_row.date - timedelta(days=CALENDAR_LAG_DAYS - 1)
    eligible_indices_rev: list[int] = []
    j = target_index
    while j >= 0 and rows[j].date >= lag_window_start:
        eligible_indices_rev.append(j)
        j -= 1
    eligible_indices = list(reversed(eligible_indices_rev))
    if j < 0:
        return None, "insufficient_history"

    main_mv = target_row.movement_percent
    if NEUTRAL_BAND_LOWER <= main_mv < NEUTRAL_BAND_UPPER:
        return None, "middle_band"

    trading_day_rows = [rows[idx] for idx in eligible_indices]
    price_feature_rows = [rows[j], *trading_day_rows[:-1]]
    trading_dates = [row.date for row in trading_day_rows]
    aligned_tweets = [[] for _ in trading_day_rows]
    aligned_calendar_dates = [[] for _ in trading_day_rows]

    total_lag_tweets = 0
    calendar_date = target_row.date - timedelta(days=CALENDAR_LAG_DAYS)
    calendar_end = target_row.date - timedelta(days=1)
    while calendar_date <= calendar_end:
        tweet_file = tweet_root / iso_date(calendar_date)
        texts = load_preprocessed_tweets(tweet_file)
        if texts:
            total_lag_tweets += len(texts)
            for day_index, trading_date in enumerate(trading_dates):
                if calendar_date < trading_date:
                    aligned_tweets[day_index].extend(texts)
                    aligned_calendar_dates[day_index].append(iso_date(calendar_date))
                    break
        calendar_date += timedelta(days=1)

    labels = [label_int_from_movement(row.movement_percent) for row in trading_day_rows]
    aligned_days = []
    auxiliary_targets = []
    for day_index, (trading_row, feature_row) in enumerate(zip(trading_day_rows, price_feature_rows), start=1):
        aligned_days.append(
            {
                "day_index": day_index,
                "date": iso_date(trading_row.date),
                "is_target_day": day_index == len(trading_day_rows),
                "tweet_calendar_dates": aligned_calendar_dates[day_index - 1],
                "tweets": aligned_tweets[day_index - 1],
                "tweet_count": len(aligned_tweets[day_index - 1]),
                "price_feature_date": iso_date(feature_row.date),
                "price_features_preprocessed": preprocessed_price_dict(feature_row),
                "price_features_raw": raw_price_dict(feature_row),
            }
        )
        if day_index != len(trading_day_rows):
            auxiliary_targets.append(
                {
                    "day_index": day_index,
                    "date": iso_date(trading_row.date),
                    "label_int": labels[day_index - 1],
                    "label_text": label_text(labels[day_index - 1]),
                    "movement_percent": trading_row.movement_percent,
                }
            )

    main_label_int = labels[-1]
    row = {
        "example_id": f"{DATASET_ID}__{symbol}__{target_date}",
        "dataset_id": DATASET_ID,
        "split": split,
        "stock_symbol": symbol,
        "target_date": target_date,
        "label_int": main_label_int,
        "label_text": label_text(main_label_int),
        "target_movement_percent": main_mv,
        "target_price_prev_adj_close": price_feature_rows[-1].raw_adj_close,
        "target_price_adj_close": target_row.raw_adj_close,
        "calendar_lag_days": CALENDAR_LAG_DAYS,
        "aligned_trading_days_count": len(aligned_days),
        "aligned_days": aligned_days,
        "auxiliary_targets": auxiliary_targets,
        "source_dataset": SOURCE_REPO_NAME,
        "source_policy": "paper_canonical_stocknet_acl18",
        "lag_tweet_count": total_lag_tweets,
        "has_any_lag_tweet": total_lag_tweets > 0,
        "source_paths": {
            "price_preprocessed": f"price/preprocessed/{symbol}.txt",
            "price_raw": f"price/raw/{symbol}.csv",
            "tweet_preprocessed_root": f"tweet/preprocessed/{symbol}",
        },
    }
    return row, "kept"


def build_raw_schema_summary(snapshot_root: Path, symbols: list[str], rows_by_symbol: dict[str, list[PriceRow]]) -> dict:
    tweet_dirs = sorted(p.name for p in (snapshot_root / "tweet" / "preprocessed").iterdir() if p.is_dir())
    missing_tweet_dirs = sorted(set(symbols) - set(tweet_dirs))
    sample_symbol = "WFC"
    sample_price_row = rows_by_symbol[sample_symbol][0]
    sample_tweet_file = snapshot_root / "tweet" / "preprocessed" / sample_symbol / "2014-01-02"
    sample_tweet = load_preprocessed_tweets(sample_tweet_file)[:3]
    return {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "price_preprocessed_file_count": len(symbols),
        "price_raw_file_count": len(list((snapshot_root / "price" / "raw").glob("*.csv"))),
        "tweet_preprocessed_dir_count": len(tweet_dirs),
        "tweet_raw_dir_count": len([p for p in (snapshot_root / "tweet" / "raw").iterdir() if p.is_dir()]),
        "missing_tweet_dirs": missing_tweet_dirs,
        "sample_price_preprocessed_fields": list(preprocessed_price_dict(sample_price_row).keys()),
        "sample_price_raw_fields": list(raw_price_dict(sample_price_row).keys()),
        "sample_preprocessed_tweet_texts": sample_tweet,
        "notes": [
            "The official StockNet release exposes 88 price files and 87 tweet directories at the pinned source snapshot.",
            "GMRE appears in the price release but has no corresponding tweet directory and no canonical paper-window samples.",
            "Preprocessed tweet texts are token lists that ST312 joins back into space-separated strings for canonical JSONL serialization.",
            "Price movement percents in the preprocessed release match adjusted-close returns computed from the raw Yahoo Finance CSVs within float tolerance.",
        ],
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    src_root = ensure_source_checkout()
    copy_source_snapshot(src_root)
    source_checksums = write_source_checksums(SOURCE_SNAPSHOT_DIR)

    price_files = sorted((SOURCE_SNAPSHOT_DIR / "price" / "preprocessed").glob("*.txt"))
    symbols = sorted(path.stem for path in price_files)
    rows_by_symbol = {symbol: load_stock_price_rows(SOURCE_SNAPSHOT_DIR, symbol) for symbol in symbols}

    processed = {"train": [], "dev": [], "test": []}
    candidate_counts = Counter()
    removal_counts = Counter()
    strict_tweet_counts = Counter()
    per_stock_counts = Counter()
    per_stock_no_tweet_counts = Counter()
    aligned_day_distribution = Counter()
    split_class_counts: dict[str, Counter] = defaultdict(Counter)

    for symbol in symbols:
        tweet_root = SOURCE_SNAPSHOT_DIR / "tweet" / "preprocessed" / symbol
        for target_index, target_row in enumerate(rows_by_symbol[symbol]):
            split = split_for_target_date(iso_date(target_row.date))
            if split is None:
                continue
            candidate_counts[split] += 1
            row, status = build_sample(symbol, rows_by_symbol[symbol], target_index, tweet_root)
            if row is None:
                removal_counts[status] += 1
                continue
            processed[row["split"]].append(row)
            per_stock_counts[symbol] += 1
            aligned_day_distribution[row["aligned_trading_days_count"]] += 1
            split_class_counts[row["split"]][row["label_text"]] += 1
            if not row["has_any_lag_tweet"]:
                per_stock_no_tweet_counts[symbol] += 1
            else:
                strict_tweet_counts[row["split"]] += 1

    for split in processed:
        processed[split].sort(key=lambda row: (row["target_date"], row["stock_symbol"]))

    actual_counts = {split: len(rows) for split, rows in processed.items()}
    total_count = sum(actual_counts.values())
    if actual_counts != EXPECTED_SPLIT_COUNTS or total_count != EXPECTED_TOTAL:
        audit = {
            "status": "failure",
            "paper_expected_counts": EXPECTED_SPLIT_COUNTS,
            "paper_expected_total": EXPECTED_TOTAL,
            "reconstructed_counts": actual_counts,
            "reconstructed_total": total_count,
            "candidate_counts": dict(candidate_counts),
            "removal_counts": dict(removal_counts),
            "strict_tweet_presence_counts": dict(strict_tweet_counts),
            "notes": [
                "The canonical reconstruction did not match the paper's exact counts, so publication must stop.",
                RECONSTRUCTION_POLICY_NOTE,
            ],
        }
        write_json(RECONSTRUCTION_AUDIT_PATH, audit)
        raise RuntimeError(f"StockNet reconstruction failed exact-count invariant: {actual_counts} / {total_count}")

    write_jsonl(TRAIN_PATH, processed["train"])
    write_jsonl(DEV_PATH, processed["dev"])
    write_jsonl(TEST_PATH, processed["test"])

    strict_tweet_total = sum(strict_tweet_counts.values())
    no_tweet_after_threshold = total_count - strict_tweet_total
    raw_schema_summary = build_raw_schema_summary(SOURCE_SNAPSHOT_DIR, symbols, rows_by_symbol)
    write_json(RAW_SCHEMA_SUMMARY_PATH, raw_schema_summary)

    reconstruction_audit = {
        "status": "success",
        "paper_expected_counts": EXPECTED_SPLIT_COUNTS,
        "paper_expected_total": EXPECTED_TOTAL,
        "reconstructed_counts": actual_counts,
        "reconstructed_total": total_count,
        "candidate_counts_before_filtering": dict(candidate_counts),
        "removal_counts": dict(removal_counts),
        "strict_tweet_presence_filter_counts": dict(strict_tweet_counts),
        "strict_tweet_presence_filter_total": strict_tweet_total,
        "strict_tweet_presence_matches_paper_counts": strict_tweet_total == EXPECTED_TOTAL and dict(strict_tweet_counts) == EXPECTED_SPLIT_COUNTS,
        "strict_tweet_presence_drop_count": no_tweet_after_threshold,
        "source_snapshot_commit": SOURCE_COMMIT,
        "stocks_in_price_release": len(symbols),
        "stocks_in_tweet_release": raw_schema_summary["tweet_preprocessed_dir_count"],
        "stocks_with_reconstructed_samples": len(per_stock_counts),
        "per_stock_sample_counts": dict(sorted(per_stock_counts.items())),
        "per_stock_no_tweet_counts": dict(sorted((k, v) for k, v in per_stock_no_tweet_counts.items() if v)),
        "aligned_trading_days_distribution": dict(sorted(aligned_day_distribution.items())),
        "class_counts_by_split": {split: dict(counter) for split, counter in split_class_counts.items()},
        "notes": [
            "Canonical ST312 reconstruction preserves the paper's exact split boundaries, 5-day alignment semantics, and asymmetric thresholds.",
            RECONSTRUCTION_POLICY_NOTE,
            "This is an inference from the official dataset release and reference code, because every official source snapshot reproduces the paper counts only without the extra hard tweet-presence filter.",
        ],
    }
    write_json(RECONSTRUCTION_AUDIT_PATH, reconstruction_audit)

    source_snapshot_files = sorted(p.relative_to(SOURCE_SNAPSHOT_DIR).as_posix() for p in SOURCE_SNAPSHOT_DIR.rglob("*") if p.is_file())
    download_meta = {
        "source_repo": SOURCE_REPO_NAME,
        "source_url": SOURCE_REPO_URL,
        "source_commit": SOURCE_COMMIT,
        "source_snapshot_datetime_utc": datetime.now(timezone.utc).isoformat(),
        "acquisition_method": "git_clone_checkout_copytree",
        "source_snapshot_root": str(SOURCE_SNAPSHOT_DIR),
        "source_snapshot_file_count": len(source_snapshot_files),
        "source_snapshot_file_sample": source_snapshot_files[:50],
        "source_snapshot_checksums_manifest": str(RAW_SOURCE_CHECKSUMS_PATH),
        "sha256_by_core_file": {
            "README.md": source_checksums["README.md"],
            "LICENSE": source_checksums["LICENSE"],
            "StockTable": source_checksums["StockTable"],
            "appendix_table_of_target_stocks.pdf": source_checksums["appendix_table_of_target_stocks.pdf"],
        },
        "notes": [
            "The official StockNet repository is MIT-licensed.",
            UPSTREAM_RIGHTS_NOTE,
            RECONSTRUCTION_POLICY_NOTE,
        ],
    }
    write_json(RAW_DOWNLOAD_META_PATH, download_meta)

    ingest_summary = {
        "dataset_id": DATASET_ID,
        "canonical_source": SOURCE_REPO_NAME,
        "source_commit": SOURCE_COMMIT,
        "paper_expected_counts": EXPECTED_SPLIT_COUNTS,
        "paper_expected_total": EXPECTED_TOTAL,
        "reconstructed_counts": actual_counts,
        "reconstructed_total": total_count,
        "number_of_stocks_in_price_release": len(symbols),
        "number_of_stocks_in_tweet_release": raw_schema_summary["tweet_preprocessed_dir_count"],
        "number_of_stocks_with_reconstructed_samples": len(per_stock_counts),
        "number_of_candidate_stock_days_before_thresholding": sum(candidate_counts.values()),
        "number_removed_by_middle_band_filter": removal_counts["middle_band"],
        "number_removed_for_insufficient_history": removal_counts["insufficient_history"],
        "strict_tweet_presence_filter_drop_count": no_tweet_after_threshold,
        "strict_tweet_presence_filter_counts": dict(strict_tweet_counts),
        "split_counts": actual_counts,
        "all_paper_count_invariants_passed": True,
        "strict_tweet_presence_filter_matches_paper_counts": False,
        "per_stock_anomalies": {
            "missing_tweet_directories": raw_schema_summary["missing_tweet_dirs"],
            "stocks_without_reconstructed_samples": sorted(set(symbols) - set(per_stock_counts)),
        },
        "notes": [
            "Canonical reconstruction preserves the paper's exact split dates and total sample counts.",
            "Middle-band filtering uses the paper thresholds <= -0.5% -> Fall and > 0.55% -> Rise.",
            "The official release contains many threshold-retained samples with zero tweets in the 5-day lag; ST312 documents this but does not apply it as a hard filter because doing so breaks the exact paper counts.",
            UPSTREAM_RIGHTS_NOTE,
        ],
    }
    write_json(INGEST_SUMMARY_PATH, ingest_summary)

    print(f"[DONE] Reconstructed {DATASET_ID}")
    print(f"[INFO] source_commit={SOURCE_COMMIT}")
    print(f"[INFO] reconstructed_total={total_count}")
    print(f"[INFO] split_counts={actual_counts}")
    print(f"[INFO] strict_tweet_presence_counts={dict(strict_tweet_counts)}")
    print(f"[OUT]  {TRAIN_PATH}")
    print(f"[OUT]  {DEV_PATH}")
    print(f"[OUT]  {TEST_PATH}")
    print(f"[OUT]  {INGEST_SUMMARY_PATH}")
    print(f"[OUT]  {RECONSTRUCTION_AUDIT_PATH}")


if __name__ == "__main__":
    main()
