from __future__ import annotations

import json


def normalize_answer_text(text: str) -> str:
    return " ".join(text.split())


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


def parse_answer_prediction(text: str) -> dict | None:
    parsed = extract_first_json_object(text)
    if not isinstance(parsed, dict) or len(parsed) != 1:
        return None
    if "answer" not in parsed or not isinstance(parsed["answer"], str):
        return None
    return {
        "answer": parsed["answer"],
        "normalized_answer": normalize_answer_text(parsed["answer"]),
        "_format_valid": True,
    }
