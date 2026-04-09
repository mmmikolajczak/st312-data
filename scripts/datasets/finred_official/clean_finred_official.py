import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RAW_DIR = Path("data/finred_official/raw")
PROCESSED_DIR = Path("data/finred_official/processed")

ALL_CLEAN_PATH = PROCESSED_DIR / "finred_official_all_clean.jsonl"
CLEAN_META_PATH = PROCESSED_DIR / "finred_official_clean_meta.json"

SPLITS = ["train", "dev", "test"]
RELATION_ALIASES = {
    "director/manager": "director_/_manager",
}


def read_lines(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def canonicalize_relation_display(s: str) -> str:
    s = s.strip().lower()
    if s in RELATION_ALIASES:
        return RELATION_ALIASES[s]
    s = s.replace("/", " or ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return "_".join(s.split())


def normalize_text(s: str) -> str:
    s = s.strip()
    s = s.replace("’", "'").replace("`", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    return s


def parse_tup_line(line: str):
    line = line.strip()
    if not line:
        return []
    out = []
    for chunk in line.split(" | "):
        parts = [x.strip() for x in chunk.split(" ; ")]
        if len(parts) != 3:
            raise ValueError(f"Malformed .tup chunk: {chunk!r}")
        head_text, tail_text, relation = parts
        out.append({
            "head_text": head_text,
            "tail_text": tail_text,
            "relation": relation,
        })
    return out


def parse_pointer_line(line: str):
    line = line.strip()
    if not line:
        return []
    out = []
    for chunk in line.split(" | "):
        parts = chunk.split()
        if len(parts) < 5:
            raise ValueError(f"Malformed .pointer chunk: {chunk!r}")
        hs, he, ts, te = map(int, parts[:4])
        relation = " ".join(parts[4:])
        out.append({
            "head_start": hs,
            "head_end": he,
            "tail_start": ts,
            "tail_end": te,
            "relation": relation,
        })
    return out


def relation_display_map():
    rel_path = RAW_DIR / "relations.txt"
    display_lines = [x.strip() for x in read_lines(rel_path) if x.strip()]
    display_to_canonical = {x: canonicalize_relation_display(x) for x in display_lines}
    return {
        "display_lines": display_lines,
        "display_to_canonical": display_to_canonical,
        "canonical_relations_from_relations_txt": sorted(display_to_canonical.values()),
    }


def join_tokens(tokens, start, end):
    if start < 0 or end < start or end >= len(tokens):
        raise ValueError(f"Invalid span ({start}, {end}) for token length {len(tokens)}")
    return " ".join(tokens[start:end+1])


def split_quality(split_name: str):
    if split_name == "test":
        return {
            "source_supervision": "manual_eval_split",
            "weak_supervision": False,
            "paper_note": "Paper states test data were manually annotated/cleaned for evaluation.",
        }
    return {
        "source_supervision": "distant_supervision",
        "weak_supervision": True,
        "paper_note": "Paper states train/dev data are derived using distant supervision.",
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rel_info = relation_display_map()
    canonical_from_relations_txt = set(rel_info["canonical_relations_from_relations_txt"])

    records = []
    split_counts = Counter()
    split_relation_counts = defaultdict(Counter)
    pointer_relation_counts = Counter()
    tup_relation_counts = Counter()
    relation_text_mismatch_count = 0
    relation_label_mismatch_count = 0
    examples_with_text_mismatch = []

    for split in SPLITS:
        sent_lines = read_lines(RAW_DIR / f"{split}.sent")
        tup_lines = read_lines(RAW_DIR / f"{split}.tup")
        pointer_lines = read_lines(RAW_DIR / f"{split}.pointer")
        txt_lines = read_lines(RAW_DIR / f"{split}.txt")

        n = len(sent_lines)
        if not (len(tup_lines) == len(pointer_lines) == len(txt_lines) == n):
            raise ValueError(
                f"Line-count mismatch for {split}: "
                f"sent={len(sent_lines)} tup={len(tup_lines)} pointer={len(pointer_lines)} txt={len(txt_lines)}"
            )

        for idx, (sent, tup_line, pointer_line, txt_line) in enumerate(
            zip(sent_lines, tup_lines, pointer_lines, txt_lines),
            start=1,
        ):
            tokens = sent.split()
            tup_triplets = parse_tup_line(tup_line)
            pointer_triplets = parse_pointer_line(pointer_line)

            if len(tup_triplets) != len(pointer_triplets):
                raise ValueError(
                    f"Triplet count mismatch in {split} line {idx}: "
                    f"tup={len(tup_triplets)} pointer={len(pointer_triplets)}"
                )

            triplets = []
            for t, p in zip(tup_triplets, pointer_triplets):
                if t["relation"] != p["relation"]:
                    relation_label_mismatch_count += 1

                head_text_from_pointer = join_tokens(tokens, p["head_start"], p["head_end"])
                tail_text_from_pointer = join_tokens(tokens, p["tail_start"], p["tail_end"])

                head_match = normalize_text(head_text_from_pointer) == normalize_text(t["head_text"])
                tail_match = normalize_text(tail_text_from_pointer) == normalize_text(t["tail_text"])

                if not (head_match and tail_match):
                    relation_text_mismatch_count += 1
                    if len(examples_with_text_mismatch) < 20:
                        examples_with_text_mismatch.append({
                            "split": split,
                            "line_index": idx,
                            "sentence": sent,
                            "pointer_head_text": head_text_from_pointer,
                            "tup_head_text": t["head_text"],
                            "pointer_tail_text": tail_text_from_pointer,
                            "tup_tail_text": t["tail_text"],
                            "relation": p["relation"],
                        })

                pointer_relation_counts[p["relation"]] += 1
                tup_relation_counts[t["relation"]] += 1
                split_relation_counts[split][p["relation"]] += 1

                triplets.append({
                    "head": {
                        "start": p["head_start"],
                        "end": p["head_end"],
                        "text": head_text_from_pointer,
                        "tup_text": t["head_text"],
                        "text_matches_tup": head_match,
                    },
                    "relation": p["relation"],
                    "tail": {
                        "start": p["tail_start"],
                        "end": p["tail_end"],
                        "text": tail_text_from_pointer,
                        "tup_text": t["tail_text"],
                        "text_matches_tup": tail_match,
                    },
                })

            example_id = f"finred_{split}_{idx:06d}"
            rec = {
                "example_id": example_id,
                "data": {
                    "text": sent,
                    "tokens": tokens,
                    "release_txt": txt_line,
                },
                "label": {
                    "triplets": triplets,
                    "n_triplets": len(triplets),
                },
                "meta": {
                    "split": split,
                    **split_quality(split),
                    "source_files": {
                        "sent": f"{split}.sent",
                        "tup": f"{split}.tup",
                        "pointer": f"{split}.pointer",
                        "txt": f"{split}.txt",
                    },
                },
            }
            records.append(rec)
            split_counts[split] += 1

    pointer_relations = set(pointer_relation_counts)
    tup_relations = set(tup_relation_counts)

    clean_meta = {
        "dataset_id": "finred_official_v0",
        "n_examples_total": len(records),
        "split_counts": dict(split_counts),
        "released_total_check": sum(split_counts.values()),
        "paper_vs_release_notes": [
            "Paper states total size 7,775.",
            "Paper reports 5,699 train and 1,068 test examples.",
            "Released files parsed here give counts determined from raw line counts.",
            "Trust released files for ingestion while recording this discrepancy in provenance."
        ],
        "relation_inventory": {
            "n_unique_pointer_relations": len(pointer_relations),
            "n_unique_tup_relations": len(tup_relations),
            "pointer_relations": sorted(pointer_relations),
            "tup_relations": sorted(tup_relations),
            "relations_txt_display_lines": rel_info["display_lines"],
            "relations_txt_canonicalized": rel_info["canonical_relations_from_relations_txt"],
            "relations_txt_display_to_canonical": rel_info["display_to_canonical"],
            "pointer_equals_tup_relation_set": sorted(pointer_relations) == sorted(tup_relations),
            "pointer_equals_relations_txt_canonicalized": sorted(pointer_relations) == sorted(canonical_from_relations_txt),
        },
        "relation_counts_by_split": {
            split: dict(split_relation_counts[split]) for split in SPLITS
        },
        "alignment_checks": {
            "relation_label_mismatch_count": relation_label_mismatch_count,
            "entity_text_mismatch_count": relation_text_mismatch_count,
            "sample_entity_text_mismatches": examples_with_text_mismatch,
        },
    }

    with ALL_CLEAN_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    CLEAN_META_PATH.write_text(json.dumps(clean_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote all-clean JSONL: {ALL_CLEAN_PATH}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META_PATH}")
    print(f"[INFO] Split counts: {dict(split_counts)}")
    print(f"[INFO] Unique relations (pointer): {len(pointer_relations)}")
    print(f"[INFO] Relation label mismatches: {relation_label_mismatch_count}")
    print(f"[INFO] Entity text mismatches: {relation_text_mismatch_count}")
    print(f"[INFO] pointer_equals_relations_txt_canonicalized: {sorted(pointer_relations) == sorted(canonical_from_relations_txt)}")


if __name__ == "__main__":
    main()
