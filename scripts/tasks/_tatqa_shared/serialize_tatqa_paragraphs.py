from __future__ import annotations


def _normalize_text(text: object) -> str:
    value = "" if text is None else str(text)
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def serialize_tatqa_paragraphs(paragraphs: list[dict]) -> str:
    if not isinstance(paragraphs, list):
        raise ValueError("paragraphs must be a list")

    ordered = sorted(paragraphs, key=lambda p: int(p["order"]))
    blocks = []
    for paragraph in ordered:
        order = int(paragraph["order"])
        text = _normalize_text(paragraph.get("text", ""))
        blocks.append(f"[P{order}] {text}")
    return "\n\n".join(blocks)
