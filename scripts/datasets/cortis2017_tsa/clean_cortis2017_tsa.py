import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Optional


RAW_DIR = Path("data/cortis2017_tsa/raw")
PROC_DIR = Path("data/cortis2017_tsa/processed")

ARTIFACT_REPLACEMENTS = {
    "\u00a0": " ",
    "Â£": "£",
    "â€™": "’",
    "â€œ": "“",
    "â€": "”",
    "â€“": "–",
    "â€”": "—",
}


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def dump_jsonl(rows, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def clean_surface_text(text: str) -> str:
    text = html.unescape(str(text))
    for bad, good in ARTIFACT_REPLACEMENTS.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_for_key(text: str) -> str:
    return clean_surface_text(text).casefold()


def slugify(text: str, limit: int = 40) -> str:
    text = normalize_for_key(text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:limit] or "na"


def lookup(rec: dict, candidates) -> Optional[object]:
    lowered = {str(k).lower(): v for k, v in rec.items()}
    for cand in candidates:
        if cand in rec and rec[cand] not in (None, ""):
            return rec[cand]
        lc = cand.lower()
        if lc in lowered and lowered[lc] not in (None, ""):
            return lowered[lc]
    return None


def coerce_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict) and len(value) == 1:
        return coerce_float(next(iter(value.values())))
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
    return None


def extract_title(rec: dict) -> Optional[str]:
    value = lookup(rec, ["title", "headline", "text", "message", "sentence"])
    return None if value is None else str(value)


def extract_company(rec: dict) -> Optional[str]:
    value = lookup(rec, ["company", "target_company", "target", "entity", "stock", "cashtag"])
    return None if value is None else str(value)


def extract_label(rec: dict) -> Optional[float]:
    value = lookup(
        rec,
        [
            "sentiment_score",
            "sentiment score",
            "sentiment",
            "score",
            "label",
            "gold",
            "value",
        ],
    )
    score = coerce_float(value)
    if score is None:
        return None
    if score < -1.000001 or score > 1.000001:
        raise ValueError(f"Sentiment score out of expected range [-1,1]: {score}")
    return max(-1.0, min(1.0, score))


def extract_official_id(rec: dict) -> Optional[str]:
    value = lookup(rec, ["id", "ID", "guid", "uid", "record_id", "instance_id"])
    if value is None:
        return None
    return str(value).strip()


def make_join_key(official_id: Optional[str], title_raw: str, company_raw: str):
    return (
        official_id or "",
        normalize_for_key(title_raw),
        normalize_for_key(company_raw),
    )


def make_example_id(split: str, official_id: Optional[str], title_raw: str, company_raw: str) -> str:
    company_slug = slugify(company_raw)
    if official_id:
        return f"cortis2017_tsa::{split}::{official_id}::{company_slug}"
    material = f"{split}||{title_raw}||{company_raw}"
    h = hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]
    return f"cortis2017_tsa::{split}::hash::{h}::{company_slug}"


def canonicalize(raw_wrapper: dict) -> dict:
    rec = raw_wrapper["raw_record"]
    split = raw_wrapper["official_split"]
    raw_index = raw_wrapper["raw_index"]

    title_raw = extract_title(rec)
    company_raw = extract_company(rec)
    if title_raw is None or company_raw is None:
        raise ValueError(
            f"Could not extract title/company for split={split} raw_index={raw_index}: keys={sorted(rec.keys())}"
        )

    official_id = extract_official_id(rec)
    label = extract_label(rec)

    row = {
        "example_id": make_example_id(split, official_id, title_raw, company_raw),
        "split": split,
        "source_dataset": "cortis2017_tsa",
        "task_family": "sentiment_regression",
        "data": {
            "title_raw": title_raw,
            "title_normalized": clean_surface_text(title_raw),
            "target_company_raw": company_raw,
            "target_company_normalized": clean_surface_text(company_raw),
        },
        "provenance": {
            "official_split": split,
            "upstream_record_id": official_id,
            "raw_index": raw_index,
        },
    }

    if label is not None:
        row["label"] = {"sentiment_score": label}

    return row


def read_and_clean(path: Path):
    rows = []
    for wrapped in load_jsonl(path):
        rows.append(canonicalize(wrapped))
    return rows


def join_test_gold(test_inputs, test_gold_rows):
    gold_by_key = {}
    for row in test_gold_rows:
        key = make_join_key(
            row["provenance"].get("upstream_record_id"),
            row["data"]["title_raw"],
            row["data"]["target_company_raw"],
        )
        if "label" not in row:
            continue
        if key in gold_by_key:
            raise ValueError(f"Duplicate gold join key detected: {key}")
        gold_by_key[key] = row["label"]["sentiment_score"]

    scored = []
    missing = 0
    for row in test_inputs:
        key = make_join_key(
            row["provenance"].get("upstream_record_id"),
            row["data"]["title_raw"],
            row["data"]["target_company_raw"],
        )
        if key not in gold_by_key:
            missing += 1
            continue
        out = dict(row)
        out["label"] = {"sentiment_score": gold_by_key[key]}
        scored.append(out)

    return scored, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default=str(RAW_DIR))
    ap.add_argument("--processed-dir", default=str(PROC_DIR))
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    proc_dir = Path(args.processed_dir)
    proc_dir.mkdir(parents=True, exist_ok=True)

    raw_paths = {
        "train": raw_dir / "cortis2017_tsa_train_raw.jsonl",
        "trial": raw_dir / "cortis2017_tsa_trial_raw.jsonl",
        "test_inputs": raw_dir / "cortis2017_tsa_test_inputs_raw.jsonl",
        "test_gold": raw_dir / "cortis2017_tsa_test_gold_raw.jsonl",
    }

    for split in ("train", "trial", "test_inputs"):
        if not raw_paths[split].exists():
            raise SystemExit(f"Missing ingested raw JSONL for split={split}: {raw_paths[split]}")

    train_rows = read_and_clean(raw_paths["train"])
    trial_rows = read_and_clean(raw_paths["trial"])
    test_input_rows = read_and_clean(raw_paths["test_inputs"])

    out_train = proc_dir / "cortis2017_tsa_train.jsonl"
    out_trial = proc_dir / "cortis2017_tsa_trial.jsonl"
    out_test_inputs = proc_dir / "cortis2017_tsa_test_inputs.jsonl"
    dump_jsonl(train_rows, out_train)
    dump_jsonl(trial_rows, out_trial)
    dump_jsonl(test_input_rows, out_test_inputs)

    test_gold_present = raw_paths["test_gold"].exists()
    test_scored_rows = []
    test_gold_missing_after_join = None

    if test_gold_present:
        gold_rows = read_and_clean(raw_paths["test_gold"])
        test_scored_rows, test_gold_missing_after_join = join_test_gold(test_input_rows, gold_rows)
        dump_jsonl(test_scored_rows, proc_dir / "cortis2017_tsa_test_scored.jsonl")

    all_labeled = train_rows + trial_rows + test_scored_rows
    dump_jsonl(all_labeled, proc_dir / "cortis2017_tsa_all_labeled.jsonl")

    meta = {
        "dataset_id": "cortis2017_tsa_v0",
        "counts": {
            "train": len(train_rows),
            "trial": len(trial_rows),
            "test_inputs": len(test_input_rows),
            "test_scored": len(test_scored_rows),
            "all_labeled": len(all_labeled),
        },
        "test_gold_present": test_gold_present,
        "test_gold_missing_after_join": test_gold_missing_after_join,
        "paths": {
            "train": str(out_train),
            "trial": str(out_trial),
            "test_inputs": str(out_test_inputs),
            "test_scored": str(proc_dir / "cortis2017_tsa_test_scored.jsonl"),
            "all_labeled": str(proc_dir / "cortis2017_tsa_all_labeled.jsonl"),
        },
    }
    meta_path = proc_dir / "cortis2017_tsa_clean_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[DONE] Clean step complete")
    print(f"[META] {meta_path}")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
