import json
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

RAW_DIR = Path("data/salinas_sec_loan_ner/raw")
PROCESSED_DIR = Path("data/salinas_sec_loan_ner/processed")
ALL_CLEAN_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_all_clean.jsonl"
CLEAN_META_PATH = PROCESSED_DIR / "salinas_sec_loan_ner_clean_meta.json"

SOURCE_TO_SPLIT = {
    "FIN5.txt": "train",
    "FIN3.txt": "test",
}


def read_conll_sentences(path: Path) -> Iterable[List[Tuple[str, str, str, str]]]:
    sentence: List[Tuple[str, str, str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                if sentence:
                    yield sentence
                    sentence = []
                continue
            if line.startswith("-DOCSTART-") or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                raise ValueError(f"Expected >=4 columns in {path}, got: {line!r}")
            token, pos_tag, chunk_tag, ner_tag = parts[0], parts[1], parts[2], parts[3]
            sentence.append((token, pos_tag, chunk_tag, ner_tag))
    if sentence:
        yield sentence


def to_bio2(tags: List[str]) -> List[str]:
    out: List[str] = []
    prev_type = None
    prev_is_entity = False
    for tag in tags:
        if tag == "O":
            out.append("O")
            prev_type = None
            prev_is_entity = False
            continue
        if "-" not in tag:
            raise ValueError(f"Malformed tag without hyphen: {tag!r}")
        prefix, ent_type = tag.split("-", 1)
        if prefix not in {"B", "I"}:
            raise ValueError(f"Unsupported BIO prefix in tag: {tag!r}")
        if prefix == "B":
            out.append(tag)
            prev_type = ent_type
            prev_is_entity = True
            continue
        if (not prev_is_entity) or (prev_type != ent_type):
            out.append(f"B-{ent_type}")
        else:
            out.append(tag)
        prev_type = ent_type
        prev_is_entity = True
    return out


def label_signature(tags: List[str]) -> str:
    ents = sorted({tag.split("-", 1)[1] for tag in tags if tag != "O"})
    return "|".join(ents) if ents else "NONE"


def simple_text(tokens: List[str]) -> str:
    return " ".join(tokens)


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    token_tag_counts_original = Counter()
    token_tag_counts_bio2 = Counter()
    entity_type_counts = Counter()
    split_sentence_counts = Counter()
    split_token_counts = Counter()
    source_sentence_counts = Counter()

    split_indices = {"train": 0, "test": 0}

    for source_name in ["FIN5.txt", "FIN3.txt"]:
        source_path = RAW_DIR / source_name
        if not source_path.exists():
            raise SystemExit(f"Missing raw file: {source_path}. Run ingest first.")
        split = SOURCE_TO_SPLIT[source_name]
        for sentence in read_conll_sentences(source_path):
            split_indices[split] += 1
            tokens = [row[0] for row in sentence]
            pos_tags = [row[1] for row in sentence]
            chunk_tags = [row[2] for row in sentence]
            original_tags = [row[3] for row in sentence]
            bio2_tags = to_bio2(original_tags)

            for tag in original_tags:
                token_tag_counts_original[tag] += 1
            for tag in bio2_tags:
                token_tag_counts_bio2[tag] += 1
                if tag != "O":
                    entity_type_counts[tag.split("-", 1)[1]] += 1

            source_sentence_counts[source_name] += 1
            split_sentence_counts[split] += 1
            split_token_counts[split] += len(tokens)

            example_id = f"salinas_sec_loan_ner_{split}_{split_indices[split]:06d}"
            records.append({
                "example_id": example_id,
                "data": {
                    "tokens": tokens,
                    "pos_tags": pos_tags,
                    "chunk_tags": chunk_tags,
                    "text": simple_text(tokens),
                },
                "label": {
                    "tags": bio2_tags,
                    "original_tags": original_tags,
                },
                "meta": {
                    "source_file": source_name,
                    "canonical_split": split,
                    "sentence_index_in_source": split_indices[split],
                    "n_tokens": len(tokens),
                    "label_signature": label_signature(bio2_tags),
                    "contains_misc": any(tag.endswith("MISC") for tag in bio2_tags),
                    "contains_lender_token": any(tok.lower() == "lender" for tok in tokens),
                    "contains_borrower_token": any(tok.lower() == "borrower" for tok in tokens),
                    "notes": [
                        "Original CoNLL columns preserved in data.pos_tags, data.chunk_tags, and label.original_tags.",
                        "label.tags stores derived BIO2 labels for training/evaluation.",
                    ],
                },
            })

    with ALL_CLEAN_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    clean_meta = {
        "dataset_id": "salinas_sec_loan_ner_v0",
        "n_examples": len(records),
        "n_tokens_total": sum(split_token_counts.values()),
        "source_sentence_counts": dict(source_sentence_counts),
        "split_sentence_counts": dict(split_sentence_counts),
        "split_token_counts": dict(split_token_counts),
        "token_tag_counts_original": dict(token_tag_counts_original),
        "token_tag_counts_bio2": dict(token_tag_counts_bio2),
        "entity_type_counts_bio2": dict(entity_type_counts),
        "label_policy_notes": [
            "MISC retained exactly as a supported entity type.",
            "Original CoNLL-style NER tags preserved in label.original_tags.",
            "BIO2 normalization stored separately in label.tags.",
            "Corpus-specific lender/borrower→PER policy documented from the paper; no local relabelling beyond BIO2 normalization is applied.",
        ],
    }
    CLEAN_META_PATH.write_text(json.dumps(clean_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[DONE] Wrote all-clean JSONL: {ALL_CLEAN_PATH}")
    print(f"[DONE] Wrote clean metadata: {CLEAN_META_PATH}")
    print(f"[INFO] Examples: {len(records)}")
    print(f"[INFO] Split counts: {dict(split_sentence_counts)}")


if __name__ == "__main__":
    main()
