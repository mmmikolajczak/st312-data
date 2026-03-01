import json
from pathlib import Path

FILES = [
    Path("data/multifin/processed/multifin_highlevel_train_clean.jsonl"),
    Path("data/multifin/processed/multifin_highlevel_validation_clean.jsonl"),
    Path("data/multifin/processed/multifin_highlevel_test_clean.jsonl"),
]

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

for path in FILES:
    rows = []
    changed = 0
    total = 0
    for row in load_jsonl(path):
        total += 1
        if isinstance(row.get("label"), str):
            row["label"] = {"topic": row["label"]}
            changed += 1
        rows.append(row)
    write_jsonl(path, rows)
    print(f"[DONE] {path} repaired_rows={changed} total_rows={total}")
