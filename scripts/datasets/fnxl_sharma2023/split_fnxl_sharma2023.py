import json
import random
from collections import Counter, defaultdict, deque
from pathlib import Path

AGGREGATE_PATH = Path("data/fnxl_sharma2023/processed/fnxl_release_raw_aggregate.jsonl")
LABEL_INVENTORY_PATH = Path("data/fnxl_sharma2023/processed/fnxl_label_inventory.json")
PROCESSED_DIR = Path("data/fnxl_sharma2023/processed")

TRAIN_PATH = PROCESSED_DIR / "fnxl_clean_company_split_train.jsonl"
TEST_PATH = PROCESSED_DIR / "fnxl_clean_company_split_test.jsonl"
MANIFEST_PATH = PROCESSED_DIR / "fnxl_clean_company_split_manifest.json"
TRAIN_COMPANIES_PATH = PROCESSED_DIR / "fnxl_clean_company_split_train_companies.json"
TEST_COMPANIES_PATH = PROCESSED_DIR / "fnxl_clean_company_split_test_companies.json"
TRAIN_FILES_PATH = PROCESSED_DIR / "fnxl_clean_company_split_train_files.json"
TEST_FILES_PATH = PROCESSED_DIR / "fnxl_clean_company_split_test_files.json"

SEED = 42
TRAIN_FRACTION = 0.80
TOP_K_FREQUENT_LABELS = 25


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    if not AGGREGATE_PATH.exists():
        raise SystemExit(f"Missing aggregate file: {AGGREGATE_PATH}")
    if not LABEL_INVENTORY_PATH.exists():
        raise SystemExit(f"Missing label inventory: {LABEL_INVENTORY_PATH}")

    random.seed(SEED)

    records = list(load_jsonl(AGGREGATE_PATH))
    label_inventory = json.loads(LABEL_INVENTORY_PATH.read_text(encoding="utf-8"))
    top_labels = [x["label"] for x in sorted(label_inventory["labels"], key=lambda r: (-r["count"], r["rank"]))[:TOP_K_FREQUENT_LABELS]]
    label_name_by_id = {i + 1: x["label"] for i, x in enumerate(sorted(label_inventory["labels"], key=lambda r: r["rank"]))}

    # Build bipartite graph company <-> file
    company_to_files = defaultdict(set)
    file_to_companies = defaultdict(set)

    for rec in records:
        c = rec["meta"]["company_group_key"]
        f = rec["meta"]["fileName"]
        company_to_files[c].add(f)
        file_to_companies[f].add(c)

    # Connected components ensure both company and file disjointness.
    components = []
    seen_companies = set()
    for company in company_to_files:
        if company in seen_companies:
            continue

        q = deque([("company", company)])
        comp_companies = set()
        comp_files = set()

        while q:
            node_type, node = q.popleft()
            if node_type == "company":
                if node in comp_companies:
                    continue
                comp_companies.add(node)
                seen_companies.add(node)
                for f in company_to_files[node]:
                    if f not in comp_files:
                        q.append(("file", f))
            else:
                if node in comp_files:
                    continue
                comp_files.add(node)
                for c in file_to_companies[node]:
                    if c not in comp_companies:
                        q.append(("company", c))

        components.append({
            "companies": comp_companies,
            "files": comp_files,
        })

    file_to_component = {}
    company_to_component = {}
    for idx, comp in enumerate(components):
        for c in comp["companies"]:
            company_to_component[c] = idx
        for f in comp["files"]:
            file_to_component[f] = idx

    component_stats = []
    total_rows = 0
    total_pos = 0
    top_label_totals = Counter()

    for idx, comp in enumerate(components):
        rows = 0
        pos = 0
        label_counts = Counter()

        for rec in records:
            if file_to_component[rec["meta"]["fileName"]] != idx:
                continue
            rows += 1
            mentions = rec["label"]["positive_mentions"]
            pos += len(mentions)
            for m in mentions:
                lbl_name = label_name_by_id.get(m["label_id"])
                if lbl_name in top_labels:
                    label_counts[lbl_name] += 1

        total_rows += rows
        total_pos += pos
        top_label_totals.update(label_counts)

        component_stats.append({
            "component_id": idx,
            "companies": sorted(comp["companies"]),
            "files": sorted(comp["files"]),
            "rows": rows,
            "positive_mentions": pos,
            "top_label_counts": dict(label_counts),
        })

    target_train_rows = total_rows * TRAIN_FRACTION
    target_train_pos = total_pos * TRAIN_FRACTION

    def score_if_assign(train_rows, train_pos, train_top_counts, comp, to_train: bool):
        if to_train:
            rows = train_rows + comp["rows"]
            pos = train_pos + comp["positive_mentions"]
            top_counts = Counter(train_top_counts)
            top_counts.update(comp["top_label_counts"])
        else:
            rows = train_rows
            pos = train_pos
            top_counts = Counter(train_top_counts)

        row_term = abs(rows - target_train_rows) / max(target_train_rows, 1.0)
        pos_term = abs(pos - target_train_pos) / max(target_train_pos, 1.0)

        label_terms = []
        for lbl in top_labels:
            total_lbl = top_label_totals.get(lbl, 0)
            if total_lbl <= 0:
                continue
            train_share = top_counts.get(lbl, 0) / total_lbl
            label_terms.append(abs(train_share - TRAIN_FRACTION))
        label_term = (sum(label_terms) / len(label_terms)) if label_terms else 0.0

        return row_term + pos_term + 0.25 * label_term

    components_sorted = sorted(
        component_stats,
        key=lambda c: (c["rows"], c["positive_mentions"], len(c["companies"]), len(c["files"])),
        reverse=True,
    )

    train_component_ids = set()
    train_rows = 0
    train_pos = 0
    train_top_counts = Counter()

    for comp in components_sorted:
        score_train = score_if_assign(train_rows, train_pos, train_top_counts, comp, True)
        score_test = score_if_assign(train_rows, train_pos, train_top_counts, comp, False)

        assign_to_train = score_train <= score_test
        if assign_to_train:
            train_component_ids.add(comp["component_id"])
            train_rows += comp["rows"]
            train_pos += comp["positive_mentions"]
            train_top_counts.update(comp["top_label_counts"])

    train_records = []
    test_records = []

    train_companies = set()
    test_companies = set()
    train_files = set()
    test_files = set()
    train_label_counts = Counter()
    test_label_counts = Counter()
    train_pos_mentions = 0
    test_pos_mentions = 0

    for rec in records:
        comp_id = file_to_component[rec["meta"]["fileName"]]
        out_rec = dict(rec)
        out_rec["meta"] = dict(rec["meta"])
        if comp_id in train_component_ids:
            out_rec["meta"]["canonical_split"] = "train"
            train_records.append(out_rec)
            train_companies.add(out_rec["meta"]["company_group_key"])
            train_files.add(out_rec["meta"]["fileName"])
            train_pos_mentions += out_rec["label"]["n_positive_mentions"]
            for m in out_rec["label"]["positive_mentions"]:
                train_label_counts[m["label_id"]] += 1
        else:
            out_rec["meta"]["canonical_split"] = "test"
            test_records.append(out_rec)
            test_companies.add(out_rec["meta"]["company_group_key"])
            test_files.add(out_rec["meta"]["fileName"])
            test_pos_mentions += out_rec["label"]["n_positive_mentions"]
            for m in out_rec["label"]["positive_mentions"]:
                test_label_counts[m["label_id"]] += 1

    company_overlap = sorted(train_companies & test_companies)
    file_overlap = sorted(train_files & test_files)

    with TRAIN_PATH.open("w", encoding="utf-8") as f:
        for rec in train_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with TEST_PATH.open("w", encoding="utf-8") as f:
        for rec in test_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    TRAIN_COMPANIES_PATH.write_text(json.dumps(sorted(train_companies), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TEST_COMPANIES_PATH.write_text(json.dumps(sorted(test_companies), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TRAIN_FILES_PATH.write_text(json.dumps(sorted(train_files), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TEST_FILES_PATH.write_text(json.dumps(sorted(test_files), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def summarize_label_coverage(counter):
        used = set(counter)
        return {
            "distinct_used_labels": len(used),
            "top10_label_ids_by_mass": [[int(k), int(v)] for k, v in counter.most_common(10)],
        }

    manifest = {
        "dataset_id": "fnxl_sharma2023_v0",
        "seed": SEED,
        "grouping_strategy": {
            "primary_group_key": "company",
            "audit_key": "fileName",
            "actual_assignment_unit": "connected_components_of_company_file_graph",
        },
        "target_train_fraction": TRAIN_FRACTION,
        "totals": {
            "rows": len(records),
            "positive_mentions": sum(r["label"]["n_positive_mentions"] for r in records),
            "components": len(component_stats),
        },
        "split_counts": {
            "train": {
                "rows": len(train_records),
                "companies": len(train_companies),
                "files": len(train_files),
                "positive_mentions": train_pos_mentions,
            },
            "test": {
                "rows": len(test_records),
                "companies": len(test_companies),
                "files": len(test_files),
                "positive_mentions": test_pos_mentions,
            },
        },
        "overlap_checks": {
            "company_overlap_count": len(company_overlap),
            "file_overlap_count": len(file_overlap),
            "company_overlap_preview": company_overlap[:20],
            "file_overlap_preview": file_overlap[:20],
        },
        "label_coverage_summary": {
            "train": summarize_label_coverage(train_label_counts),
            "test": summarize_label_coverage(test_label_counts),
        },
        "top_k_frequent_label_balance": {
            "top_k": TOP_K_FREQUENT_LABELS,
            "labels": top_labels,
            "train_counts": {lbl: int(train_top_counts.get(lbl, 0)) for lbl in top_labels},
            "total_counts": {lbl: int(top_label_totals.get(lbl, 0)) for lbl in top_labels},
        },
        "membership_files": {
            "train_companies": str(TRAIN_COMPANIES_PATH),
            "test_companies": str(TEST_COMPANIES_PATH),
            "train_files": str(TRAIN_FILES_PATH),
            "test_files": str(TEST_FILES_PATH),
        },
        "notes": [
            "Original release split was preserved in the raw aggregate but not used as canonical evaluation due to leakage.",
            "Canonical split is grouped 80/20 and enforces both company and file disjointness.",
            "Exact preservation of long-tail label frequencies is not expected for this extreme label space.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote canonical train split: {TRAIN_PATH}")
    print(f"[DONE] Wrote canonical test split: {TEST_PATH}")
    print(f"[DONE] Wrote split manifest: {MANIFEST_PATH}")
    print(f"[INFO] train_rows: {len(train_records)}")
    print(f"[INFO] test_rows: {len(test_records)}")
    print(f"[INFO] company_overlap_count: {len(company_overlap)}")
    print(f"[INFO] file_overlap_count: {len(file_overlap)}")


if __name__ == "__main__":
    main()
