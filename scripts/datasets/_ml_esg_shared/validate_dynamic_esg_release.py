from __future__ import annotations

import re
from collections import Counter


REQUIRED_KEYS = ["pk", "URL", "News_Headline", "ESG_Category"]
IMPACT_REQUIRED_KEYS = ["pk", "URL", "News_Headline", "Impact_Type"]
LABEL_SANITY_RE = re.compile(r"^(?:[ESG]\d{2}|NN)$")


def make_article_id(pk: int) -> str:
    return f"dynamicesg_bt_{pk}"


def make_example_id(dataset_id: str, split: str, article_id: str) -> str:
    return f"{dataset_id}__{split}__{article_id}"


def normalize_label_code(value: str) -> str:
    return str(value).strip().upper()


def normalize_impact_type(value: str) -> str:
    return " ".join(str(value).split())


def canonicalize_labels(values: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"Label values must be strings, got {type(value)!r}")
        label = normalize_label_code(value)
        if not label:
            raise ValueError("Encountered an empty label after normalization")
        if label not in seen:
            seen.add(label)
            normalized.append(label)
    return sorted(normalized)


def canonicalize_singleton_impact_type(value) -> str:
    if not isinstance(value, list):
        raise ValueError("Impact_Type must be a list")
    if len(value) != 1:
        raise ValueError(f"Impact_Type must contain exactly one label, got {len(value)}")
    raw_label = value[0]
    if not isinstance(raw_label, str):
        raise TypeError(f"Impact_Type label must be a string, got {type(raw_label)!r}")
    label = normalize_impact_type(raw_label)
    if not label:
        raise ValueError("Encountered an empty Impact_Type label after normalization")
    return label


def build_processed_row(
    *,
    dataset_id: str,
    split: str,
    source_repo: str,
    source_commit: str,
    source_path: str,
    row: dict,
) -> dict:
    pk = int(row["pk"])
    article_id = make_article_id(pk)
    labels = canonicalize_labels(row["ESG_Category"])
    headline = str(row["News_Headline"]).strip()
    url = str(row["URL"]).strip()

    return {
        "example_id": make_example_id(dataset_id, split, article_id),
        "article_id": article_id,
        "dataset_id": dataset_id,
        "split": split,
        "language": "zh",
        "text": headline,
        "headline": headline,
        "url": url,
        "source_pk": pk,
        "labels": labels,
        "label_count": len(labels),
        "source_repo": source_repo,
        "source_commit": source_commit,
        "source_path": source_path,
    }


def build_processed_single_label_row(
    *,
    dataset_id: str,
    split: str,
    source_repo: str,
    source_commit: str,
    source_path: str,
    row: dict,
) -> dict:
    pk = int(row["pk"])
    article_id = make_article_id(pk)
    impact_type = canonicalize_singleton_impact_type(row["Impact_Type"])
    headline = str(row["News_Headline"]).strip()
    url = str(row["URL"]).strip()

    return {
        "example_id": make_example_id(dataset_id, split, article_id),
        "article_id": article_id,
        "dataset_id": dataset_id,
        "split": split,
        "language": "zh",
        "text": headline,
        "headline": headline,
        "url": url,
        "source_pk": pk,
        "impact_type": impact_type,
        "source_impact_type_list": list(row["Impact_Type"]),
        "source_repo": source_repo,
        "source_commit": source_commit,
        "source_path": source_path,
    }


def validate_and_build_rows(
    *,
    dataset_id: str,
    split: str,
    source_repo: str,
    source_commit: str,
    source_path: str,
    rows: list[dict],
) -> tuple[list[dict], dict]:
    processed_rows = []
    missing_field_counts = Counter({key: 0 for key in REQUIRED_KEYS})
    unexpected_label_codes = set()
    seen_example_ids = set()
    seen_article_ids = set()

    for idx, row in enumerate(rows):
        for key in REQUIRED_KEYS:
            if key not in row:
                missing_field_counts[key] += 1
        missing_keys = [key for key in REQUIRED_KEYS if key not in row]
        if missing_keys:
            raise KeyError(f"{split}[{idx}] missing required keys: {missing_keys}")

        try:
            pk = int(row["pk"])
        except Exception as exc:
            raise ValueError(f"{split}[{idx}] pk is not integer-like: {row['pk']!r}") from exc

        url = row["URL"]
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"{split}[{idx}] URL must be a non-empty string")

        headline = row["News_Headline"]
        if not isinstance(headline, str) or not headline.strip():
            raise ValueError(f"{split}[{idx}] News_Headline must be a non-empty string")

        labels = row["ESG_Category"]
        if not isinstance(labels, list):
            raise ValueError(f"{split}[{idx}] ESG_Category must be a list")

        for label in labels:
            if not isinstance(label, str):
                raise ValueError(f"{split}[{idx}] ESG_Category labels must all be strings")

        processed = build_processed_row(
            dataset_id=dataset_id,
            split=split,
            source_repo=source_repo,
            source_commit=source_commit,
            source_path=source_path,
            row=row,
        )

        for label in processed["labels"]:
            if not LABEL_SANITY_RE.match(label):
                unexpected_label_codes.add(label)

        if processed["article_id"] in seen_article_ids:
            raise ValueError(f"Duplicate article_id detected in {split}: {processed['article_id']}")
        if processed["example_id"] in seen_example_ids:
            raise ValueError(f"Duplicate example_id detected in {split}: {processed['example_id']}")

        seen_example_ids.add(processed["example_id"])
        seen_article_ids.add(processed["article_id"])
        if pk != processed["source_pk"]:
            raise AssertionError("source_pk mismatch after processing")
        processed_rows.append(processed)

    return processed_rows, {
        "missing_field_counts": dict(missing_field_counts),
        "unexpected_label_codes": sorted(unexpected_label_codes),
    }


def validate_and_build_single_label_rows(
    *,
    dataset_id: str,
    split: str,
    source_repo: str,
    source_commit: str,
    source_path: str,
    rows: list[dict],
    allowed_labels: set[str] | None = None,
) -> tuple[list[dict], dict]:
    processed_rows = []
    missing_field_counts = Counter({key: 0 for key in IMPACT_REQUIRED_KEYS})
    seen_example_ids = set()
    seen_article_ids = set()
    observed_labels = set()

    for idx, row in enumerate(rows):
        for key in IMPACT_REQUIRED_KEYS:
            if key not in row:
                missing_field_counts[key] += 1
        missing_keys = [key for key in IMPACT_REQUIRED_KEYS if key not in row]
        if missing_keys:
            raise KeyError(f"{split}[{idx}] missing required keys: {missing_keys}")

        try:
            pk = int(row["pk"])
        except Exception as exc:
            raise ValueError(f"{split}[{idx}] pk is not integer-like: {row['pk']!r}") from exc

        url = row["URL"]
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"{split}[{idx}] URL must be a non-empty string")

        headline = row["News_Headline"]
        if not isinstance(headline, str) or not headline.strip():
            raise ValueError(f"{split}[{idx}] News_Headline must be a non-empty string")

        impact_type = row["Impact_Type"]
        if not isinstance(impact_type, list):
            raise ValueError(f"{split}[{idx}] Impact_Type must be a list")
        if len(impact_type) != 1:
            raise ValueError(f"{split}[{idx}] Impact_Type must have exactly one label")
        if not isinstance(impact_type[0], str) or not impact_type[0].strip():
            raise ValueError(f"{split}[{idx}] Impact_Type single entry must be a non-empty string")

        processed = build_processed_single_label_row(
            dataset_id=dataset_id,
            split=split,
            source_repo=source_repo,
            source_commit=source_commit,
            source_path=source_path,
            row=row,
        )

        if allowed_labels is not None and processed["impact_type"] not in allowed_labels:
            raise ValueError(
                f"{split}[{idx}] normalized impact_type {processed['impact_type']!r} is outside the allowed inventory"
            )

        observed_labels.add(processed["impact_type"])

        if processed["article_id"] in seen_article_ids:
            raise ValueError(f"Duplicate article_id detected in {split}: {processed['article_id']}")
        if processed["example_id"] in seen_example_ids:
            raise ValueError(f"Duplicate example_id detected in {split}: {processed['example_id']}")

        seen_example_ids.add(processed["example_id"])
        seen_article_ids.add(processed["article_id"])
        if pk != processed["source_pk"]:
            raise AssertionError("source_pk mismatch after processing")
        processed_rows.append(processed)

    return processed_rows, {
        "missing_field_counts": dict(missing_field_counts),
        "observed_labels": sorted(observed_labels),
    }
