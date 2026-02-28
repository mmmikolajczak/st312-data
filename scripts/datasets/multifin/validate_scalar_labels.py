import json
from pathlib import Path
from collections import Counter

files = sorted(Path("data/multifin/processed").glob("*.jsonl"))
if not files:
    raise SystemExit("No files found under data/multifin/processed/*.jsonl")

bad = 0

for path in files:
    n = 0
    non_string = 0
    empty_string = 0
    label_counter = Counter()

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            row = json.loads(line)
            n += 1
            label = row.get("label")

            if not isinstance(label, str):
                non_string += 1
                bad += 1
                continue

            if not label.strip():
                empty_string += 1
                bad += 1
                continue

            label_counter[label] += 1

    print("=" * 80)
    print(f"[CHECK] {path}")
    print(f"[CHECK] rows={n}")
    print(f"[CHECK] non_string_labels={non_string}")
    print(f"[CHECK] empty_string_labels={empty_string}")
    print(f"[CHECK] labels={sorted(label_counter)}")

if bad:
    raise SystemExit(f"[FAIL] Found {bad} invalid labels across MultiFin processed files.")
print("[OK] All MultiFin processed labels are scalar non-empty strings.")
