from __future__ import annotations

import math


def normalize_finqa_answer(value: object) -> str:
    if value is None:
        return "n/a"

    if isinstance(value, bool):
        return "yes" if value else "no"

    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return "n/a"
        text = f"{round(float(value), 5):.5f}".rstrip("0").rstrip(".")
        return text or "0"

    text = str(value).strip()
    lower = text.lower()
    if lower in {"yes", "no", "n/a"}:
        return lower

    numeric_candidate = text.replace(",", "")
    try:
        num = float(numeric_candidate)
    except ValueError:
        return text

    text = f"{round(num, 5):.5f}".rstrip("0").rstrip(".")
    return text or "0"
