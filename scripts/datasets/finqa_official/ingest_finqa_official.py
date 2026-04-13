from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_SHARED_DIR = SCRIPT_DIR.parent.parent / "tasks" / "_finqa_shared"
if str(TASK_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_SHARED_DIR))

from normalize_finqa_answer import normalize_finqa_answer  # noqa: E402
from parse_finqa_program import tokenize_source_program  # noqa: E402
from serialize_finqa_table import serialize_finqa_table  # noqa: E402


DATASET_ID = "finqa_official_v0"
SOURCE_REPO = "czyssrs/FinQA"
SOURCE_REPO_URL = "https://github.com/czyssrs/FinQA.git"
PINNED_SOURCE_COMMIT = "0f16e2867befa6840783e58be38c9efb9229d742"
RAW_DIR = Path("data/finqa_official/raw")
PROCESSED_DIR = Path("data/finqa_official/processed")
SOURCE_PATHS = [
    "dataset/train.json",
    "dataset/dev.json",
    "dataset/test.json",
    "dataset/private_test.json",
    "LICENSE",
    "README.md",
]
PUBLIC_SPLIT_PATHS = {
    "train": "dataset/train.json",
    "dev": "dataset/dev.json",
    "test": "dataset/test.json",
}
PRIVATE_TEST_PATH = "dataset/private_test.json"
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "label_inventory.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
PRIVATE_TEST_SUMMARY_PATH = PROCESSED_DIR / "private_test_summary.json"
README_BUGFIX_NOTES = [
    "2022-04-29 retriever formatting bugfix",
    "2022-05-04 table_row_to_text bugfix and corrected leaderboard results",
    "2022-05-15 private-test refactor for easier testing",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def github_display_url(source_commit: str, source_path: str) -> str:
    return f"https://github.com/{SOURCE_REPO}/blob/{source_commit}/{source_path}"


def github_raw_url(source_commit: str, source_path: str) -> str:
    return f"https://raw.githubusercontent.com/{SOURCE_REPO}/{source_commit}/{source_path}"


def clone_repo() -> tuple[Path, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="finqa_clone_"))
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


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def derive_report_page_id(example_id: str) -> str:
    match = re.match(r"^(.*)-\d+$", example_id)
    return match.group(1) if match else example_id


def validate_text_list(name: str, value) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a list of strings")
    return value


def validate_table(table) -> list[list[str]]:
    if not isinstance(table, list):
        raise ValueError("table must be a 2D list")
    normalized = []
    for row in table:
        if not isinstance(row, list):
            raise ValueError("table rows must be lists")
        normalized.append([str(cell) for cell in row])
    return normalized


def copy_source_files(repo_dir: Path) -> dict[str, Path]:
    copied = {}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for source_path in SOURCE_PATHS:
        src = repo_dir / source_path
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")
        dst = RAW_DIR / Path(source_path).name
        shutil.copy2(src, dst)
        copied[source_path] = dst
    return copied


def build_download_meta(source_commit: str, copied_files: dict[str, Path], repo_dir: Path) -> dict:
    tags = (
        subprocess.run(
            ["git", "-C", str(repo_dir), "tag"],
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
        .splitlines()
    )
    readme_text = (repo_dir / "README.md").read_text(encoding="utf-8")
    for marker in ["05/15/2022", "05/04/2022", "04/29/2022"]:
        if marker not in readme_text:
            raise RuntimeError(f"Pinned README is missing expected reproducibility note {marker}")

    return {
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "source_paths": SOURCE_PATHS,
        "source_display_urls": {path: github_display_url(source_commit, path) for path in SOURCE_PATHS},
        "source_raw_urls": {path: github_raw_url(source_commit, path) for path in SOURCE_PATHS},
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": {path: copied_files[path].stat().st_size for path in SOURCE_PATHS},
        "sha256_by_file": {path: sha256_file(copied_files[path]) for path in SOURCE_PATHS},
        "download_method": "git_clone_checkout_copy",
        "notes": [
            "The official FinQA repo has no tagged releases; reproducibility requires pinning a concrete commit SHA.",
            "The pinned README includes the documented 2022 bugfix notes dated 2022-04-29, 2022-05-04, and 2022-05-15.",
        ],
        "repo_tags_at_download": tags,
        "repo_has_tagged_releases": bool(tags),
        "readme_bugfix_history": README_BUGFIX_NOTES,
    }


def source_field_summary(rows: list[dict]) -> dict:
    top_fields = Counter()
    qa_fields = Counter()
    for row in rows:
        top_fields.update(row.keys())
        qa = row.get("qa", {})
        if isinstance(qa, dict):
            qa_fields.update(qa.keys())
    return {
        "top_level_fields": sorted(top_fields),
        "qa_fields": sorted(qa_fields),
    }


def build_processed_row(split: str, source_commit: str, source_path: str, row: dict) -> dict:
    required_top_keys = ["id", "pre_text", "post_text", "table", "qa"]
    missing_top = [key for key in required_top_keys if key not in row]
    if missing_top:
        raise KeyError(f"{split}:{row.get('id', '<unknown>')} missing top-level keys {missing_top}")

    qa = row["qa"]
    if not isinstance(qa, dict):
        raise ValueError(f"{split}:{row['id']} qa must be a dict")

    required_qa_keys = ["question", "program", "gold_inds", "exe_ans", "program_re"]
    missing_qa = [key for key in required_qa_keys if key not in qa]
    if missing_qa:
        raise KeyError(f"{split}:{row['id']} missing qa keys {missing_qa}")

    pre_text = validate_text_list("pre_text", row["pre_text"])
    post_text = validate_text_list("post_text", row["post_text"])
    table = validate_table(row["table"])
    question = qa["question"]
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"{split}:{row['id']} question must be a non-empty string")

    gold_program = qa["program"]
    if not isinstance(gold_program, str) or not gold_program.strip():
        raise ValueError(f"{split}:{row['id']} program must be a non-empty string")

    tokens = tokenize_source_program(gold_program)

    return {
        "example_id": row["id"],
        "dataset_id": DATASET_ID,
        "split": split,
        "report_page_id": derive_report_page_id(row["id"]),
        "source_filename": row.get("filename"),
        "question": question,
        "pre_text": pre_text,
        "post_text": post_text,
        "table": table,
        "table_serialized": serialize_finqa_table(table),
        "gold_program_tokens": tokens,
        "gold_program_str": gold_program,
        "gold_program_nested": qa.get("program_re"),
        "gold_supporting_facts": qa.get("gold_inds"),
        "gold_execution_answer": normalize_finqa_answer(qa.get("exe_ans")),
        "gold_answer_raw": {key: qa.get(key) for key in ["answer", "exe_ans"] if key in qa},
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "source_path": source_path,
        "source_fields_present": {
            "top_level": sorted(row.keys()),
            "qa": sorted(qa.keys()),
        },
    }


def validate_public_splits(processed_by_split: dict[str, list[dict]]) -> dict:
    seen_ids = set()
    report_page_ids = {}
    for split, rows in processed_by_split.items():
        report_page_ids[split] = set()
        for row in rows:
            if row["example_id"] in seen_ids:
                raise ValueError(f"Duplicate example_id across public splits: {row['example_id']}")
            seen_ids.add(row["example_id"])
            report_page_ids[split].add(row["report_page_id"])

    overlap_report = {}
    split_names = list(processed_by_split)
    for idx, left in enumerate(split_names):
        for right in split_names[idx + 1 :]:
            overlap = sorted(report_page_ids[left] & report_page_ids[right])
            overlap_report[f"{left}__{right}"] = {
                "count": len(overlap),
                "sample": overlap[:20],
            }
            if overlap:
                raise ValueError(f"Split-level report/page overlap detected between {left} and {right}")
    return overlap_report


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    repo_dir, source_commit = clone_repo()
    try:
        if source_commit != PINNED_SOURCE_COMMIT:
            raise RuntimeError(f"Expected pinned commit {PINNED_SOURCE_COMMIT}, got {source_commit}")

        copied_files = copy_source_files(repo_dir)
        download_meta = build_download_meta(source_commit, copied_files, repo_dir)
        write_json(DOWNLOAD_META_PATH, download_meta)

        raw_rows_by_split = {
            split: json.loads(copied_files[source_path].read_text(encoding="utf-8"))
            for split, source_path in PUBLIC_SPLIT_PATHS.items()
        }
        private_test_rows = json.loads(copied_files[PRIVATE_TEST_PATH].read_text(encoding="utf-8"))

        processed_by_split = {}
        observed_ops = Counter()
        observed_step_counts = Counter()
        source_schema = {}
        for split, source_path in PUBLIC_SPLIT_PATHS.items():
            rows = raw_rows_by_split[split]
            source_schema[split] = source_field_summary(rows)
            processed_rows = [build_processed_row(split, source_commit, source_path, row) for row in rows]
            processed_by_split[split] = processed_rows
            write_jsonl(PROCESSED_DIR / f"{split}.jsonl", processed_rows)

            for processed in processed_rows:
                tokens = processed["gold_program_tokens"][:-1]
                observed_step_counts[len(tokens) // 4] += 1
                for idx in range(0, len(tokens), 4):
                    observed_ops[tokens[idx].rstrip("(")] += 1

        overlap_report = validate_public_splits(processed_by_split)

        private_summary = {
            "split": "private_test",
            "count": len(private_test_rows),
            "top_level_fields": source_field_summary(private_test_rows)["top_level_fields"],
            "qa_fields": source_field_summary(private_test_rows)["qa_fields"],
            "no_references": True,
            "published_in_supervised_canonical_dataset": False,
        }
        write_json(PRIVATE_TEST_SUMMARY_PATH, private_summary)

        label_inventory = {
            "dataset_id": DATASET_ID,
            "source_repo": SOURCE_REPO,
            "source_commit": source_commit,
            "operation_names": [
                "add",
                "subtract",
                "multiply",
                "divide",
                "greater",
                "exp",
                "table_max",
                "table_min",
                "table_sum",
                "table_average",
            ],
            "operation_tokens": [
                "add(",
                "subtract(",
                "multiply(",
                "divide(",
                "greater(",
                "exp(",
                "table_max(",
                "table_min(",
                "table_sum(",
                "table_average(",
            ],
            "structural_tokens": [")", "EOF"],
            "reference_token_pattern": "^#\\d+$",
            "constant_token_pattern": "^const_(?:m1|[-+]?(?:\\d+\\.?\\d*|\\.\\d+))$",
            "observed_operation_frequencies": dict(sorted(observed_ops.items())),
            "observed_program_step_count_distribution": {
                str(length): count for length, count in sorted(observed_step_counts.items())
            },
            "canonical_tokenization_note": "Canonical gold programs are tokenized using the official evaluator tokenization with underscore table operations."
        }
        write_json(LABEL_INVENTORY_PATH, label_inventory)

        ingest_summary = {
            "dataset_id": DATASET_ID,
            "source_repo": SOURCE_REPO,
            "source_commit": source_commit,
            "canonical_public_splits": {split: len(rows) for split, rows in processed_by_split.items()},
            "private_test_count": len(private_test_rows),
            "private_test_publication_policy": "raw_provenance_only_no_references_not_published_as_supervised_split",
            "public_source_schema_by_split": source_schema,
            "private_test_schema": source_field_summary(private_test_rows),
            "report_page_overlap_audit": overlap_report,
            "headline_or_page_scope": "report_page_numerical_reasoning",
            "task_target": "program_generation",
            "primary_metric": "execution_accuracy",
            "secondary_metric": "program_accuracy",
            "repo_has_tagged_releases": False,
            "readme_bugfix_history": README_BUGFIX_NOTES,
            "schema_drift_note": "The pinned official repo contains additional retrieval-era fields beyond the README summary; the canonical processed dataset preserves the public supervised reasoning fields and records observed source field sets.",
            "canonical_table_serialization": "deterministic_tsv_with_escaped_control_characters",
        }
        write_json(INGEST_SUMMARY_PATH, ingest_summary)

        print("[DONE] FinQA official ingest complete")
        print(f"[SOURCE_COMMIT] {source_commit}")
        for split, rows in processed_by_split.items():
            print(f"[{split.upper()}] data/finqa_official/processed/{split}.jsonl ({len(rows)} rows)")
        print(f"[PRIVATE_TEST] raw only ({len(private_test_rows)} rows)")
        print(f"[LABEL_INVENTORY] {LABEL_INVENTORY_PATH}")
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
