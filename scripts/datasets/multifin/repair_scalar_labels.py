import argparse
import json
from pathlib import Path

def unwrap_label(label):
    if isinstance(label, str):
        return label, False
    if isinstance(label, dict) and len(label) == 1:
        (_, value), = label.items()
        if isinstance(value, str):
            return value, True
    return label, False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(Path("data/multifin/processed").glob("*.jsonl"))
    if not files:
        raise SystemExit("No files found under data/multifin/processed/*.jsonl")

    total_rows = 0
    total_fixed = 0

    for path in files:
        rows = []
        file_fixed = 0

        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                row = json.loads(line)
                total_rows += 1

                if "label" in row:
                    new_label, changed = unwrap_label(row["label"])
                    if changed:
                        row["label"] = new_label
                        file_fixed += 1
                        total_fixed += 1

                rows.append(row)

        print(f"[SCAN] {path} rows={len(rows)} fixed_labels={file_fixed}")

        if args.apply and file_fixed > 0:
            with path.open("w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[WRITE] {path}")

    print(f"[DONE] total_rows={total_rows} total_fixed={total_fixed}")
    if not args.apply:
        print("Re-run with --apply to write changes.")

if __name__ == "__main__":
    main()
