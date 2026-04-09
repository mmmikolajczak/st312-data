import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RAW_DIR = Path("data/fincausal2020_official/raw")

FILES = {
    "task1_trial": RAW_DIR / "data/trial/fnp2020-fincausal-task1.csv",
    "task1_practice": RAW_DIR / "data/practice/fnp2020-fincausal2-task1.csv",
    "task1_evaluation": RAW_DIR / "data/evaluation/task1_blind.csv",
    "task2_trial": RAW_DIR / "data/trial/fnp2020-fincausal-task2.csv",
    "task2_practice": RAW_DIR / "data/practice/fnp2020-fincausal2-task2.csv",
    "task2_evaluation": RAW_DIR / "data/evaluation/task2_blind.csv",
}

def normalize_key(k: str) -> str:
    return k.strip().lower().replace(" ", "_")

def read_semicolon_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)
    if not rows:
        return [], []
    header = [h.strip() for h in rows[0]]
    data = rows[1:]
    dict_rows = []
    for row in data:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[:len(header)]
        dict_rows.append({normalize_key(h): v for h, v in zip(header, row)})
    return header, dict_rows

def base_task2_section_id(idx: str) -> str:
    idx = idx.strip()
    if re.fullmatch(r".+\.\d+", idx) and idx.count(".") >= 2:
        return idx.rsplit(".", 1)[0]
    return idx

def summarize_task1(name: str, path: Path):
    header, rows = read_semicolon_csv(path)
    blank_rows = []
    gold_counter = Counter()
    for r in rows:
        text = r.get("text", "").strip()
        gold = r.get("gold", "").strip()
        if text == "":
            blank_rows.append(r.get("index", ""))
        if gold != "":
            gold_counter[gold] += 1

    print("=" * 100)
    print(f"[TASK 1 FILE] {name}")
    print(f"path: {path}")
    print(f"header: {header}")
    print(f"row_count: {len(rows)}")
    print(f"blank_text_row_count: {len(blank_rows)}")
    print(f"blank_text_row_ids[:20]: {blank_rows[:20]}")
    print(f"gold_distribution: {dict(gold_counter)}")
    print("[sample_rows]")
    for r in rows[:2]:
        sample = {
            "index": r.get("index", ""),
            "text": r.get("text", "")[:220],
            "gold": r.get("gold", ""),
        }
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    print()

def summarize_task2(name: str, path: Path):
    header, rows = read_semicolon_csv(path)
    rows_per_base = Counter()
    multi_examples = []
    blank_text = 0
    blank_cause = 0
    blank_effect = 0

    for r in rows:
        idx = r.get("index", "")
        rows_per_base[base_task2_section_id(idx)] += 1
        if r.get("text", "").strip() == "":
            blank_text += 1
        if r.get("cause", "").strip() == "":
            blank_cause += 1
        if r.get("effect", "").strip() == "":
            blank_effect += 1

    multi = {k: v for k, v in rows_per_base.items() if v > 1}
    multi_examples = list(sorted(multi.items()))[:20]

    print("=" * 100)
    print(f"[TASK 2 FILE] {name}")
    print(f"path: {path}")
    print(f"header: {header}")
    print(f"row_count: {len(rows)}")
    print(f"blank_text_count: {blank_text}")
    print(f"blank_cause_count: {blank_cause}")
    print(f"blank_effect_count: {blank_effect}")
    print(f"base_section_count: {len(rows_per_base)}")
    print(f"multi_pair_section_count: {len(multi)}")
    print(f"multi_pair_examples[:20]: {multi_examples}")
    print("[sample_rows]")
    for r in rows[:2]:
        sample = {
            "index": r.get("index", ""),
            "text": r.get("text", "")[:220],
            "cause": r.get("cause", "")[:160],
            "effect": r.get("effect", "")[:160],
            "sentence": r.get("sentence", "")[:220],
        }
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    print()

def main():
    for key in ["task1_trial", "task1_practice", "task1_evaluation"]:
        summarize_task1(key, FILES[key])

    for key in ["task2_trial", "task2_practice", "task2_evaluation"]:
        summarize_task2(key, FILES[key])

    meta_path = RAW_DIR / "fincausal2020_ingest_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        print("=" * 100)
        print("[INGEST META SUMMARY]")
        print(json.dumps({
            "dataset_id": meta["dataset_id"],
            "n_downloads": len(meta["downloads"]),
            "downloads_preview": meta["downloads"][:10],
        }, ensure_ascii=False, indent=2))
        print()

if __name__ == "__main__":
    main()
