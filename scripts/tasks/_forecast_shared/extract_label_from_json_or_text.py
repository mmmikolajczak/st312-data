from __future__ import annotations

import re

from parse_binary_direction import extract_first_json_object, normalize_binary_direction


LABEL_PATTERN = re.compile(r"\b(Rise|Fall)\b", re.IGNORECASE)


def extract_label_from_json_or_text(text: str) -> dict | None:
    if not isinstance(text, str):
        return None

    parsed = extract_first_json_object(text)
    if isinstance(parsed, dict):
        for key in ["label", "answer"]:
            label = normalize_binary_direction(parsed.get(key))
            if label is not None:
                return {"label": label, "mode": "json"}

    matches = {normalize_binary_direction(match.group(0)) for match in LABEL_PATTERN.finditer(text)}
    matches.discard(None)
    if len(matches) != 1:
        return None
    label = next(iter(matches))
    return {"label": label, "mode": "text"}
