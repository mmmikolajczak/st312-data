from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

WRAPPER_DATASET = "TheFinAI/flare-sm-acl"
OUT_PATH = Path("reports/stocknet_acl18_paper/finben_wrapper_audit.json")
INGEST_SUMMARY_PATH = Path("data/stocknet_acl18_paper/processed/ingest_summary.json")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_wrapper_label(value) -> str | None:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"rise", "fall"}:
            return normalized.title()
    if isinstance(value, int):
        return {0: "Rise", 1: "Fall"}.get(value)
    return None


def audit_wrapper() -> dict:
    os.environ.setdefault("HF_HOME", str(Path(".hf_cache").resolve()))
    os.environ.setdefault("HF_HUB_CACHE", str((Path(".hf_cache") / "hub").resolve()))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str((Path(".hf_cache") / "hub").resolve()))
    os.environ.setdefault("HF_DATASETS_CACHE", str((Path(".hf_cache") / "datasets").resolve()))
    os.environ.setdefault("HF_XET_CACHE", str((Path(".hf_cache") / "xet").resolve()))
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    from datasets import load_dataset

    cache_dir = Path(os.environ["HF_DATASETS_CACHE"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    ds = load_dataset(WRAPPER_DATASET, cache_dir=str(cache_dir))
    ingest_summary = json.loads(INGEST_SUMMARY_PATH.read_text(encoding="utf-8"))
    observed_split_counts = {split: ds[split].num_rows for split in ds}
    observed_fields = {split: ds[split].column_names for split in ds}

    samples = {}
    label_semantics = {}
    for split in ds:
        row = ds[split][0]
        samples[split] = {key: row[key] for key in row.keys()}
        label_semantics[split] = {
            "answer_label": normalize_wrapper_label(row.get("answer")),
            "gold_label": normalize_wrapper_label(row.get("gold")),
            "choices": row.get("choices"),
        }

    return {
        "wrapper_dataset": WRAPPER_DATASET,
        "wrapper_split_counts_observed": observed_split_counts,
        "canonical_split_counts": ingest_summary["split_counts"],
        "field_shape_differences": {
            "wrapper_fields": observed_fields,
            "canonical_row_shape": [
                "example_id",
                "dataset_id",
                "split",
                "stock_symbol",
                "target_date",
                "label_int",
                "label_text",
                "target_movement_percent",
                "target_price_prev_adj_close",
                "target_price_adj_close",
                "calendar_lag_days",
                "aligned_trading_days_count",
                "aligned_days",
                "auxiliary_targets",
                "source_dataset",
                "source_policy",
            ],
        },
        "sample_rows": samples,
        "threshold_rule_difference_note": (
            "The FLARE wrapper is promptized and aligns with a simplified public description, while the canonical ST312 "
            "module preserves the paper-level asymmetric thresholds <= -0.5% / > 0.55% and exact ACL18 split counts."
        ),
        "wrapper_date_range_and_lag_window_note": (
            "Wrapper examples appear to present a 10-row flattened historical context and observed split counts "
            "20,781 / 2,555 / 3,720, which do not match the paper's 20,339 / 2,555 / 3,720 split counts."
        ),
        "answer_gold_semantics": label_semantics,
        "notes": [
            "The FLARE wrapper is audited only as a compatibility surface and does not define the canonical StockNet dataset.",
            "Wrapper answer values appear to use Rise/Fall directly, while wrapper gold values appear to be choice indices.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    audit = audit_wrapper()
    out_path = Path(args.out)
    write_json(out_path, audit)
    print(f"[DONE] Wrote FLARE wrapper audit to {out_path}")


if __name__ == "__main__":
    main()
