from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[3]
FAMILY_REGISTRY_PATH = ROOT / "datasets" / "calm_family_shared" / "calm_family_registry.json"
FINEVAL_REPO_ID = "Salesforce/FinEval"


def load_family_registry() -> dict:
    return json.loads(FAMILY_REGISTRY_PATH.read_text(encoding="utf-8"))


def load_module_config(module_key: str) -> dict:
    registry = load_family_registry()
    config = registry["modules"][module_key].copy()
    config["canonical_benchmark_release_repo"] = registry["canonical_benchmark_release_repo"]
    config["canonical_benchmark_release_url"] = registry["canonical_benchmark_release_url"]
    config["canonical_benchmark_release_revision"] = registry["canonical_benchmark_release_revision"]
    config["canonical_benchmark_release_license"] = registry["canonical_benchmark_release_license"]
    return config


def configure_hf_env() -> None:
    os.environ.setdefault("HF_HUB_CACHE", str((ROOT / ".hf_cache" / "hub").resolve()))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str((ROOT / ".hf_cache" / "hub").resolve()))
    os.environ.setdefault("HF_DATASETS_CACHE", str((ROOT / ".hf_cache" / "datasets").resolve()))
    os.environ.setdefault("HF_XET_CACHE", str((ROOT / ".hf_cache" / "xet").resolve()))
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


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


def raw_dir(config: dict) -> Path:
    return ROOT / "data" / config["data_slug"] / "raw"


def processed_dir(config: dict) -> Path:
    return ROOT / "data" / config["data_slug"] / "processed"


def report_dir(config: dict) -> Path:
    return ROOT / "reports" / config["data_slug"]


def download_raw_artifacts(config: dict) -> dict:
    configure_hf_env()
    from huggingface_hub import HfApi, hf_hub_download

    raw_root = raw_dir(config)
    raw_root.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    repo_info = api.dataset_info(FINEVAL_REPO_ID)
    revision = repo_info.sha

    readme_cache = Path(
        hf_hub_download(
            repo_id=FINEVAL_REPO_ID,
            repo_type="dataset",
            filename="README.md",
            revision=revision,
        )
    )
    subset_parquet_cache = Path(
        hf_hub_download(
            repo_id=FINEVAL_REPO_ID,
            repo_type="dataset",
            filename=config["benchmark_subset_path"],
            revision=revision,
        )
    )

    readme_path = raw_root / "README.md"
    parquet_path = raw_root / subset_parquet_cache.name
    shutil.copy2(readme_cache, readme_path)
    shutil.copy2(subset_parquet_cache, parquet_path)

    file_meta = {
        "README.md": {
            "repo_path": "README.md",
            "sha256": sha256_file(readme_path),
            "size_bytes": readme_path.stat().st_size,
        },
        subset_parquet_cache.name: {
            "repo_path": config["benchmark_subset_path"],
            "sha256": sha256_file(parquet_path),
            "size_bytes": parquet_path.stat().st_size,
        },
    }

    download_meta = {
        "dataset_id": config["dataset_id"],
        "canonical_benchmark_release_repo": FINEVAL_REPO_ID,
        "canonical_benchmark_release_url": config["canonical_benchmark_release_url"],
        "canonical_benchmark_release_revision": revision,
        "canonical_benchmark_subset": config["benchmark_subset"],
        "canonical_benchmark_release_license": config["canonical_benchmark_release_license"],
        "files": file_meta,
        "notes": [
            "The canonical public benchmark release surface for CALM-family onboarding is Salesforce/FinEval.",
            "The shared FinEval README.md is preserved raw alongside the subset parquet file for provenance.",
            "Best-known raw-source metadata is recorded separately from benchmark-release provenance and may have weaker confidence.",
        ],
    }
    write_json(raw_root / "download_meta.json", download_meta)
    return {
        "revision": revision,
        "parquet_filename": subset_parquet_cache.name,
        "files": file_meta,
    }


def load_subset(config: dict):
    configure_hf_env()
    from datasets import load_dataset

    return load_dataset(FINEVAL_REPO_ID, config["benchmark_subset"])


def normalize_label(config: dict, raw_label: str) -> str:
    normalized = config["normalized_label_map"].get(str(raw_label).strip().lower())
    if normalized is None:
        raise ValueError(f"Unexpected raw label for {config['dataset_id']}: {raw_label!r}")
    return normalized


def process_split(config: dict, split: str, rows) -> tuple[list[dict], dict]:
    processed_rows: list[dict] = []
    label_counts = Counter()
    raw_label_counts = Counter()
    text_lengths: list[int] = []

    for row in rows:
        answer = str(row["answer"]).strip().lower()
        if row["choices"][int(row["gold"])] != row["answer"]:
            raise ValueError(
                f"{config['dataset_id']} row id={row['id']} has answer/gold mismatch: "
                f"choices[{row['gold']}]={row['choices'][int(row['gold'])]!r} vs answer={row['answer']!r}"
            )
        normalized = normalize_label(config, answer)
        feature_text = row.get("text") or row.get("query") or ""
        text_lengths.append(len(feature_text))
        label_counts[normalized] += 1
        raw_label_counts[answer] += 1
        processed_rows.append(
            {
                "example_id": f"{config['dataset_id']}__{split}__{int(row['id']):06d}",
                "dataset_id": config["dataset_id"],
                "split": split,
                "id": row["id"],
                "query": row["query"],
                "answer": row["answer"],
                "choices": row["choices"],
                "gold": row["gold"],
                "text": row.get("text"),
                "label_raw": answer,
                "label_normalized": normalized,
                "label_id": int(row["gold"]),
                "feature_text": feature_text,
                "source_dataset": config["benchmark_subset"],
                "source_release_repo": FINEVAL_REPO_ID,
                "calm_family": True,
                "calm_role": config["calm_role"],
                "calm_instruction_style": config["calm_instruction_style"],
                "calm_training_recipe_minority_resampled": config["calm_training_recipe_minority_resampled"],
            }
        )

    split_summary = {
        "row_count": len(processed_rows),
        "label_raw_counts": dict(raw_label_counts),
        "label_normalized_counts": dict(label_counts),
        "choices": processed_rows[0]["choices"] if processed_rows else config["allowed_labels"],
        "min_feature_text_length": min(text_lengths) if text_lengths else 0,
        "max_feature_text_length": max(text_lengths) if text_lengths else 0,
        "mean_feature_text_length": mean(text_lengths) if text_lengths else 0.0,
    }
    return processed_rows, split_summary


def build_raw_schema_summary(config: dict, dataset_dict, raw_meta: dict) -> dict:
    split_name = list(dataset_dict.keys())[0]
    sample_row = dataset_dict[split_name][0]
    return {
        "dataset_id": config["dataset_id"],
        "canonical_benchmark_release_repo": FINEVAL_REPO_ID,
        "canonical_benchmark_release_revision": raw_meta["revision"],
        "canonical_benchmark_subset": config["benchmark_subset"],
        "available_splits": {split: dataset_dict[split].num_rows for split in dataset_dict},
        "fields": list(sample_row.keys()),
        "sample_row": sample_row,
        "files": raw_meta["files"],
    }


def build_label_inventory(config: dict) -> dict:
    return {
        "dataset_id": config["dataset_id"],
        "allowed_labels": config["allowed_labels"],
        "normalized_label_map": config["normalized_label_map"],
        "choices_alignment_note": "label_id preserves the benchmark wrapper gold index, and label_raw preserves the wrapper answer string exactly as released.",
    }


def build_ingest_summary(config: dict, dataset_dict, split_summaries: dict, raw_meta: dict) -> dict:
    return {
        "dataset_id": config["dataset_id"],
        "canonical_benchmark_release_repo": FINEVAL_REPO_ID,
        "canonical_benchmark_release_revision": raw_meta["revision"],
        "canonical_benchmark_subset": config["benchmark_subset"],
        "available_splits": {split: dataset_dict[split].num_rows for split in dataset_dict},
        "split_summaries": split_summaries,
        "calm_family": True,
        "calm_role": config["calm_role"],
        "calm_instruction_style": config["calm_instruction_style"],
        "calm_training_recipe_minority_resampled": config["calm_training_recipe_minority_resampled"],
        "best_known_raw_source": config["best_known_raw_source"],
        "raw_source_confidence": config["raw_source_confidence"],
        "notes": [
            "ST312 preserves the public FinEval benchmark wrapper exactly as released and does not fabricate train/dev splits for these public subsets.",
            "CALM role metadata records whether the dataset was used for train+eval or held out as eval-only in the original CALM recipe; it does not imply the public benchmark release exposes the same split structure.",
            config["source_chain_caution"],
        ],
    }


def run_ingest(module_key: str) -> dict:
    config = load_module_config(module_key)
    raw_meta = download_raw_artifacts(config)
    dataset_dict = load_subset(config)

    split_summaries: dict[str, dict] = {}
    for split in dataset_dict:
        processed_rows, split_summary = process_split(config, split, dataset_dict[split])
        write_jsonl(processed_dir(config) / f"{split}.jsonl", processed_rows)
        split_summaries[split] = split_summary

    write_json(report_dir(config) / "raw_schema_summary.json", build_raw_schema_summary(config, dataset_dict, raw_meta))
    write_json(processed_dir(config) / "label_inventory.json", build_label_inventory(config))
    write_json(processed_dir(config) / "ingest_summary.json", build_ingest_summary(config, dataset_dict, split_summaries, raw_meta))

    return {
        "config": config,
        "raw_meta": raw_meta,
        "split_summaries": split_summaries,
    }
