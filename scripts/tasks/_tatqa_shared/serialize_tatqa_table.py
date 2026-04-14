from __future__ import annotations


def _normalize_cell(cell: object) -> str:
    text = "" if cell is None else str(cell)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ").replace("\n", " \\n ")
    return text.strip()


def serialize_tatqa_table(table: list[list[object]]) -> str:
    if not isinstance(table, list):
        raise ValueError("table must be a list of rows")

    rows: list[str] = []
    for row in table:
        if not isinstance(row, list):
            raise ValueError("table rows must be lists")
        rows.append("\t".join(_normalize_cell(cell) for cell in row))
    return "\n".join(rows)
