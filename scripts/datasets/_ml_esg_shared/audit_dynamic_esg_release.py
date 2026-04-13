from __future__ import annotations

from collections import Counter, defaultdict

from validate_dynamic_esg_release import LABEL_SANITY_RE


def _duplicate_audit(rows: list[dict], key: str) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(
            {
                "split": row["split"],
                "article_id": row["article_id"],
                "example_id": row["example_id"],
            }
        )
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    sample_items = []
    for value, entries in list(sorted(duplicates.items(), key=lambda item: (-len(item[1]), item[0])))[:10]:
        sample_items.append({"value": value, "entries": entries})
    return {
        "count": len(duplicates),
        "sample": sample_items,
    }


def _build_common_audit(
    processed_by_split: dict[str, list[dict]],
    validation_summary_by_split: dict[str, dict],
    *,
    label_getter,
    label_regex_pattern: str | None = None,
    label_regex_nonmatching: list[str] | None = None,
) -> dict:
    all_rows = []
    split_counts = {}
    label_frequencies = Counter()
    label_cardinality_distribution = Counter()
    article_ids_by_split = {}
    missing_field_counts = Counter()

    for split, rows in processed_by_split.items():
        split_counts[split] = len(rows)
        article_ids_by_split[split] = {row["article_id"] for row in rows}
        all_rows.extend(rows)
        for row in rows:
            labels = label_getter(row)
            label_frequencies.update(labels)
            label_cardinality_distribution[len(labels)] += 1
        missing_field_counts.update(validation_summary_by_split[split]["missing_field_counts"])

    label_inventory = sorted(label_frequencies)
    cross_split_duplicate_article_ids = {}
    split_names = list(processed_by_split)
    for idx, left in enumerate(split_names):
        for right in split_names[idx + 1:]:
            overlap = sorted(article_ids_by_split[left] & article_ids_by_split[right])
            cross_split_duplicate_article_ids[f"{left}__{right}"] = {
                "count": len(overlap),
                "sample": overlap[:20],
            }

    report = {
        "split_counts": split_counts,
        "label_inventory": label_inventory,
        "label_inventory_size": len(label_inventory),
        "label_frequencies": dict(sorted(label_frequencies.items())),
        "label_cardinality_distribution": {
            str(cardinality): count
            for cardinality, count in sorted(label_cardinality_distribution.items())
        },
        "cross_split_duplicate_article_ids": cross_split_duplicate_article_ids,
        "duplicate_headline_audit": _duplicate_audit(all_rows, "headline"),
        "duplicate_url_audit": _duplicate_audit(all_rows, "url"),
        "missing_field_counts": dict(missing_field_counts),
        "validation_summary_by_split": validation_summary_by_split,
    }
    if label_regex_pattern is not None and label_regex_nonmatching is not None:
        report["label_regex_sanity"] = {
            "pattern": label_regex_pattern,
            "nonmatching_labels": label_regex_nonmatching,
            "note": "Observed official labels are reported but not rejected merely for regex mismatch.",
        }
    return report


def build_ingest_audit(
    processed_by_split: dict[str, list[dict]],
    validation_summary_by_split: dict[str, dict],
) -> dict:
    label_inventory = sorted(
        {
            label
            for rows in processed_by_split.values()
            for row in rows
            for label in row["labels"]
        }
    )
    invalid_by_regex = [label for label in label_inventory if not LABEL_SANITY_RE.match(label)]
    return _build_common_audit(
        processed_by_split,
        validation_summary_by_split,
        label_getter=lambda row: row["labels"],
        label_regex_pattern=LABEL_SANITY_RE.pattern,
        label_regex_nonmatching=invalid_by_regex,
    )


def build_single_label_ingest_audit(
    processed_by_split: dict[str, list[dict]],
    validation_summary_by_split: dict[str, dict],
) -> dict:
    return _build_common_audit(
        processed_by_split,
        validation_summary_by_split,
        label_getter=lambda row: [row["impact_type"]],
    )
