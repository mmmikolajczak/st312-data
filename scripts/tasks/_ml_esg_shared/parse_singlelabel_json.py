from __future__ import annotations

from normalize_labels import canonicalize_single_label
from parse_multilabel_json import extract_first_json_object


ALIAS_KEYS = ["impact_type", "label", "impact", "impactType"]


def parse_keyed_singlelabel_prediction(
    text: str,
    allowed_labels: list[str],
    alias_keys: list[str],
) -> str | None:
    obj = extract_first_json_object(text)
    if obj is None:
        return None

    present_aliases = [key for key in alias_keys if key in obj]
    if len(present_aliases) != 1:
        return None
    alias_key = present_aliases[0]
    if set(obj.keys()) != {alias_key}:
        return None

    return canonicalize_single_label(obj[alias_key], allowed_labels)


def parse_singlelabel_prediction(text: str, allowed_labels: list[str]) -> str | None:
    return parse_keyed_singlelabel_prediction(text, allowed_labels, ALIAS_KEYS)
