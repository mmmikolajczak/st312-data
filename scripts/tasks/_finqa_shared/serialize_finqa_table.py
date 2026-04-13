from __future__ import annotations


def _escape_cell(cell: object) -> str:
    text = str(cell)
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def serialize_finqa_table(table: list[list[object]]) -> str:
    """Deterministically serialize the raw 2D table into a loss-minimizing TSV string."""
    return "\n".join("\t".join(_escape_cell(cell) for cell in row) for row in table)
