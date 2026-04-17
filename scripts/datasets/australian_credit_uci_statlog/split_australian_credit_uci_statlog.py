import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

IN_PATH = Path("data/australian_credit_uci_statlog/processed/australian_credit_all_clean.jsonl")
OUT_DIR = Path("data/australian_credit_uci_statlog/processed")
TARGET = {"train": 482, "valid": 69, "test": 139}
SEED = 42

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def save_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for rec in rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def proportional_counts(total_by_label, target_total):
    total = sum(total_by_label.values())
    exact = {k: total_by_label[k] * target_total / total for k in total_by_label}
    floors = {k: int(exact[k]) for k in total_by_label}
    remainder = target_total - sum(floors.values())
    ranked = sorted(total_by_label.keys(), key=lambda k: (exact[k] - floors[k]), reverse=True)
    for k in ranked[:remainder]:
        floors[k] += 1
    return floors

def try_load_flare_wrapper():
    try:
        from datasets import load_dataset
    except Exception:
        return None, "datasets_library_unavailable"
    try:
        ds = load_dataset("TheFinAI/flare-australian")
    except Exception as e:
        return None, f"flare_load_failed:{type(e).__name__}"
    return ds, "ok"

def extract_feature_tuple_from_text(text):
    if not isinstance(text, str):
        return None
    found = re.findall(r"A(\d+)\s*[:=]\s*([^,\n;]+)", text)
    if not found:
        return None
    vals = {}
    for k, v in found:
        vals[int(k)] = v.strip()
    if set(vals.keys()) != set(range(1, 15)):
        return None
    return tuple(vals[i] for i in range(1, 15))

def attempt_exact_membership(records):
    ds, status = try_load_flare_wrapper()
    if ds is None:
        return None, {"attempted": True, "status": status}

    tuple_to_ids = defaultdict(list)
    for rec in records:
        tup = tuple(rec["data"]["features"][f"A{i}"] for i in range(1, 15))
        tuple_to_ids[tup].append(rec["example_id"])

    split_members = {}
    unresolved = 0
    dup = 0

    for split in ["train", "valid", "test"]:
        ids = []
        for row in ds[split]:
            tup = extract_feature_tuple_from_text(row.get("text"))
            if tup is None:
                unresolved += 1
                continue
            candidates = tuple_to_ids.get(tup, [])
            if len(candidates) == 1:
                ids.append(candidates[0])
            elif len(candidates) > 1:
                dup += 1
            else:
                unresolved += 1
        split_members[split] = ids

    exact_ok = (
        unresolved == 0 and dup == 0 and
        len(split_members["train"]) == TARGET["train"] and
        len(split_members["valid"]) == TARGET["valid"] and
        len(split_members["test"]) == TARGET["test"]
    )

    return (split_members if exact_ok else None), {
        "attempted": True,
        "status": status,
        "unresolved_count": unresolved,
        "duplicate_match_count": dup,
        "matched_counts": {k: len(v) for k, v in split_members.items()},
        "exact_membership_verified": exact_ok,
    }

def stratified_count_matched_split(records):
    rng = random.Random(SEED)
    by_label = defaultdict(list)
    for rec in records:
        by_label[rec["label"]["label_id"]].append(rec)
    for lab in by_label:
        rng.shuffle(by_label[lab])

    total_by_label = {lab: len(rows) for lab, rows in by_label.items()}
    train_counts = proportional_counts(total_by_label, TARGET["train"])
    rem_after_train = {lab: total_by_label[lab] - train_counts[lab] for lab in total_by_label}
    valid_counts = proportional_counts(rem_after_train, TARGET["valid"])
    test_counts = {lab: rem_after_train[lab] - valid_counts[lab] for lab in total_by_label}

    splits = {"train": [], "valid": [], "test": []}
    for lab, rows in by_label.items():
        a = train_counts[lab]
        b = a + valid_counts[lab]
        splits["train"].extend(rows[:a])
        splits["valid"].extend(rows[a:b])
        splits["test"].extend(rows[b:])

    for split in splits:
        splits[split] = sorted(splits[split], key=lambda r: r["data"]["row_id"])

    return splits, {
        "seed": SEED,
        "per_label_allocations": {
            "train": train_counts,
            "valid": valid_counts,
            "test": test_counts,
        },
    }

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = list(load_jsonl(IN_PATH))
    exact_members, exact_audit = attempt_exact_membership(records)
    by_id = {r["example_id"]: r for r in records}

    if exact_members is not None:
        split_policy = "finben_exact_membership"
        splits = {k: [by_id[x] for x in v] for k, v in exact_members.items()}
        split_aux = {"exact_alignment_audit": exact_audit}
    else:
        split_policy = "finben_count_matched_reconstruction"
        splits, recon = stratified_count_matched_split(records)
        split_aux = {
            "exact_alignment_audit": exact_audit,
            "count_matched_reconstruction": recon,
        }

    for split, rows in splits.items():
        path = OUT_DIR / f"australian_credit_{split}.jsonl"
        save_jsonl(path, rows)
        print(f"[DONE] Wrote {split} JSONL: {path} ({len(rows)} rows)")

    manifest = {
        "dataset_id": "australian_credit_uci_statlog_v0",
        "split_policy": split_policy,
        "target_counts": TARGET,
        "actual_counts": {k: len(v) for k, v in splits.items()},
        "label_balance": {
            split: dict(Counter(r["label"]["label"] for r in rows))
            for split, rows in splits.items()
        },
        **split_aux,
    }
    manifest_path = OUT_DIR / "australian_credit_split_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Wrote split manifest: {manifest_path}")
    print("[INFO] split_policy:", split_policy)
    print("[INFO] actual_counts:", {k: len(v) for k, v in splits.items()})
    print("[INFO] label_balance:", json.dumps(manifest["label_balance"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
