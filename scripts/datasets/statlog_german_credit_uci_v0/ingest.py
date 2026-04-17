from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests


DATASET_ID = "statlog_german_credit_uci_v0"
UCI_DATASET_URL = "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data"
UCI_DOI = "10.24432/C5NC77"
UCI_CITATION = "Hofmann, H. (1994). Statlog (German Credit Data) [Dataset]. UCI Machine Learning Repository."
SOURCE_DATASET = "uci_statlog_german_credit"
SOURCE_POLICY = "canonical_uci_archive"
WRAPPER_DATASET = "TheFinAI/german-credit-benchmark"
WRAPPER_SPLIT_COUNTS = {"train": 700, "valid": 100, "test": 200}
UCI_RAW_URLS = {
    "german.data": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data",
    "german.data-numeric": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data-numeric",
    "german.doc": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.doc",
}

ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = ROOT / "datasets" / DATASET_ID
RAW_DIR = ROOT / "data" / "statlog_german_credit_uci" / "raw"
PROCESSED_DIR = ROOT / "data" / "statlog_german_credit_uci" / "processed"
REPORT_DIR = ROOT / "reports" / "statlog_german_credit_uci"
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
RAW_SCHEMA_SUMMARY_PATH = REPORT_DIR / "raw_schema_summary.json"
SPLIT_REPLICATION_AUDIT_PATH = REPORT_DIR / "split_replication_audit.json"
WRAPPER_ALIGNMENT_AUDIT_PATH = REPORT_DIR / "wrapper_alignment_audit.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"

NUMERIC_ATTRIBUTES = {
    "Attribute2",
    "Attribute5",
    "Attribute8",
    "Attribute11",
    "Attribute13",
    "Attribute16",
    "Attribute18",
}
FEATURE_ORDER = [f"Attribute{i}" for i in range(1, 21)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_feature_maps() -> tuple[dict, dict]:
    return (
        load_json(DATASET_DIR / "feature_name_map.json"),
        load_json(DATASET_DIR / "categorical_value_map.json"),
    )


def download_raw_files() -> dict[str, dict]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_meta: dict[str, dict] = {}
    for name, url in UCI_RAW_URLS.items():
        path = RAW_DIR / name
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)
        file_meta[name] = {
            "url": url,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
    return file_meta


def parse_symbolic_rows(feature_map: dict, categorical_map: dict) -> list[dict]:
    rows: list[dict] = []
    symbolic_path = RAW_DIR / "german.data"
    for row_index, line in enumerate(symbolic_path.read_text(encoding="utf-8").splitlines(), start=1):
        tokens = line.split()
        if len(tokens) != 21:
            raise ValueError(f"Unexpected token count in german.data row {row_index}: {len(tokens)}")

        record: dict = {
            "uci_row_index": row_index,
            "source_dataset": SOURCE_DATASET,
            "source_policy": SOURCE_POLICY,
        }
        feature_pairs_decoded: list[dict] = []
        feature_text_lines: list[str] = []
        wrapper_features: dict[str, str] = {}

        for attr_name, raw_token in zip(FEATURE_ORDER, tokens[:20]):
            feature_info = feature_map[attr_name]
            wrapper_alias = feature_info["wrapper_alias"]
            decoded_feature_name = feature_info["decoded_feature_name"]
            if attr_name in NUMERIC_ATTRIBUTES:
                raw_value = int(raw_token)
                decoded_value = str(raw_value)
                wrapper_alias_value = f"{float(raw_value):.2f}"
            else:
                raw_value = raw_token
                category_info = categorical_map[attr_name][raw_token]
                decoded_value = category_info["decoded_value"]
                wrapper_alias_value = category_info["wrapper_alias_value"]

            record[attr_name] = raw_value
            wrapper_features[wrapper_alias] = wrapper_alias_value
            feature_pairs_decoded.append(
                {
                    "attribute_id": attr_name,
                    "feature_name": decoded_feature_name,
                    "raw_value": raw_value,
                    "decoded_value": decoded_value,
                    "wrapper_alias": wrapper_alias,
                    "wrapper_alias_value": wrapper_alias_value,
                }
            )
            if attr_name in NUMERIC_ATTRIBUTES:
                feature_text_lines.append(f"{attr_name} — {decoded_feature_name}: {raw_value}")
            else:
                feature_text_lines.append(
                    f"{attr_name} — {decoded_feature_name}: {raw_value} (decoded: {decoded_value})"
                )

        class_value = int(tokens[20])
        if class_value not in {1, 2}:
            raise ValueError(f"Unexpected class value in german.data row {row_index}: {class_value}")
        record["Class"] = class_value
        record["label_int_uci"] = class_value
        record["label_text"] = "good" if class_value == 1 else "bad"
        record["feature_pairs_decoded"] = feature_pairs_decoded
        record["feature_text_decoded"] = "\n".join(feature_text_lines)
        record["_wrapper_feature_vector"] = wrapper_features
        rows.append(record)

    if len(rows) != 1000:
        raise ValueError(f"Expected 1000 symbolic rows, found {len(rows)}")
    return rows


def load_wrapper_dataset():
    os.environ.setdefault("HF_HUB_CACHE", str((ROOT / ".hf_cache" / "hub").resolve()))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str((ROOT / ".hf_cache" / "hub").resolve()))
    os.environ.setdefault("HF_DATASETS_CACHE", str((ROOT / ".hf_cache" / "datasets").resolve()))
    os.environ.setdefault("HF_XET_CACHE", str((ROOT / ".hf_cache" / "xet").resolve()))
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    from datasets import load_dataset

    return load_dataset(WRAPPER_DATASET, cache_dir=os.environ["HF_DATASETS_CACHE"])


def extract_wrapper_text_blob(query: str) -> str:
    if "Text:" not in query or "\nAnswer:" not in query:
        raise ValueError("Wrapper query missing expected Text/Answer markers")
    blob = query.split("Text:", 1)[1].split("\nAnswer:", 1)[0].strip()
    blob = blob.removeprefix("'").removesuffix("'.").removesuffix("'").strip()
    return blob


def parse_wrapper_query(query: str) -> dict[str, str]:
    blob = extract_wrapper_text_blob(query)
    features: dict[str, str] = {}
    for part in blob.split(", "):
        if ": " not in part:
            raise ValueError(f"Malformed wrapper feature token: {part!r}")
        key, value = part.split(": ", 1)
        features[key.strip()] = value.strip().strip("'").strip('"')
    if "telephone" in features:
        features["telephone"] = features["telephone"].strip("'").strip('"')
    return features


def build_signature(wrapper_features: dict[str, str], label_text: str, feature_map: dict) -> tuple:
    ordered = []
    for attr_name in FEATURE_ORDER:
        wrapper_alias = feature_map[attr_name]["wrapper_alias"]
        ordered.append((wrapper_alias, wrapper_features[wrapper_alias]))
    ordered.append(("label_text", label_text))
    return tuple(ordered)


def replicate_wrapper_split(uci_rows: list[dict], feature_map: dict) -> tuple[dict[int, dict], dict, dict]:
    wrapper = load_wrapper_dataset()
    observed_split_counts = {split: wrapper[split].num_rows for split in wrapper}

    signature_to_row_indices: dict[tuple, list[int]] = defaultdict(list)
    duplicate_signature_sizes: dict[str, int] = {}
    for row in uci_rows:
        signature = build_signature(row["_wrapper_feature_vector"], row["label_text"], feature_map)
        signature_to_row_indices[signature].append(row["uci_row_index"])
    for signature, indices in signature_to_row_indices.items():
        if len(indices) > 1:
            duplicate_signature_sizes[json.dumps(signature, ensure_ascii=False)] = len(indices)

    assignment_by_row_index: dict[int, dict] = {}
    signature_occurrence_counter: Counter = Counter()
    missing_rows: list[dict] = []
    overrun_rows: list[dict] = []
    wrapper_alignment_samples: dict[str, dict] = {}

    for split in ["train", "valid", "test"]:
        first_row = wrapper[split][0]
        wrapper_alignment_samples[split] = {key: first_row[key] for key in first_row}
        for row in wrapper[split]:
            parsed_features = parse_wrapper_query(row["query"])
            label_text = row["answer"].strip().lower()
            signature = build_signature(parsed_features, label_text, feature_map)
            signature_occurrence_counter[signature] += 1
            candidate_rows = signature_to_row_indices.get(signature)
            if not candidate_rows:
                missing_rows.append(
                    {
                        "split": split,
                        "id": row["id"],
                        "answer": row["answer"],
                        "parsed_features": parsed_features,
                    }
                )
                continue

            occurrence_index = signature_occurrence_counter[signature] - 1
            if occurrence_index >= len(candidate_rows):
                overrun_rows.append(
                    {
                        "split": split,
                        "id": row["id"],
                        "signature": list(signature),
                        "available_matches": len(candidate_rows),
                        "requested_occurrence_index": occurrence_index,
                    }
                )
                continue

            matched_row_index = candidate_rows[occurrence_index]
            if matched_row_index in assignment_by_row_index:
                raise RuntimeError(f"Duplicate wrapper assignment for UCI row {matched_row_index}")
            assignment_by_row_index[matched_row_index] = {
                "split": split,
                "wrapper_id": row["id"],
                "wrapper_gold": row["gold"],
            }

    split_counts = Counter(meta["split"] for meta in assignment_by_row_index.values())
    exact_match_count = len(assignment_by_row_index)
    unassigned_rows = [row["uci_row_index"] for row in uci_rows if row["uci_row_index"] not in assignment_by_row_index]
    passed = (
        exact_match_count == 1000
        and not missing_rows
        and not overrun_rows
        and split_counts == Counter(WRAPPER_SPLIT_COUNTS)
        and not unassigned_rows
    )

    split_audit = {
        "status": "success" if passed else "failed",
        "canonical_dataset_id": DATASET_ID,
        "wrapper_dataset": WRAPPER_DATASET,
        "wrapper_split_counts_observed": observed_split_counts,
        "target_split_counts": WRAPPER_SPLIT_COUNTS,
        "matched_rows_total": exact_match_count,
        "unassigned_uci_rows": len(unassigned_rows),
        "unassigned_uci_row_indices_sample": unassigned_rows[:25],
        "missing_wrapper_rows": len(missing_rows),
        "missing_wrapper_rows_sample": missing_rows[:10],
        "overrun_wrapper_rows": len(overrun_rows),
        "overrun_wrapper_rows_sample": overrun_rows[:10],
        "duplicate_signature_count": len(duplicate_signature_sizes),
        "duplicate_signature_sizes": duplicate_signature_sizes,
        "ambiguous_duplicate_matches": 0,
        "assigned_split_counts": dict(split_counts),
        "replication_passed": passed,
        "notes": [
            "The FinBen-style wrapper is used only as a split replication surface, not as the canonical source dataset.",
            "Split replication is exact only if all 1,000 UCI rows are matched and assigned to train/valid/test at 700/100/200.",
        ],
    }

    wrapper_alignment_audit = {
        "wrapper_dataset": WRAPPER_DATASET,
        "wrapper_split_counts_observed": observed_split_counts,
        "wrapper_feature_alias_order": [feature_map[attr]["wrapper_alias"] for attr in FEATURE_ORDER],
        "wrapper_example_samples": wrapper_alignment_samples,
        "wrapper_answer_space": ["good", "bad"],
        "wrapper_choices_example": wrapper_alignment_samples["train"]["choices"],
        "wrapper_gold_semantics_note": "Wrapper gold behaves as the index into choices=['good','bad'], while answer is the lower-case label string.",
        "uci_match_coverage": exact_match_count,
        "notes": [
            "Wrapper query text uses decoded alias features such as ageInYears and statusOfExistingCheckingAccount.",
            "Telephone values in the wrapper occasionally include a leading quote; ST312 normalizes that before matching.",
        ],
    }

    return assignment_by_row_index, split_audit, wrapper_alignment_audit


def build_processed_rows(uci_rows: list[dict], assignment_by_row_index: dict[int, dict]) -> dict[str, list[dict]]:
    split_rows = {"train": [], "valid": [], "test": []}
    for row in uci_rows:
        assignment = assignment_by_row_index[row["uci_row_index"]]
        split = assignment["split"]
        output_row = {
            "example_id": f"uci_row_{row['uci_row_index']:04d}",
            "dataset_id": DATASET_ID,
            "split": split,
            "uci_row_index": row["uci_row_index"],
            **{attr: row[attr] for attr in FEATURE_ORDER},
            "Class": row["Class"],
            "label_int_uci": row["label_int_uci"],
            "label_text": row["label_text"],
            "feature_pairs_decoded": row["feature_pairs_decoded"],
            "feature_text_decoded": row["feature_text_decoded"],
            "source_dataset": SOURCE_DATASET,
            "source_policy": SOURCE_POLICY,
        }
        split_rows[split].append(output_row)
    return split_rows


def class_counts(rows: list[dict]) -> dict[str, int]:
    counts = Counter(row["label_text"] for row in rows)
    return {"good": counts.get("good", 0), "bad": counts.get("bad", 0)}


def build_ingest_summary(
    file_meta: dict[str, dict],
    split_rows: dict[str, list[dict]],
    split_audit: dict,
) -> dict:
    return {
        "dataset_id": DATASET_ID,
        "uci_dataset_url": UCI_DATASET_URL,
        "doi": UCI_DOI,
        "raw_files": file_meta,
        "row_count": sum(len(rows) for rows in split_rows.values()),
        "split_counts": {split: len(rows) for split, rows in split_rows.items()},
        "class_counts_by_split": {split: class_counts(rows) for split, rows in split_rows.items()},
        "exact_wrapper_matches": split_audit["matched_rows_total"],
        "ambiguous_duplicate_matches": split_audit["ambiguous_duplicate_matches"],
        "split_replication_passed": split_audit["replication_passed"],
        "no_missing_values": True,
        "source_cost_matrix": {
            "actual_good_pred_good": 0,
            "actual_good_pred_bad": 1,
            "actual_bad_pred_good": 5,
            "actual_bad_pred_bad": 0,
        },
        "notes": [
            "UCI provides no official train/valid/test split on the archive page, so ST312 reuses the public wrapper split only after exact row-level replication.",
            "The canonical source remains the original symbolic german.data file; german.data-numeric is retained raw-only as an auxiliary file.",
            "This historical credit benchmark contains sensitive demographic-style variables including personal status and sex, age in years, and foreign-worker status.",
        ],
    }


def build_raw_schema_summary(file_meta: dict[str, dict]) -> dict:
    symbolic_lines = (RAW_DIR / "german.data").read_text(encoding="utf-8").splitlines()
    numeric_lines = (RAW_DIR / "german.data-numeric").read_text(encoding="utf-8").splitlines()
    return {
        "dataset_id": DATASET_ID,
        "source_dataset_url": UCI_DATASET_URL,
        "doi": UCI_DOI,
        "raw_files": file_meta,
        "symbolic_row_count": len(symbolic_lines),
        "numeric_row_count": len(numeric_lines),
        "symbolic_columns_per_row": len(symbolic_lines[0].split()) if symbolic_lines else 0,
        "numeric_columns_per_row": len(numeric_lines[0].split()) if numeric_lines else 0,
        "doc_size_bytes": file_meta["german.doc"]["size_bytes"],
        "notes": [
            "german.data is the canonical original symbolic dataset surface preserved by ST312.",
            "german.data-numeric is auxiliary only and is not used as the canonical processed source.",
            "UCI states the dataset has no missing values and requires use of a cost matrix.",
        ],
    }


def build_download_meta(file_meta: dict[str, dict]) -> dict:
    return {
        "dataset_id": DATASET_ID,
        "uci_dataset_url": UCI_DATASET_URL,
        "doi": UCI_DOI,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_raw_source_policy": "raw archive files are the source of truth; fetch_ucirepo(id=144) is documented by UCI but not treated as the canonical raw surface",
        "raw_files": file_meta,
        "notes": [
            "The canonical source is the UCI archive listing for dataset 144.",
            "The original symbolic file german.data is preserved as the canonical raw dataset surface.",
            "UCI also documents Python access via fetch_ucirepo(id=144), but ST312 treats the archive raw files as authoritative.",
        ],
    }


def run_pipeline(fail_on_split_mismatch: bool = True) -> dict:
    feature_map, categorical_map = load_feature_maps()
    file_meta = download_raw_files()
    uci_rows = parse_symbolic_rows(feature_map, categorical_map)
    assignment_by_row_index, split_audit, wrapper_alignment_audit = replicate_wrapper_split(uci_rows, feature_map)

    write_json(DOWNLOAD_META_PATH, build_download_meta(file_meta))
    write_json(RAW_SCHEMA_SUMMARY_PATH, build_raw_schema_summary(file_meta))
    write_json(SPLIT_REPLICATION_AUDIT_PATH, split_audit)
    write_json(WRAPPER_ALIGNMENT_AUDIT_PATH, wrapper_alignment_audit)

    if not split_audit["replication_passed"]:
        if fail_on_split_mismatch:
            raise SystemExit(
                "Exact wrapper split replication failed; inspect reports/statlog_german_credit_uci/split_replication_audit.json"
            )
        return {"split_audit": split_audit}

    split_rows = build_processed_rows(uci_rows, assignment_by_row_index)
    write_jsonl(PROCESSED_DIR / "train.jsonl", split_rows["train"])
    write_jsonl(PROCESSED_DIR / "valid.jsonl", split_rows["valid"])
    write_jsonl(PROCESSED_DIR / "test.jsonl", split_rows["test"])

    ingest_summary = build_ingest_summary(file_meta, split_rows, split_audit)
    write_json(INGEST_SUMMARY_PATH, ingest_summary)
    return {"split_rows": split_rows, "ingest_summary": ingest_summary, "split_audit": split_audit}


def main() -> None:
    result = run_pipeline(fail_on_split_mismatch=True)
    print(f"[DONE] Reconstructed {DATASET_ID}")
    print(f"[INFO] split_counts={result['ingest_summary']['split_counts']}")
    print(f"[INFO] exact_wrapper_matches={result['split_audit']['matched_rows_total']}")
    print(f"[OUT]  {PROCESSED_DIR / 'train.jsonl'}")
    print(f"[OUT]  {PROCESSED_DIR / 'valid.jsonl'}")
    print(f"[OUT]  {PROCESSED_DIR / 'test.jsonl'}")
    print(f"[OUT]  {INGEST_SUMMARY_PATH}")
    print(f"[OUT]  {SPLIT_REPLICATION_AUDIT_PATH}")


if __name__ == "__main__":
    main()
