import json
import hashlib
from pathlib import Path
from collections import Counter

ALLOWED = {"dovish", "hawkish", "neutral"}

RAW_PATH = Path("data/fomc/raw/finben_fomc_test_raw.jsonl")
OUT_PATH = Path("data/fomc/processed/finben_fomc_all_clean.jsonl")
META_PATH = Path("data/fomc/processed/finben_fomc_clean_meta.json")

def stable_example_id(upstream_id: str, text: str, label: str) -> str:
    s = f"{upstream_id}|||{text}|||{label}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def infer_label(answer, gold, choices):
    label_from_answer = None
    if isinstance(answer, str):
        a = answer.strip().lower()
        if a in ALLOWED:
            label_from_answer = a

    label_from_gold = None
    if isinstance(gold, int) and isinstance(choices, list) and 0 <= gold < len(choices):
        c = str(choices[gold]).strip().lower()
        if c in ALLOWED:
            label_from_gold = c

    if label_from_answer and label_from_gold and label_from_answer != label_from_gold:
        raise ValueError(f"Label mismatch: answer={label_from_answer}, gold/choices={label_from_gold}")

    label = label_from_answer or label_from_gold
    if label not in ALLOWED:
        raise ValueError(f"Could not infer valid label from answer={answer}, gold={gold}, choices={choices}")

    return label

def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing raw file: {RAW_PATH}")

    rows_out = []
    counts = Counter()
    n_in = 0

    with RAW_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            n_in += 1
            rec = json.loads(line)

            text = (rec.get("text") or "").strip()
            if not text:
                raise ValueError(f"Empty text at row {n_in}")

            label = infer_label(rec.get("answer"), rec.get("gold"), rec.get("choices"))
            ex_id = stable_example_id(str(rec.get('_id')), text, label)

            out = {
                "example_id": ex_id,
                "dataset_id": "finben_fomc_v0",
                "config": "raw_labels_v0",
                "data": {
                    "text": text
                },
                "label": {
                    "stance": label
                },
                "meta": {
                    "source": rec.get("source"),
                    "upstream_id": rec.get("_id"),
                    "upstream_split": rec.get("split"),
                    "upstream_answer": rec.get("answer"),
                    "upstream_gold": rec.get("gold"),
                    "upstream_choices": rec.get("choices"),
                    "upstream_query": rec.get("query"),
                    "label_source": "answer/gold+choices"
                }
            }

            rows_out.append(out)
            counts[label] += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": "finben_fomc_v0",
        "config": "raw_labels_v0",
        "source_dataset": "TheFinAI/finben-fomc",
        "n_in": n_in,
        "n_out": len(rows_out),
        "label_counts": dict(counts),
        "label_scheme": {
            "type": "categorical_3way",
            "labels": ["dovish", "hawkish", "neutral"],
            "source_fields": ["answer", "gold", "choices"]
        }
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] wrote {len(rows_out)} rows -> {OUT_PATH}")
    print(f"[INFO] label counts: {dict(counts)}")
    print(f"[META] {META_PATH}")
    print("[OK] Cleaning complete.")

if __name__ == "__main__":
    main()
