import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CANONICAL_FILE = Path.home() / "Downloads" / "gold_commodity_news_kaggle_daittan_raw" / "finalDataset_0208.csv"
DEFAULT_DERIVATIVE_FILE = Path.home() / "Downloads" / "gold_commodity_news_kaggle_raw" / "gold-dataset-sinha-khandait.csv"

CANONICAL_OUT = Path("data/gold_commodity_news/raw/canonical/finalDataset_0208.csv")
DERIVATIVE_OUT = Path("data/gold_commodity_news/raw/derivative_reference/gold-dataset-sinha-khandait.csv")
META_OUT = Path("data/gold_commodity_news/raw/gold_commodity_news_ingest_meta.json")


def copy_file(src: Path, dst: Path, force: bool = False) -> int:
    if not src.exists():
        raise FileNotFoundError(f"Missing source file: {src}")
    if dst.exists() and not force:
        return dst.stat().st_size
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst.stat().st_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical-file", default=None, help="Path to canonical finalDataset_0208.csv")
    ap.add_argument("--derivative-file", default=None, help="Path to derivative gold-dataset-sinha-khandait.csv")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    canonical_src = Path(args.canonical_file).expanduser() if args.canonical_file else DEFAULT_CANONICAL_FILE
    derivative_src = Path(args.derivative_file).expanduser() if args.derivative_file else DEFAULT_DERIVATIVE_FILE

    if not canonical_src.exists():
        raise SystemExit(f"Canonical source file missing: {canonical_src}")

    n_bytes = copy_file(canonical_src, CANONICAL_OUT, force=args.force)
    print(f"[OK] {canonical_src} -> {CANONICAL_OUT} ({n_bytes} bytes)")

    derivative_copied = False
    derivative_bytes = None
    if derivative_src.exists():
        derivative_bytes = copy_file(derivative_src, DERIVATIVE_OUT, force=args.force)
        derivative_copied = True
        print(f"[OK] {derivative_src} -> {DERIVATIVE_OUT} ({derivative_bytes} bytes)")
    else:
        print(f"[WARN] Derivative reference file not found, skipping copy: {derivative_src}")

    meta = {
        "dataset_id": "gold_commodity_news_kaggle_default_v0",
        "source_kind": "user_provided_local_kaggle_copy",
        "canonical_source": {
            "posting": "daittan/gold-commodity-news-and-dimensions",
            "kaggle_url": "https://www.kaggle.com/datasets/daittan/gold-commodity-news-and-dimensions",
            "expected_filename": "finalDataset_0208.csv",
            "copied_filename": CANONICAL_OUT.name,
            "copied_to": str(CANONICAL_OUT),
        },
        "derivative_reference_only": {
            "posting": "ankurzing/sentiment-analysis-in-commodity-market-gold",
            "kaggle_url": "https://www.kaggle.com/datasets/ankurzing/sentiment-analysis-in-commodity-market-gold",
            "expected_filename": "gold-dataset-sinha-khandait.csv",
            "copied": derivative_copied,
            "copied_filename": DERIVATIVE_OUT.name if derivative_copied else None,
            "copied_to": str(DERIVATIVE_OUT) if derivative_copied else None,
        },
        "source_resolution_policy": {
            "canonical_default": str(DEFAULT_CANONICAL_FILE),
            "derivative_default": str(DEFAULT_DERIVATIVE_FILE),
            "absolute_paths_in_published_metadata": False,
        },
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes": {
            "canonical_bytes": n_bytes,
            "derivative_bytes": derivative_bytes,
        },
        "notes": [
            "Canonical ingest source is the daittan Kaggle posting because it matches the paper-era row count and 9-label schema.",
            "The ankurzing file is retained for provenance comparison only and is not the canonical raw source.",
            "No raw modifications are applied at ingest time.",
        ],
    }
    META_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote ingest metadata: {META_OUT}")


if __name__ == "__main__":
    main()
