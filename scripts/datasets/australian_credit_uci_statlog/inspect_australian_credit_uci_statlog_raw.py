import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path("data/australian_credit_uci_statlog/raw")
REPORT_DIR = Path("reports/australian_credit_uci_statlog")
DAT_PATH = RAW_DIR / "australian.dat"
DOC_PATH = RAW_DIR / "australian.doc"

def parse_rows(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        toks = line.replace(",", " ").split()
        rows.append(toks)
    return rows

def detect_label_col(rows):
    ncols = len(rows[0])
    first_vals = {r[0] for r in rows}
    last_vals = {r[-1] for r in rows}
    if len(first_vals) == 2 and len(last_vals) != 2:
        return 0
    if len(last_vals) == 2 and len(first_vals) != 2:
        return ncols - 1
    return ncols - 1

def main():
    if not DAT_PATH.exists():
        raise SystemExit(f"Missing raw file: {DAT_PATH}")

    rows = parse_rows(DAT_PATH)
    col_lens = Counter(len(r) for r in rows)
    if len(col_lens) != 1:
        raise SystemExit(f"Inconsistent row widths: {dict(col_lens)}")

    ncols = next(iter(col_lens))
    label_col = detect_label_col(rows)
    raw_label_counts = Counter(r[label_col] for r in rows)
    feature_missing_token_count = sum(
        1 for r in rows for i, x in enumerate(r) if i != label_col and x == "?"
    )

    print("=" * 100)
    print("[RAW SUMMARY]")
    print("rows:", len(rows))
    print("columns:", ncols)
    print("detected_label_col:", label_col)
    print("raw_label_counts:", dict(raw_label_counts))
    print("feature_missing_token_count:", feature_missing_token_count)
    print("doc_exists:", DOC_PATH.exists())
    print("first_row:", rows[0])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "dataset_id": "australian_credit_uci_statlog_v0",
        "rows": len(rows),
        "columns": ncols,
        "detected_label_col": label_col,
        "raw_label_counts": dict(raw_label_counts),
        "feature_missing_token_count": feature_missing_token_count,
        "uci_missing_value_doc_ambiguity": {
            "uci_page_reports_missing_values": True,
            "recorded_note": "UCI page says there are a few missing values / has missing values; preserve ambiguity in metadata."
        },
        "raw_doc_present": DOC_PATH.exists(),
    }
    out = REPORT_DIR / "raw_audit_summary.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote raw audit summary: {out}")

if __name__ == "__main__":
    main()
