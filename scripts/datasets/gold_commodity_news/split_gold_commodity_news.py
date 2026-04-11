import json
import random
from collections import Counter, defaultdict, deque
from pathlib import Path

CLEAN_JSONL = Path("data/gold_commodity_news/processed/gold_commodity_news_clean.jsonl")
CLEAN_META = Path("data/gold_commodity_news/processed/gold_commodity_news_clean_meta.json")
PROCESSED_DIR = Path("data/gold_commodity_news/processed")

TRAIN_JSONL = PROCESSED_DIR / "gold_commodity_news_train.jsonl"
TEST_JSONL = PROCESSED_DIR / "gold_commodity_news_test.jsonl"
MANIFEST_JSON = PROCESSED_DIR / "gold_commodity_news_split_manifest.json"
TRAIN_URLS_JSON = PROCESSED_DIR / "gold_commodity_news_train_urls.json"
TEST_URLS_JSON = PROCESSED_DIR / "gold_commodity_news_test_urls.json"
TRAIN_HEADLINES_JSON = PROCESSED_DIR / "gold_commodity_news_train_headlines.json"
TEST_HEADLINES_JSON = PROCESSED_DIR / "gold_commodity_news_test_headlines.json"

SEED = 42
TRAIN_FRAC = 0.80

STRAT_LABELS = [
    "price_or_not_norm",
    "Direction Up",
    "Direction Constant",
    "Direction Down",
    "PastPrice",
    "FuturePrice",
    "PastNews",
    "FutureNews",
    "Asset Comparision",
]


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    if not CLEAN_JSONL.exists():
        raise SystemExit(f"Missing cleaned JSONL: {CLEAN_JSONL}")

    random.seed(SEED)

    records = list(load_jsonl(CLEAN_JSONL))

    # Connected components over normalized URL <-> normalized headline to prevent leakage.
    url_to_news = defaultdict(set)
    news_to_url = defaultdict(set)

    for rec in records:
        url = rec["data"]["url_norm"]
        news = rec["data"]["headline_norm"]
        url_to_news[url].add(news)
        news_to_url[news].add(url)

    components = []
    seen_urls = set()

    for url in url_to_news:
        if url in seen_urls:
            continue

        q = deque([("url", url)])
        comp_urls = set()
        comp_news = set()

        while q:
            kind, node = q.popleft()
            if kind == "url":
                if node in comp_urls:
                    continue
                comp_urls.add(node)
                seen_urls.add(node)
                for news in url_to_news[node]:
                    if news not in comp_news:
                        q.append(("news", news))
            else:
                if node in comp_news:
                    continue
                comp_news.add(node)
                for u in news_to_url[node]:
                    if u not in comp_urls:
                        q.append(("url", u))

        components.append({"urls": comp_urls, "news": comp_news})

    url_to_component = {}
    for idx, comp in enumerate(components):
        for url in comp["urls"]:
            url_to_component[url] = idx

    component_stats = []
    total_rows = len(records)
    total_label_sums = Counter()

    for idx, comp in enumerate(components):
        rows = 0
        label_sums = Counter()
        for rec in records:
            if url_to_component[rec["data"]["url_norm"]] != idx:
                continue
            rows += 1
            label_sums["price_or_not_norm"] += int(rec["label"]["price_or_not_norm"])
            for k, v in rec["label"]["labels_raw"].items():
                label_sums[k] += int(v)
        total_label_sums.update(label_sums)
        component_stats.append({
            "component_id": idx,
            "rows": rows,
            "urls": sorted(comp["urls"]),
            "news": sorted(comp["news"]),
            "label_sums": dict(label_sums),
        })

    target_train_rows = total_rows * TRAIN_FRAC

    def score_if_assign(train_rows, train_label_sums, comp, to_train: bool):
        if to_train:
            rows = train_rows + comp["rows"]
            lbl = Counter(train_label_sums)
            lbl.update(comp["label_sums"])
        else:
            rows = train_rows
            lbl = Counter(train_label_sums)

        row_term = abs(rows - target_train_rows) / max(target_train_rows, 1.0)

        label_terms = []
        for lab in STRAT_LABELS:
            total_lab = total_label_sums.get(lab, 0)
            if total_lab <= 0:
                continue
            share = lbl.get(lab, 0) / total_lab
            label_terms.append(abs(share - TRAIN_FRAC))
        label_term = (sum(label_terms) / len(label_terms)) if label_terms else 0.0

        return row_term + 0.5 * label_term

    comps_sorted = sorted(component_stats, key=lambda x: x["rows"], reverse=True)

    train_component_ids = set()
    train_rows = 0
    train_label_sums = Counter()

    for comp in comps_sorted:
        score_train = score_if_assign(train_rows, train_label_sums, comp, True)
        score_test = score_if_assign(train_rows, train_label_sums, comp, False)
        if score_train <= score_test:
            train_component_ids.add(comp["component_id"])
            train_rows += comp["rows"]
            train_label_sums.update(comp["label_sums"])

    train_records = []
    test_records = []
    train_urls = set()
    test_urls = set()
    train_news = set()
    test_news = set()
    train_label_sums_final = Counter()
    test_label_sums_final = Counter()

    for rec in records:
        comp_id = url_to_component[rec["data"]["url_norm"]]
        out = dict(rec)
        out["meta"] = dict(rec["meta"])
        split = "train" if comp_id in train_component_ids else "test"
        out["meta"]["canonical_split"] = split

        if split == "train":
            train_records.append(out)
            train_urls.add(out["data"]["url_norm"])
            train_news.add(out["data"]["headline_norm"])
            train_label_sums_final["price_or_not_norm"] += int(out["label"]["price_or_not_norm"])
            for k, v in out["label"]["labels_raw"].items():
                train_label_sums_final[k] += int(v)
        else:
            test_records.append(out)
            test_urls.add(out["data"]["url_norm"])
            test_news.add(out["data"]["headline_norm"])
            test_label_sums_final["price_or_not_norm"] += int(out["label"]["price_or_not_norm"])
            for k, v in out["label"]["labels_raw"].items():
                test_label_sums_final[k] += int(v)

    url_overlap = sorted(train_urls & test_urls)
    news_overlap = sorted(train_news & test_news)

    with TRAIN_JSONL.open("w", encoding="utf-8") as f:
        for rec in train_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with TEST_JSONL.open("w", encoding="utf-8") as f:
        for rec in test_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    TRAIN_URLS_JSON.write_text(json.dumps(sorted(train_urls), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TEST_URLS_JSON.write_text(json.dumps(sorted(test_urls), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TRAIN_HEADLINES_JSON.write_text(json.dumps(sorted(train_news), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TEST_HEADLINES_JSON.write_text(json.dumps(sorted(test_news), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    clean_meta = json.loads(CLEAN_META.read_text(encoding="utf-8"))

    manifest = {
        "dataset_id": "gold_commodity_news_kaggle_default_v0",
        "seed": SEED,
        "grouping_strategy": {
            "primary_group_key": "normalized_URL",
            "secondary_group_key": "normalized_News",
            "actual_assignment_unit": "connected_components_of_url_news_graph",
        },
        "target_train_fraction": TRAIN_FRAC,
        "totals": {
            "rows": len(records),
            "components": len(component_stats),
        },
        "split_counts": {
            "train": {
                "rows": len(train_records),
                "unique_urls": len(train_urls),
                "unique_headlines": len(train_news),
            },
            "test": {
                "rows": len(test_records),
                "unique_urls": len(test_urls),
                "unique_headlines": len(test_news),
            },
        },
        "overlap_checks": {
            "url_overlap_count": len(url_overlap),
            "headline_overlap_count": len(news_overlap),
            "url_overlap_preview": url_overlap[:20],
            "headline_overlap_preview": news_overlap[:20],
        },
        "label_balance": {
            "train": {k: int(train_label_sums_final.get(k, 0)) for k in STRAT_LABELS},
            "test": {k: int(test_label_sums_final.get(k, 0)) for k in STRAT_LABELS},
            "total": {k: int(total_label_sums.get(k, 0)) for k in STRAT_LABELS},
        },
        "membership_files": {
            "train_urls": str(TRAIN_URLS_JSON),
            "test_urls": str(TEST_URLS_JSON),
            "train_headlines": str(TRAIN_HEADLINES_JSON),
            "test_headlines": str(TEST_HEADLINES_JSON),
        },
        "cleaning_reference": clean_meta,
        "notes": [
            "Split built on the cleaned canonical dataset after exact duplicate removal.",
            "Original raw label columns are preserved; price_or_not_norm is a derived field.",
            "Canonical split is grouped to prevent leakage via repeated URLs and repeated headlines.",
        ],
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote train JSONL: {TRAIN_JSONL}")
    print(f"[DONE] Wrote test JSONL: {TEST_JSONL}")
    print(f"[DONE] Wrote split manifest: {MANIFEST_JSON}")
    print(f"[INFO] train_rows: {len(train_records)}")
    print(f"[INFO] test_rows: {len(test_records)}")
    print(f"[INFO] url_overlap_count: {len(url_overlap)}")
    print(f"[INFO] headline_overlap_count: {len(news_overlap)}")


if __name__ == "__main__":
    main()
