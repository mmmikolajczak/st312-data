from __future__ import annotations

import json
from typing import Any


SCALE_INVENTORY = ["", "thousand", "million", "billion", "percent"]
ANSWER_TYPE_ALIASES = {
    "span": "span",
    "spans": "multi-span",
    "multi-span": "multi-span",
    "arithmetic": "arithmetic",
    "count": "count",
    "counting": "count",
}
ANSWER_FROM_INVENTORY = ["table", "text", "table-text"]
REQUIRED_KEYS = {
    "answer",
    "scale",
    "derivation",
    "answer_type",
    "answer_from",
    "rel_paragraphs",
    "req_comparison",
}


def extract_first_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def normalize_answer_type(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    return ANSWER_TYPE_ALIASES.get(key)


def normalize_answer_from(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    return key if key in ANSWER_FROM_INVENTORY else None


def normalize_scale(value: object) -> str | None:
    if value is None:
        return ""
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    return key if key in SCALE_INVENTORY else None


def normalize_answer(value: object) -> str | int | float | list[str] | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            if item is None or isinstance(item, bool):
                return None
            normalized.append(str(item).strip())
        return normalized
    return None


def normalize_rel_paragraphs(value: object) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if item is None or isinstance(item, bool):
            return None
        text = str(item).strip()
        if not text:
            continue
        if text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def normalize_prediction_obj(obj: object, allow_extra_keys: bool = False) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None

    keys = set(obj)
    if not REQUIRED_KEYS.issubset(keys):
        return None
    if not allow_extra_keys and keys != REQUIRED_KEYS:
        return None

    answer = normalize_answer(obj.get("answer"))
    scale = normalize_scale(obj.get("scale"))
    derivation = obj.get("derivation")
    answer_type = normalize_answer_type(obj.get("answer_type"))
    answer_from = normalize_answer_from(obj.get("answer_from"))
    rel_paragraphs = normalize_rel_paragraphs(obj.get("rel_paragraphs"))
    req_comparison = obj.get("req_comparison")

    if answer is None and obj.get("answer") is not None:
        return None
    if scale is None or answer_type is None or answer_from is None or rel_paragraphs is None:
        return None
    if derivation is None:
        derivation = ""
    if not isinstance(derivation, str):
        return None
    if not isinstance(req_comparison, bool):
        return None

    return {
        "answer": answer,
        "scale": scale,
        "derivation": derivation.strip(),
        "answer_type": answer_type,
        "answer_from": answer_from,
        "rel_paragraphs": rel_paragraphs,
        "req_comparison": req_comparison,
    }


def parse_prediction_text(text: str, allow_extra_keys: bool = False) -> dict[str, Any] | None:
    obj = extract_first_json_object(text)
    if obj is None:
        return None
    return normalize_prediction_obj(obj, allow_extra_keys=allow_extra_keys)


def prediction_to_official_pair(prediction: dict[str, Any] | None) -> list[Any] | None:
    if prediction is None:
        return None
    return [prediction["answer"], prediction["scale"]]
