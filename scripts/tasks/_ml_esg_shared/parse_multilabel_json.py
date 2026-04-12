from __future__ import annotations

import json
from json import JSONDecodeError, JSONDecoder

from normalize_labels import canonicalize_label_list


JSON_DECODER = JSONDecoder()
ALIAS_KEYS = ["esg_categories", "labels", "issues", "esg_labels"]


def extract_first_json_object(text: str) -> dict | None:
    if not isinstance(text, str):
        return None
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = JSON_DECODER.raw_decode(text[idx:])
        except JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def parse_multilabel_prediction(text: str, allowed_labels: set[str]) -> list[str] | None:
    obj = extract_first_json_object(text)
    if obj is None:
        return None

    present_aliases = [key for key in ALIAS_KEYS if key in obj]
    if len(present_aliases) != 1:
        return None
    alias_key = present_aliases[0]
    if set(obj.keys()) != {alias_key}:
        return None

    normalized = canonicalize_label_list(obj[alias_key], allowed_labels=allowed_labels)
    if normalized is None:
        return None
    return normalized
