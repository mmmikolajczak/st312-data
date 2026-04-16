from __future__ import annotations


PRICE_COLUMNS = [
    "date",
    "c_open",
    "c_high",
    "c_low",
    "n_close",
    "n_adj_close",
    "adj_sum_5",
    "adj_sum_10",
    "adj_sum_15",
    "adj_sum_20",
    "adj_sum_25",
    "adj_sum_30",
    "adjusted_close_price",
]


def render_price_history(rows: list[dict]) -> str:
    header = ",".join(PRICE_COLUMNS)
    body = []
    for row in rows:
        body.append(",".join(str(row[column]) for column in PRICE_COLUMNS))
    return "\n".join([header, *body])
