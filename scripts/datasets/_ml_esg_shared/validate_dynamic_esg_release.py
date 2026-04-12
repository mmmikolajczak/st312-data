from __future__ import annotations

import re
from collections import Counter


REQUIRED_KEYS = ["pk", "URL", "News_Headline", "ESG_Category"]
LABEL_SANITY_RE = re.compile(r"^(?:[ESG]\d{2}|NN)$")


def make_article_id(pk: int) -> str:
    return f"dynamicesg_bt_{pk}"


def make_example_id(dataset_id: str, split: str, article_id: str) -> str:
    return f"{dataset_id}__{split}__{article_id}"


def normalize_label_code(value: str) -> str:
    return str(value).strip().upper()


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
