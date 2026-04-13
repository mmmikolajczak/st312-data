from __future__ import annotations


def normalize_label_code(value: str) -> str:
    return str(value).strip().upper()


def normalize_text_label(value: str) -> str:
    return " ".join(str(value).split())


def canonicalize_label_list(values, allowed_labels: set[str] | None = None) -> list[str] | None:
    if not isinstance(values, list):
        return None

    normalized = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            return None
        label = normalize_label_code(value)
        if not label:
            return None
        if allowed_labels is not None and label not in allowed_labels:
            return None
        if label not in seen:
            seen.add(label)
            normalized.append(label)
    return sorted(normalized)


def canonicalize_single_label(value, allowed_labels: list[str] | set[str]) -> str | None:
    if not isinstance(value, str):
        return None

    allowed_sequence = list(allowed_labels)
    allowed_map = {normalize_text_label(label).casefold(): label for label in allowed_sequence}
    normalized = normalize_text_label(value)
    if not normalized:
        return None
    return allowed_map.get(normalized.casefold())
