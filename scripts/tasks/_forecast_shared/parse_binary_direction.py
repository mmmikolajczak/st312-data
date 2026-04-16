from __future__ import annotations

import json


ALLOWED_LABELS = {"rise": "Rise", "fall": "Fall"}


def extract_first_json_object(text: str):
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                snippet = text[start : idx + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    return None
    return None


def normalize_binary_direction(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = ALLOWED_LABELS.get(value.strip().lower())
    return normalized


def parse_label_prediction(text: str) -> dict | None:
    parsed = extract_first_json_object(text)
    if not isinstance(parsed, dict) or len(parsed) != 1:
        return None
    label = normalize_binary_direction(parsed.get("label"))
    if label is None:
        return None
    return {
        "label": label,
        "_format_valid": True,
    }
