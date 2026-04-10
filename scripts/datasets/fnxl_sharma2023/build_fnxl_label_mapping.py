import json
from pathlib import Path

LABELS_JSON = Path("data/fnxl_sharma2023/raw/release/labels.json")
LABEL_INVENTORY_JSON = Path("data/fnxl_sharma2023/processed/fnxl_label_inventory.json")
AGGREGATE_JSONL = Path("data/fnxl_sharma2023/processed/fnxl_release_raw_aggregate.jsonl")
OUT_JSON = Path("data/fnxl_sharma2023/processed/fnxl_label_id_mapping.json")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    if not LABELS_JSON.exists():
        raise SystemExit(f"Missing {LABELS_JSON}")
    if not LABEL_INVENTORY_JSON.exists():
        raise SystemExit(f"Missing {LABEL_INVENTORY_JSON}")
    if not AGGREGATE_JSONL.exists():
        raise SystemExit(f"Missing {AGGREGATE_JSONL}")

    labels_obj = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    inventory_obj = json.loads(LABEL_INVENTORY_JSON.read_text(encoding="utf-8"))

    if not isinstance(labels_obj, dict):
        raise SystemExit(f"Expected labels.json to be a dict, got {type(labels_obj).__name__}")

    authoritative_labels = {x["label"] for x in inventory_obj["labels"]}

    used_positive_ids = set()
    for rec in load_jsonl(AGGREGATE_JSONL):
        for m in rec["label"]["positive_mentions"]:
            used_positive_ids.add(int(m["label_id"]))

    label_to_id = {}
    for k, v in labels_obj.items():
        if not isinstance(v, int):
            continue
        label_to_id[k] = v

    id_to_raw_labels = {}
    for label_str, idx in label_to_id.items():
        id_to_raw_labels.setdefault(idx, []).append(label_str)

    def base_label(label_str: str):
        if label_str == "O":
            return "O"
        if label_str.startswith("B-") or label_str.startswith("I-"):
            return label_str[2:]
        return label_str

    used_id_records = []
    used_base_labels = set()
    unresolved_ids = []
    ids_with_multiple_base_candidates = []

    for idx in sorted(used_positive_ids):
        raw_labels = sorted(id_to_raw_labels.get(idx, []))
        base_candidates = sorted({base_label(x) for x in raw_labels if base_label(x) != "O"})

        chosen_base = None
        if len(base_candidates) == 1:
            chosen_base = base_candidates[0]
        elif len(base_candidates) > 1:
            ids_with_multiple_base_candidates.append({
                "label_id": idx,
                "raw_labels": raw_labels,
                "base_candidates": base_candidates,
            })
        else:
            unresolved_ids.append(idx)

        if chosen_base is not None:
            used_base_labels.add(chosen_base)

        used_id_records.append({
            "label_id": idx,
            "raw_labels": raw_labels,
            "base_candidates": base_candidates,
            "chosen_base_label": chosen_base,
            "in_authoritative_inventory": chosen_base in authoritative_labels if chosen_base is not None else False,
        })

    extra_base_labels_vs_authoritative = sorted(used_base_labels - authoritative_labels)
    missing_authoritative_labels_vs_used = sorted(authoritative_labels - used_base_labels)

    out = {
        "dataset_id": "fnxl_sharma2023_v0",
        "mapping_source": {
            "id_source": "labels.json",
            "authoritative_inventory_source": "fnxl_label_inventory.json",
            "used_id_source": "fnxl_release_raw_aggregate.jsonl",
        },
        "summary": {
            "authoritative_inventory_size": len(authoritative_labels),
            "observed_used_positive_label_id_count": len(used_positive_ids),
            "observed_min_label_id": min(used_positive_ids) if used_positive_ids else None,
            "observed_max_label_id": max(used_positive_ids) if used_positive_ids else None,
            "resolved_used_label_id_count": sum(1 for x in used_id_records if x["chosen_base_label"] is not None),
            "unresolved_used_label_id_count": len(unresolved_ids),
            "ids_with_multiple_base_candidates_count": len(ids_with_multiple_base_candidates),
            "resolved_used_base_label_count": len(used_base_labels),
            "extra_base_labels_vs_authoritative_count": len(extra_base_labels_vs_authoritative),
            "missing_authoritative_labels_vs_used_count": len(missing_authoritative_labels_vs_used),
        },
        "extra_base_labels_vs_authoritative": extra_base_labels_vs_authoritative[:100],
        "missing_authoritative_labels_vs_used": missing_authoritative_labels_vs_used[:100],
        "ids_with_multiple_base_candidates": ids_with_multiple_base_candidates[:50],
        "unresolved_used_label_ids_preview": unresolved_ids[:100],
        "id_records": used_id_records,
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote FNXL label-id mapping: {OUT_JSON}")
    print("[INFO] authoritative_inventory_size:", out["summary"]["authoritative_inventory_size"])
    print("[INFO] observed_used_positive_label_id_count:", out["summary"]["observed_used_positive_label_id_count"])
    print("[INFO] observed_min_label_id:", out["summary"]["observed_min_label_id"])
    print("[INFO] observed_max_label_id:", out["summary"]["observed_max_label_id"])
    print("[INFO] resolved_used_label_id_count:", out["summary"]["resolved_used_label_id_count"])
    print("[INFO] unresolved_used_label_id_count:", out["summary"]["unresolved_used_label_id_count"])
    print("[INFO] ids_with_multiple_base_candidates_count:", out["summary"]["ids_with_multiple_base_candidates_count"])
    print("[INFO] extra_base_labels_vs_authoritative_count:", out["summary"]["extra_base_labels_vs_authoritative_count"])
    print("[INFO] missing_authoritative_labels_vs_used_count:", out["summary"]["missing_authoritative_labels_vs_used_count"])


if __name__ == "__main__":
    main()
