from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_SHARED_DIR = SCRIPT_DIR.parent.parent / "tasks" / "_tatqa_shared"
if str(TASK_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_SHARED_DIR))

from serialize_tatqa_paragraphs import serialize_tatqa_paragraphs  # noqa: E402
from serialize_tatqa_table import serialize_tatqa_table  # noqa: E402


DATASET_ID = "tatqa_official_v0"
SOURCE_REPO = "NExTplusplus/TAT-QA"
SOURCE_REPO_URL = "https://github.com/NExTplusplus/TAT-QA.git"
PINNED_SOURCE_COMMIT = "644770eb2a66dddc24b92303bd2acbad84cd2b9f"
RAW_DIR = Path("data/tatqa_official/raw")
PROCESSED_DIR = Path("data/tatqa_official/processed")
REPORT_DIR = Path("reports/tatqa_official")
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "label_inventory.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
ORIGINAL_TEST_SUMMARY_PATH = PROCESSED_DIR / "original_test_summary.json"
INGEST_AUDIT_PATH = REPORT_DIR / "ingest_audit.json"

SOURCE_PATHS = [
    "dataset_raw/tatqa_dataset_train.json",
    "dataset_raw/tatqa_dataset_dev.json",
    "dataset_raw/tatqa_dataset_test.json",
    "dataset_raw/tatqa_dataset_test_gold.json",
    "README.md",
    "LICENSE",
    "tatqa_eval.py",
    "tatqa_metric.py",
    "tatqa_utils.py",
    "sample_prediction.json",
]

CANONICAL_SPLIT_SOURCE_PATHS = {
    "train": "dataset_raw/tatqa_dataset_train.json",
    "dev": "dataset_raw/tatqa_dataset_dev.json",
    "test": "dataset_raw/tatqa_dataset_test_gold.json",
}
ORIGINAL_TEST_SOURCE_PATH = "dataset_raw/tatqa_dataset_test.json"
EXPECTED_COUNTS = {
    "train": {"contexts": 2201, "questions": 13215},
    "dev": {"contexts": 278, "questions": 1668},
    "test": {"contexts": 277, "questions": 1663},
    "original_test": {"contexts": 278, "questions": 1669},
}
OFFICIAL_SCALE_INVENTORY = ["", "thousand", "million", "billion", "percent"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def github_display_url(source_path: str) -> str:
    return f"https://github.com/{SOURCE_REPO}/blob/{PINNED_SOURCE_COMMIT}/{source_path}"


def github_raw_url(source_path: str) -> str:
    return f"https://raw.githubusercontent.com/{SOURCE_REPO}/{PINNED_SOURCE_COMMIT}/{source_path}"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def clone_repo() -> tuple[Path, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="tatqa_clone_"))
    subprocess.run(["git", "clone", SOURCE_REPO_URL, str(temp_dir)], check=True)
    subprocess.run(["git", "-C", str(temp_dir), "checkout", PINNED_SOURCE_COMMIT], check=True)
    commit = (
        subprocess.run(
            ["git", "-C", str(temp_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
    )
    return temp_dir, commit


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_answer_type(answer_type: str) -> str:
    return "count" if answer_type == "counting" else answer_type


def parse_rel_paragraph_orders(values: list[object]) -> list[int]:
    parsed: list[int] = []
    for value in values:
        text = str(value).strip()
        if text.isdigit():
            parsed.append(int(text))
    return parsed


def validate_table_dict(table_obj: object) -> tuple[str, list[list[str]]]:
    if not isinstance(table_obj, dict):
        raise ValueError("table must be a dict")
    if "uid" not in table_obj or "table" not in table_obj:
        raise KeyError("table must contain uid and table")
    if not isinstance(table_obj["uid"], str) or not table_obj["uid"].strip():
        raise ValueError("table.uid must be a non-empty string")
    if not isinstance(table_obj["table"], list):
        raise ValueError("table.table must be a list")

    normalized_rows: list[list[str]] = []
    for row in table_obj["table"]:
        if not isinstance(row, list):
            raise ValueError("table rows must be lists")
        normalized_rows.append(["" if cell is None else str(cell) for cell in row])
    return table_obj["uid"], normalized_rows


def validate_paragraphs(paragraphs: object) -> list[dict]:
    if not isinstance(paragraphs, list):
        raise ValueError("paragraphs must be a list")

    seen_orders: set[int] = set()
    normalized: list[dict] = []
    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            raise ValueError("paragraph entries must be dicts")
        for key in ["uid", "order", "text"]:
            if key not in paragraph:
                raise KeyError(f"paragraph missing {key}")
        order = int(paragraph["order"])
        if order in seen_orders:
            raise ValueError(f"duplicate paragraph order {order}")
        seen_orders.add(order)
        text = str(paragraph["text"]).strip()
        if not text:
            raise ValueError(f"paragraph {order} text must be non-empty")
        normalized.append(
            {
                "uid": str(paragraph["uid"]),
                "order": order,
                "text": text,
            }
        )
    return normalized


def validate_question(question: object, *, require_labels: bool) -> dict:
    if not isinstance(question, dict):
        raise ValueError("question entries must be dicts")

    required_keys = ["uid", "order", "question"]
    if require_labels:
        required_keys.extend(["answer", "answer_type", "answer_from", "scale"])
    for key in required_keys:
        if key not in question:
            raise KeyError(f"question missing {key}")

    normalized = {
        "uid": str(question["uid"]),
        "order": int(question["order"]),
        "question": str(question["question"]).strip(),
    }
    if not normalized["uid"] or not normalized["question"]:
        raise ValueError("question uid and text must be non-empty")

    if require_labels:
        answer_type_raw = str(question["answer_type"]).strip()
        answer_from = str(question["answer_from"]).strip()
        scale = str(question["scale"]).strip().lower()
        if normalize_answer_type(answer_type_raw) not in {"span", "multi-span", "arithmetic", "count"}:
            raise ValueError(f"unexpected answer_type {answer_type_raw}")
        if answer_from not in {"table", "text", "table-text"}:
            raise ValueError(f"unexpected answer_from {answer_from}")
        if scale not in OFFICIAL_SCALE_INVENTORY:
            raise ValueError(f"unexpected scale {scale}")
        if not isinstance(question.get("rel_paragraphs", []), list):
            raise ValueError("rel_paragraphs must be a list")
        if not isinstance(question.get("req_comparison", False), bool):
            raise ValueError("req_comparison must be bool")

        normalized.update(
            {
                "answer": question.get("answer"),
                "derivation": str(question.get("derivation", "") or ""),
                "answer_type_raw": answer_type_raw,
                "answer_type_norm": normalize_answer_type(answer_type_raw),
                "answer_from": answer_from,
                "rel_paragraphs": [str(x) for x in question.get("rel_paragraphs", [])],
                "rel_paragraph_orders": parse_rel_paragraph_orders(question.get("rel_paragraphs", [])),
                "req_comparison": question.get("req_comparison", False),
                "scale": scale,
                "source_fields_present": sorted(question.keys()),
            }
        )
    return normalized


def build_processed_rows(split: str, source_path: str, source_commit: str, contexts: list[dict]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    split_context_ids: set[str] = set()
    split_question_ids: set[str] = set()
    answer_type_dist: Counter[str] = Counter()
    answer_from_dist: Counter[str] = Counter()
    scale_dist: Counter[str] = Counter()
    empty_answers: list[str] = []

    for context in contexts:
        if not isinstance(context, dict):
            raise ValueError("context entries must be dicts")
        for key in ["table", "paragraphs", "questions"]:
            if key not in context:
                raise KeyError(f"context missing {key}")

        context_id, table = validate_table_dict(context["table"])
        if context_id in split_context_ids:
            raise ValueError(f"duplicate context_id within {split}: {context_id}")
        split_context_ids.add(context_id)

        paragraphs = validate_paragraphs(context["paragraphs"])
        if not isinstance(context["questions"], list):
            raise ValueError("questions must be a list")

        question_orders: set[int] = set()
        for question in context["questions"]:
            q = validate_question(question, require_labels=True)
            if q["order"] in question_orders:
                raise ValueError(f"duplicate question order {q['order']} in context {context_id}")
            question_orders.add(q["order"])
            if q["uid"] in split_question_ids:
                raise ValueError(f"duplicate example_id within {split}: {q['uid']}")
            split_question_ids.add(q["uid"])

            if q["answer"] in ["", [], None]:
                empty_answers.append(q["uid"])

            answer_type_dist[q["answer_type_raw"]] += 1
            answer_from_dist[q["answer_from"]] += 1
            scale_dist[q["scale"]] += 1

            rows.append(
                {
                    "example_id": q["uid"],
                    "context_id": context_id,
                    "dataset_id": DATASET_ID,
                    "split": split,
                    "question_order": q["order"],
                    "question": q["question"],
                    "table": table,
                    "paragraphs": paragraphs,
                    "table_serialized": serialize_tatqa_table(table),
                    "paragraphs_serialized": serialize_tatqa_paragraphs(paragraphs),
                    "gold_answer": q["answer"],
                    "gold_scale": q["scale"],
                    "gold_derivation": q["derivation"],
                    "gold_answer_type_raw": q["answer_type_raw"],
                    "gold_answer_type_norm": q["answer_type_norm"],
                    "gold_answer_from": q["answer_from"],
                    "gold_rel_paragraphs_raw": q["rel_paragraphs"],
                    "gold_rel_paragraph_orders": q["rel_paragraph_orders"],
                    "gold_req_comparison": q["req_comparison"],
                    "source_repo": SOURCE_REPO,
                    "source_commit": source_commit,
                    "source_path": source_path,
                    "source_fields_present": {
                        "context": sorted(context.keys()),
                        "table": sorted(context["table"].keys()),
                        "question": q["source_fields_present"],
                    },
                }
            )

    counts = {"contexts": len(contexts), "questions": len(rows)}
    if counts != EXPECTED_COUNTS[split]:
        raise ValueError(f"{split} counts mismatch: expected {EXPECTED_COUNTS[split]}, got {counts}")

    return rows, {
        "counts": counts,
        "answer_type_distribution": dict(answer_type_dist),
        "answer_from_distribution": dict(answer_from_dist),
        "scale_distribution": dict(scale_dist),
        "empty_answer_example_ids": empty_answers,
    }


def build_original_test_summary(contexts: list[dict]) -> dict:
    counts = {"contexts": len(contexts), "questions": sum(len(item["questions"]) for item in contexts)}
    if counts != EXPECTED_COUNTS["original_test"]:
        raise ValueError(f"original unlabeled test counts mismatch: expected {EXPECTED_COUNTS['original_test']}, got {counts}")

    top_level_fields = sorted({key for item in contexts for key in item.keys()})
    question_fields = sorted({key for item in contexts for q in item["questions"] for key in q.keys()})
    return {
        "split": "original_test_unlabeled",
        "source_path": ORIGINAL_TEST_SOURCE_PATH,
        "contexts": counts["contexts"],
        "questions": counts["questions"],
        "top_level_fields": top_level_fields,
        "question_fields": question_fields,
        "no_references": True,
        "published_in_supervised_canonical_dataset": False,
        "note": "tatqa_dataset_test.json is the original unlabeled leaderboard artifact. Canonical processed test.jsonl is derived from tatqa_dataset_test_gold.json at the same pinned commit.",
    }


def build_download_meta(copied_files: dict[str, Path], repo_dir: Path) -> dict:
    readme_text = (repo_dir / "README.md").read_text(encoding="utf-8")
    if "Jan 2024" not in readme_text or "ground truth for the TAT-QA Test set" not in readme_text:
        raise RuntimeError("Pinned README is missing the Jan 2024 test-gold release note")
    return {
        "source_repo": SOURCE_REPO,
        "source_commit": PINNED_SOURCE_COMMIT,
        "source_paths": SOURCE_PATHS,
        "source_display_urls": {path: github_display_url(path) for path in SOURCE_PATHS},
        "source_raw_urls": {path: github_raw_url(path) for path in SOURCE_PATHS},
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": {path: copied_files[path].stat().st_size for path in SOURCE_PATHS},
        "sha256_by_file": {path: sha256_file(copied_files[path]) for path in SOURCE_PATHS},
        "download_method": "git_clone_checkout_copy",
        "notes": [
            "The pinned upstream commit is the Jan 2024 update announcing release of the TAT-QA test-set ground truth.",
            "The official scorer semantics live in tatqa_eval.py, tatqa_metric.py, and tatqa_utils.py at the pinned commit.",
            "Canonical supervised publication uses tatqa_dataset_test_gold.json for test, while tatqa_dataset_test.json is retained raw-only for provenance.",
        ],
    }


def copy_source_files(repo_dir: Path) -> dict[str, Path]:
    copied: dict[str, Path] = {}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for source_path in SOURCE_PATHS:
        src = repo_dir / source_path
        if not src.exists():
            raise FileNotFoundError(f"Missing source file {source_path} at pinned commit")
        dst = RAW_DIR / Path(source_path).name
        shutil.copy2(src, dst)
        copied[source_path] = dst
    return copied


def load_contexts(repo_dir: Path, source_path: str) -> list[dict]:
    data = load_json(repo_dir / source_path)
    if not isinstance(data, list):
        raise ValueError(f"{source_path} must contain a top-level list")
    return data


def split_integrity_audit(processed_by_split: dict[str, list[dict]]) -> dict:
    context_sets = {split: {row["context_id"] for row in rows} for split, rows in processed_by_split.items()}
    example_ids = {split: {row["example_id"] for row in rows} for split, rows in processed_by_split.items()}
    overlaps = {}
    split_names = list(processed_by_split)
    for idx, left in enumerate(split_names):
        for right in split_names[idx + 1 :]:
            overlaps[f"{left}__{right}"] = {
                "context_overlap_count": len(context_sets[left] & context_sets[right]),
                "question_overlap_count": len(example_ids[left] & example_ids[right]),
            }
            if overlaps[f"{left}__{right}"]["context_overlap_count"] != 0:
                raise ValueError(f"context overlap found between {left} and {right}")
            if overlaps[f"{left}__{right}"]["question_overlap_count"] != 0:
                raise ValueError(f"example_id overlap found between {left} and {right}")
    return overlaps


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    repo_dir, source_commit = clone_repo()
    if source_commit != PINNED_SOURCE_COMMIT:
        raise RuntimeError(f"Resolved commit {source_commit} does not match pinned commit {PINNED_SOURCE_COMMIT}")

    copied_files = copy_source_files(repo_dir)
    write_json(DOWNLOAD_META_PATH, build_download_meta(copied_files, repo_dir))

    processed_by_split: dict[str, list[dict]] = {}
    split_stats: dict[str, dict] = {}
    for split, source_path in CANONICAL_SPLIT_SOURCE_PATHS.items():
        contexts = load_contexts(repo_dir, source_path)
        rows, stats = build_processed_rows(split, source_path, source_commit, contexts)
        processed_by_split[split] = rows
        split_stats[split] = stats
        write_jsonl(PROCESSED_DIR / f"{split}.jsonl", rows)

    original_test_contexts = load_contexts(repo_dir, ORIGINAL_TEST_SOURCE_PATH)
    original_test_summary = build_original_test_summary(original_test_contexts)
    write_json(ORIGINAL_TEST_SUMMARY_PATH, original_test_summary)

    label_inventory = {
        "scale_inventory_official": OFFICIAL_SCALE_INVENTORY,
        "scale_inventory_observed": sorted({scale for stats in split_stats.values() for scale in stats["scale_distribution"].keys()}),
        "answer_type_raw_inventory_observed": sorted({answer_type for stats in split_stats.values() for answer_type in stats["answer_type_distribution"].keys()}),
        "answer_type_norm_inventory": sorted({normalize_answer_type(x) for stats in split_stats.values() for x in stats["answer_type_distribution"].keys()}),
        "answer_from_inventory_observed": sorted({value for stats in split_stats.values() for value in stats["answer_from_distribution"].keys()}),
        "notes": [
            "The canonical processed test split is derived from tatqa_dataset_test_gold.json at the pinned Jan 2024 upstream commit.",
            "The original unlabeled tatqa_dataset_test.json is retained raw-only for provenance and summarized in original_test_summary.json.",
        ],
    }
    write_json(LABEL_INVENTORY_PATH, label_inventory)

    split_integrity = split_integrity_audit(processed_by_split)
    ingest_summary = {
        "dataset_id": DATASET_ID,
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "canonical_split_source_paths": CANONICAL_SPLIT_SOURCE_PATHS,
        "original_unlabeled_test_source_path": ORIGINAL_TEST_SOURCE_PATH,
        "split_counts": {split: stats["counts"] for split, stats in split_stats.items()},
        "original_unlabeled_test_counts": {
            "contexts": original_test_summary["contexts"],
            "questions": original_test_summary["questions"],
        },
        "split_integrity": split_integrity,
        "observed_label_inventory_path": str(LABEL_INVENTORY_PATH),
        "notes": [
            "Train/dev counts match the canonical public release at the pinned commit.",
            "The labeled Jan 2024 test_gold release contains 277 contexts / 1663 questions, while the original unlabeled challenge test contains 278 contexts / 1669 questions.",
            "Canonical processed test.jsonl is derived from test_gold rather than the unlabeled leaderboard test artifact.",
        ],
    }
    write_json(INGEST_SUMMARY_PATH, ingest_summary)

    ingest_audit = {
        "dataset_id": DATASET_ID,
        "source_commit": source_commit,
        "split_counts": {split: stats["counts"] for split, stats in split_stats.items()},
        "answer_type_distribution": {split: stats["answer_type_distribution"] for split, stats in split_stats.items()},
        "answer_from_distribution": {split: stats["answer_from_distribution"] for split, stats in split_stats.items()},
        "scale_distribution": {split: stats["scale_distribution"] for split, stats in split_stats.items()},
        "arithmetic_or_count_fraction": {
            split: round(
                (stats["answer_type_distribution"].get("arithmetic", 0) + stats["answer_type_distribution"].get("count", 0))
                / stats["counts"]["questions"],
                6,
            )
            for split, stats in split_stats.items()
        },
        "empty_answer_example_ids": {split: stats["empty_answer_example_ids"] for split, stats in split_stats.items()},
        "context_level_split_integrity": split_integrity,
        "report_id_leakage_audit": {
            "performed": False,
            "reason": "No robust report identifier is exposed in the canonical raw schema beyond context/question UIDs.",
        },
        "release_vs_original_test_note": "At pinned commit 644770eb2a66dddc24b92303bd2acbad84cd2b9f, tatqa_dataset_test_gold.json has 277 contexts / 1663 questions, while tatqa_dataset_test.json has 278 contexts / 1669 questions.",
    }
    write_json(INGEST_AUDIT_PATH, ingest_audit)

    print(f"[DONE] Ingested {DATASET_ID}")
    for split, stats in split_stats.items():
        print(f"[{split}] contexts={stats['counts']['contexts']} questions={stats['counts']['questions']}")
    print(f"[original_test_raw_only] contexts={original_test_summary['contexts']} questions={original_test_summary['questions']}")
    print(f"[OUT] {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
