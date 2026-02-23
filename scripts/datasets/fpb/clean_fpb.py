import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_LABELS = {"positive", "neutral", "negative"}

def stable_id(config: str, sentence: str) -> str:
    # Deterministic ID: same input -> same ID across machines
    h = hashlib.sha256()
    h.update(config.encode("utf-8"))
    h.update(b"\n")
    h.update(sentence.encode("utf-8"))
    return h.hexdigest()[:16]  # short but collision-resistant for this size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="data/fpb/raw/fpb_allagree_raw.jsonl")
    ap.add_argument("--out", dest="out_path", default="data/fpb/processed/fpb_allagree_clean.jsonl")
    ap.add_argument("--dedup", action="store_true", help="Drop exact duplicate sentences (same config+sentence).")
    args = ap.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen = set()
    n_in = 0
    n_out = 0
    n_skipped_dup = 0

    with in_path.open("r", encoding="utf-8") as f_in, out_path.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            n_in += 1
            rec = json.loads(line)

            sentence = rec["sentence"].strip()
            label = rec["label"].strip().lower()
            config = rec.get("config", "unknown")

            if label not in ALLOWED_LABELS:
                raise ValueError(f"Unexpected label '{label}' in record: {rec}")

            ex_id = stable_id(config, sentence)

            if args.dedup:
                if ex_id in seen:
                    n_skipped_dup += 1
                    continue
                seen.add(ex_id)

            cleaned = {
                "example_id": ex_id,
                "dataset_id": "fpb",
                "config": config,
                "data": {"text": sentence},
                "label": {"sentiment": label},
                "meta": {"source": rec.get("source", "unknown")},
            }
            f_out.write(json.dumps(cleaned, ensure_ascii=False) + "\n")
            n_out += 1

    print(f"[DONE] Read {n_in} raw records")
    if args.dedup:
        print(f"[INFO] Skipped {n_skipped_dup} duplicates")
    print(f"[DONE] Wrote {n_out} cleaned records -> {out_path}")

if __name__ == "__main__":
    main()
