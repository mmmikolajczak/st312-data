import json
import hashlib
import argparse
from pathlib import Path
from collections import Counter


RAW_SPLITS = ["train", "valid", "test"]
ALLOWED_LABELS = {"negative", "neutral", "positive"}


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def stable_id(split: str, upstream_id: str, sentence: str, target: str, aspect: str) -> str:
    h = hashlib.sha256()
    h.update(b"fiqasa\n")
    h.update((split or "").encode("utf-8"))
    h.update(b"\n")
    h.update((str(upstream_id) if upstream_id is not None else "").encode("utf-8"))
    h.update(b"\n")
    h.update((sentence or "").encode("utf-8"))
    h.update(b"\n")
    h.update((target or "").encode("utf-8"))
    h.update(b"\n")
    h.update((aspect or "").encode("utf-8"))
    return h.hexdigest()[:16]


def discretize_score(score: float, neg_thr: float, pos_thr: float) -> str:
    # v0 convention:
    # score <= neg_thr -> negative
    # score >= pos_thr -> positive
    # else neutral
    if score <= neg_thr:
        return "negative"
    if score >= pos_thr:
        return "positive"
    return "neutral"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/fiqasa/raw")
    ap.add_argument("--out-dir", default="data/fiqasa/processed")
    ap.add_argument("--neg-thr", type=float, default=-0.1)
    ap.add_argument("--pos-thr", type=float, default=0.1)
    args = ap.parse_args()

    if not (args.neg_thr < args.pos_thr):
        raise ValueError("--neg-thr must be strictly less than --pos-thr")

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    overall_counts = Counter()
    split_summaries = {}

    for split in RAW_SPLITS:
        in_path = raw_dir / f"fiqasa_{split}_raw.jsonl"
        out_path = out_dir / f"fiqasa_{split}_clean.jsonl"

        if not in_path.exists():
            raise FileNotFoundError(f"Missing raw split file: {in_path}")

        cleaned_rows = []
        label_counts = Counter()
        n_in = 0

        for rec in load_jsonl(in_path):
            n_in += 1

            sentence = (rec.get("sentence") or "").strip()
            target = rec.get("target")
            aspect = rec.get("aspect")
            score = rec.get("score")
            ex_type = rec.get("type")
            upstream_id = rec.get("_id")

            if sentence == "":
                raise ValueError(f"Empty sentence in {split}: {rec}")

            if score is None:
                raise ValueError(f"Missing score in {split}: {rec}")

            try:
                score = float(score)
            except Exception:
                raise ValueError(f"Non-numeric score in {split}: {rec}")

            if score < -1.0 or score > 1.0:
                raise ValueError(f"Score out of expected [-1,1] range in {split}: {score}")

            label = discretize_score(score, args.neg_thr, args.pos_thr)
            if label not in ALLOWED_LABELS:
                raise ValueError(f"Unexpected discretized label: {label}")

            ex_id = stable_id(split, upstream_id, sentence, str(target), str(aspect))

            cleaned = {
                "example_id": ex_id,
                "dataset_id": "fiqasa",
                "config": "hf_default_v0_discrete",
                "data": {
                    "text": sentence,
                    "target": target,
                    "aspect": aspect,
                    "type": ex_type
                },
                "label": {
                    "sentiment": label,
                    "sentiment_score": score
                },
                "meta": {
                    "source": rec.get("source", "unknown"),
                    "upstream_id": upstream_id,
                    "split": split,
                    "label_scheme": {
                        "type": "3way_from_continuous",
                        "neg_thr": args.neg_thr,
                        "pos_thr": args.pos_thr
                    }
                }
            }

            cleaned_rows.append(cleaned)
            label_counts[label] += 1
            overall_counts[label] += 1

        n_out = write_jsonl(out_path, cleaned_rows)
        split_summaries[split] = {
            "n_in": n_in,
            "n_out": n_out,
            "label_counts": dict(label_counts)
        }
        print(f"[DONE] {split}: read {n_in}, wrote {n_out} -> {out_path}")
        print(f"[INFO] {split} label counts: {dict(label_counts)}")

    meta = {
        "dataset_id": "fiqasa",
        "config": "hf_default_v0_discrete",
        "source_dataset": "TheFinAI/fiqa-sentiment-classification",
        "splits": split_summaries,
        "total": sum(v["n_out"] for v in split_summaries.values()),
        "overall_label_counts": dict(overall_counts),
        "label_scheme": {
            "type": "3way_from_continuous",
            "neg_thr": args.neg_thr,
            "pos_thr": args.pos_thr,
            "rule": "score <= neg_thr => negative; score >= pos_thr => positive; else neutral"
        }
    }

    meta_path = out_dir / "fiqasa_clean_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[META] {meta_path}")
    print("[OK] FiQA cleaning + discretisation complete.")


if __name__ == "__main__":
    main()
