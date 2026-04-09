import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RAW_DIR = Path("data/fincausal2020_official/raw")
PROCESSED_DIR = Path("data/fincausal2020_official/processed")

TASK1_ALL_CLEAN_PATH = PROCESSED_DIR / "fincausal2020_task1_all_clean.jsonl"
TASK2_ALL_CLEAN_PATH = PROCESSED_DIR / "fincausal2020_task2_all_clean.jsonl"
CLEAN_META_PATH = PROCESSED_DIR / "fincausal2020_clean_meta.json"

TASK1_FILES = {
    "trial": RAW_DIR / "data/trial/fnp2020-fincausal-task1.csv",
    "practice": RAW_DIR / "data/practice/fnp2020-fincausal2-task1.csv",
    "evaluation": RAW_DIR / "data/evaluation/task1_blind.csv",
}

TASK2_FILES = {
    "trial": RAW_DIR / "data/trial/fnp2020-fincausal-task2.csv",
    "practice": RAW_DIR / "data/practice/fnp2020-fincausal2-task2.csv",
    "evaluation": RAW_DIR / "data/evaluation/task2_blind.csv",
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


def parse_optional_int(x: str):
    x = x.strip()
    if x == "":
        return None
    return int(x)


def normalize_gold_binary(x: str):
    x = x.strip()
    if x == "":
        return None
    if x not in {"0", "1"}:
        raise ValueError(f"Unexpected Task 1 gold label: {x!r}")
    return int(x)


def task1_record(split: str, row: dict):
    raw_index = row["index"].strip()
    text = row.get("text", "")
    gold = normalize_gold_binary(row.get("gold", ""))

    return {
        "example_id": f"fincausal2020_task1_{split}_{raw_index}",
        "data": {
            "text": text,
        },
        "label": {
            "gold": gold,
            "has_gold": gold is not None,
        },
        "meta": {
            "task": "task1",
            "split": split,
            "raw_index": raw_index,
            "source_file": str(TASK1_FILES[split].relative_to(RAW_DIR)),
        },
    }


def task2_record(split: str, row: dict):
    raw_index = row["index"].strip()
    base_index = base_task2_section_id(raw_index)

    cause = row.get("cause", "")
    effect = row.get("effect", "")
    sentence_markup = row.get("sentence", "")

    has_gold = (cause.strip() != "" and effect.strip() != "")

    return {
        "example_id": f"fincausal2020_task2_{split}_{raw_index}",
        "data": {
            "text": row.get("text", ""),
            "sentence_markup": sentence_markup,
            "offset_sentence2": parse_optional_int(row.get("offset_sentence2", "")),
            "offset_sentence3": parse_optional_int(row.get("offset_sentence3", "")),
        },
        "label": {
            "cause": cause if has_gold else None,
            "effect": effect if has_gold else None,
            "cause_start": parse_optional_int(row.get("cause_start", "")),
            "cause_end": parse_optional_int(row.get("cause_end", "")),
            "effect_start": parse_optional_int(row.get("effect_start", "")),
            "effect_end": parse_optional_int(row.get("effect_end", "")),
            "has_gold": has_gold,
        },
        "meta": {
            "task": "task2",
            "split": split,
            "raw_index": raw_index,
            "base_section_id": base_index,
            "source_file": str(TASK2_FILES[split].relative_to(RAW_DIR)),
        },
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    task1_records = []
    task2_records = []

    task1_counts_raw = Counter()
    task1_counts_kept = Counter()
    task1_blank_removed = defaultdict(list)
    task1_gold_counts = defaultdict(Counter)
    task1_positive_ids = defaultdict(set)

    task2_counts = Counter()
    task2_gold_counts = Counter()
    task2_base_counts = Counter()
    task2_multi_pair_counts = Counter()

    # Task 1
    for split, path in TASK1_FILES.items():
        _, rows = read_semicolon_csv(path)
        task1_counts_raw[split] = len(rows)

        for row in rows:
            rec = task1_record(split, row)
            text = rec["data"]["text"].strip()
            raw_index = rec["meta"]["raw_index"]

            if text == "":
                task1_blank_removed[split].append(raw_index)
                continue

            task1_records.append(rec)
            task1_counts_kept[split] += 1

            if rec["label"]["gold"] is not None:
                task1_gold_counts[split][str(rec["label"]["gold"])] += 1
                if rec["label"]["gold"] == 1:
                    task1_positive_ids[split].add(raw_index)

    # Task 2
    task2_base_ids = defaultdict(set)
    task2_rows_per_base = defaultdict(Counter)

    for split, path in TASK2_FILES.items():
        _, rows = read_semicolon_csv(path)
        task2_counts[split] = len(rows)

        for row in rows:
            rec = task2_record(split, row)
            task2_records.append(rec)

            if rec["label"]["has_gold"]:
                task2_gold_counts[split] += 1

            base_idx = rec["meta"]["base_section_id"]
            task2_base_ids[split].add(base_idx)
            task2_rows_per_base[split][base_idx] += 1

    for split in TASK2_FILES:
        task2_base_counts[split] = len(task2_base_ids[split])
        task2_multi_pair_counts[split] = sum(1 for _, c in task2_rows_per_base[split].items() if c > 1)

    linkage = {}
    for split in ["trial", "practice"]:
        t1_pos = task1_positive_ids[split]
        t2_base = task2_base_ids[split]
        linkage[split] = {
            "task1_positive_count": len(t1_pos),
            "task2_base_section_count": len(t2_base),
            "task2_base_equals_task1_positive": t2_base == t1_pos,
            "missing_in_task2_from_task1_positive": sorted(t1_pos - t2_base)[:50],
            "extra_in_task2_vs_task1_positive": sorted(t2_base - t1_pos)[:50],
        }

    clean_meta = {
        "dataset_id": "fincausal2020_official_v0",
        "split_policy": {
            "type": "author_provided_split",
            "trial": "preserved",
            "practice": "preserved",
            "evaluation": "preserved_blind",
        },
        "task1": {
            "raw_counts": dict(task1_counts_raw),
            "kept_counts_after_blank_filter": dict(task1_counts_kept),
            "blank_text_rows_removed": {k: v for k, v in task1_blank_removed.items()},
            "gold_distribution": {k: dict(v) for k, v in task1_gold_counts.items()},
        },
        "task2": {
            "row_counts": dict(task2_counts),
            "gold_row_counts": dict(task2_gold_counts),
            "base_section_counts": dict(task2_base_counts),
            "multi_pair_section_counts": dict(task2_multi_pair_counts),
        },
        "task_linkage_checks": linkage,
        "notes": [
            "Task 1 blank-text rows were removed during ingestion.",
            "Task 2 is stored row-wise as causal-pair extraction; repeated base section IDs are preserved.",
            "Evaluation split is blind: Task 1 has no Gold column values; Task 2 has no cause/effect labels.",
        ],
    }

    with TASK1_ALL_CLEAN_PATH.open("w", encoding="utf-8") as f:
        for rec in task1_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with TASK2_ALL_CLEAN_PATH.open("w", encoding="utf-8") as f:
        for rec in task2_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    CLEAN_META_PATH.write_text(json.dumps(clean_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote task1 all-clean JSONL: {TASK1_ALL_CLEAN_PATH}")
    print(f"[DONE] Wrote task2 all-clean JSONL: {TASK2_ALL_CLEAN_PATH}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META_PATH}")
    print(f"[INFO] Task 1 kept counts: {dict(task1_counts_kept)}")
    print(f"[INFO] Task 2 row counts: {dict(task2_counts)}")
    print(f"[INFO] Task 2 gold row counts: {dict(task2_gold_counts)}")
    print(f"[INFO] Task 2 base section counts: {dict(task2_base_counts)}")


if __name__ == "__main__":
    main()
