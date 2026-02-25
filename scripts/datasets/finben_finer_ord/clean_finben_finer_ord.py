import json
import hashlib
import re
from pathlib import Path
from collections import Counter

IN_PATH = Path("data/finer_ord/raw/finben_finer_ord_test_raw.jsonl")
OUT_PATH = Path("data/finer_ord/processed/finben_finer_ord_all_clean.jsonl")
META_PATH = Path("data/finer_ord/processed/finben_finer_ord_clean_meta.json")

ALLOWED = {"O", "B-PER", "I-PER", "B-LOC", "I-LOC", "B-ORG", "I-ORG"}

def stable_example_id(upstream_id: str, tokens, labels) -> str:
    h = hashlib.sha256()
    h.update((upstream_id or "").encode("utf-8"))
    h.update(b"\n")
    h.update(" ".join(tokens).encode("utf-8"))
    h.update(b"\n")
    h.update(" ".join(labels).encode("utf-8"))
    return h.hexdigest()[:16]

def extract_text_from_query(q: str):
    if not isinstance(q, str):
        return None
    m = re.search(r"Text:\s*(.*?)\s*Answer:\s*$", q, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return None

def normalize_label(x: str) -> str:
    if not isinstance(x, str):
        raise ValueError(f"Non-string label: {x!r}")
    y = x.strip().upper()
    if y not in ALLOWED:
        raise ValueError(f"Unexpected label: {x!r} -> {y!r}")
    return y

def entity_signature(labels):
    ents = sorted({lab.split("-")[-1] for lab in labels if lab != "O"})
    return "+".join(ents) if ents else "NONE"

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(IN_PATH)

    rows_out = []
    token_label_counts = Counter()
    sentence_sig_counts = Counter()
    n_in = 0

    with IN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            rec = json.loads(line)

            tokens = rec.get("token")
            labels = rec.get("label")

            if not isinstance(tokens, list) or not isinstance(labels, list):
                raise ValueError(f"Row {n_in}: token/label must be lists")
            if len(tokens) != len(labels):
                raise ValueError(f"Row {n_in}: token/label length mismatch ({len(tokens)} vs {len(labels)})")
            if len(tokens) == 0:
                raise ValueError(f"Row {n_in}: empty token list")

            tokens = [str(t) for t in tokens]
            labels = [normalize_label(x) for x in labels]

            text_from_query = extract_text_from_query(rec.get("query"))
            ex_id = stable_example_id(str(rec.get("_id")), tokens, labels)
            sig = entity_signature(labels)

            out = {
                "example_id": ex_id,
                "dataset_id": "finben_finer_ord_v0",
                "config": "token_labels_v0",
                "data": {
                    "tokens": tokens,
                    "text": text_from_query
                },
                "label": {
                    "tags": labels
                },
                "meta": {
                    "source": rec.get("source"),
                    "upstream_id": rec.get("_id"),
                    "upstream_split": rec.get("split"),
                    "upstream_query": rec.get("query"),
                    "upstream_answer": rec.get("answer"),
                    "label_signature": sig,
                    "n_tokens": len(tokens)
                }
            }

            rows_out.append(out)
            token_label_counts.update(labels)
            sentence_sig_counts[sig] += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": "finben_finer_ord_v0",
        "config": "token_labels_v0",
        "source_dataset": "TheFinAI/finben-finer-ord",
        "n_in": n_in,
        "n_out": len(rows_out),
        "allowed_labels": sorted(ALLOWED),
        "token_label_counts": dict(token_label_counts),
        "sentence_signature_counts": dict(sentence_sig_counts)
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] wrote {len(rows_out)} rows -> {OUT_PATH}")
    print(f"[INFO] token label counts: {dict(token_label_counts)}")
    print(f"[INFO] sentence signatures: {dict(sentence_sig_counts)}")
    print(f"[META] {META_PATH}")
    print("[OK] Cleaning complete.")

if __name__ == "__main__":
    main()
