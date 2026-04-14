from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TASK_FINQA_SHARED_DIR = SCRIPT_DIR.parent.parent / "tasks" / "_finqa_shared"
TASK_CONV_SHARED_DIR = SCRIPT_DIR.parent.parent / "tasks" / "_convfinqa_shared"
for path in [TASK_FINQA_SHARED_DIR, TASK_CONV_SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from normalize_finqa_answer import normalize_finqa_answer  # noqa: E402
from serialize_finqa_table import serialize_finqa_table  # noqa: E402
from normalize_convfinqa_program import tokenize_source_program  # noqa: E402
from serialize_convfinqa_dialogue import serialize_convfinqa_dialogue  # noqa: E402


DATASET_ID = "convfinqa_official_v0"
SOURCE_REPO = "czyssrs/ConvFinQA"
SOURCE_REPO_URL = "https://github.com/czyssrs/ConvFinQA.git"
PINNED_SOURCE_COMMIT = "cf3eed2d5984960bf06bb8145bcea5e80b0222a6"
RAW_DIR = Path("data/convfinqa_official/raw")
PROCESSED_DIR = Path("data/convfinqa_official/processed")
REPORT_DIR = Path("reports/convfinqa_official")
DOWNLOAD_META_PATH = RAW_DIR / "download_meta.json"
LABEL_INVENTORY_PATH = PROCESSED_DIR / "label_inventory.json"
INGEST_SUMMARY_PATH = PROCESSED_DIR / "ingest_summary.json"
TEST_RELEASE_SUMMARY_PATH = PROCESSED_DIR / "test_release_summary.json"
INGEST_AUDIT_PATH = REPORT_DIR / "ingest_audit.json"

GIT_TRACKED_SOURCE_PATHS = [
    "README.md",
    "LICENSE",
    "data.zip",
    "code/utils/general_utils.py",
    "code/finqanet_generator/finqa_utils.py",
]
ARCHIVE_MEMBER_PATHS = [
    "data/train.json",
    "data/dev.json",
    "data/test_private.json",
    "data/train_turn.json",
    "data/dev_turn.json",
    "data/test_turn_private.json",
]
CONVERSATION_SOURCE_PATHS = {
    "train": "data/train.json",
    "dev": "data/dev.json",
    "test_private": "data/test_private.json",
}
TURN_SOURCE_PATHS = {
    "train": "data/train_turn.json",
    "dev": "data/dev_turn.json",
}
UNLABELED_TEST_TURN_SOURCE_PATH = "data/test_turn_private.json"
EXPECTED_TEST_PRIVATE_ANNOTATION_KEYS = ["cur_dial"]


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


def archive_member_display_url(source_commit: str, member_path: str) -> str:
    return f"{github_display_url(source_commit, 'data.zip')}#member={member_path}"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def clone_repo() -> tuple[Path, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="convfinqa_clone_"))
    subprocess.run(["git", "clone", SOURCE_REPO_URL, str(temp_dir)], check=True)
    subprocess.run(["git", "-C", str(temp_dir), "checkout", PINNED_SOURCE_COMMIT], check=True)
    commit = (
        subprocess.run(["git", "-C", str(temp_dir), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        .stdout.strip()
    )
    return temp_dir, commit


def copy_git_tracked_sources(repo_dir: Path) -> dict[str, Path]:
    copied = {}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for source_path in GIT_TRACKED_SOURCE_PATHS:
        src = repo_dir / source_path
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")
        if source_path == "code/utils/general_utils.py":
            dst_name = "general_utils.py"
        elif source_path == "code/finqanet_generator/finqa_utils.py":
            dst_name = "generator_finqa_utils.py"
        else:
            dst_name = Path(source_path).name
        dst = RAW_DIR / dst_name
        shutil.copy2(src, dst)
        copied[source_path] = dst
    return copied


def extract_archive_members(repo_dir: Path) -> dict[str, Path]:
    archive_path = repo_dir / "data.zip"
    extracted_root = Path(tempfile.mkdtemp(prefix="convfinqa_zip_"))
    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
        for member in ARCHIVE_MEMBER_PATHS:
            if member not in names:
                raise FileNotFoundError(f"Missing archive member: {member}")
            zf.extract(member, extracted_root)

    copied = {}
    for member in ARCHIVE_MEMBER_PATHS:
        src = extracted_root / member
        dst = RAW_DIR / Path(member).name
        shutil.copy2(src, dst)
        copied[member] = dst
    return copied


def build_download_meta(source_commit: str, git_copied: dict[str, Path], archive_copied: dict[str, Path], repo_dir: Path) -> dict:
    tags = (
        subprocess.run(["git", "-C", str(repo_dir), "tag"], check=True, capture_output=True, text=True)
        .stdout.strip()
        .splitlines()
    )
    source_paths = GIT_TRACKED_SOURCE_PATHS + [f"data.zip::{member}" for member in ARCHIVE_MEMBER_PATHS]
    display_urls = {path: github_display_url(source_commit, path) for path in GIT_TRACKED_SOURCE_PATHS}
    raw_urls = {path: github_raw_url(source_commit, path) for path in GIT_TRACKED_SOURCE_PATHS}
    for member in ARCHIVE_MEMBER_PATHS:
        source_key = f"data.zip::{member}"
        display_urls[source_key] = archive_member_display_url(source_commit, member)
        raw_urls[source_key] = github_raw_url(source_commit, "data.zip")

    file_sizes = {path: git_copied[path].stat().st_size for path in GIT_TRACKED_SOURCE_PATHS}
    file_sizes.update({f"data.zip::{member}": archive_copied[member].stat().st_size for member in ARCHIVE_MEMBER_PATHS})
    sha_map = {path: sha256_file(git_copied[path]) for path in GIT_TRACKED_SOURCE_PATHS}
    sha_map.update({f"data.zip::{member}": sha256_file(archive_copied[member]) for member in ARCHIVE_MEMBER_PATHS})

    return {
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "source_paths": source_paths,
        "source_display_urls": display_urls,
        "source_raw_urls": raw_urls,
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": file_sizes,
        "sha256_by_file": sha_map,
        "download_method": "git_clone_checkout_extract_zip_members",
        "repo_tags_at_download": tags,
        "repo_has_tagged_releases": bool(tags),
        "notes": [
            "The official ConvFinQA repo has no tagged releases; reproducibility requires pinning a concrete commit SHA.",
            "ConvFinQA is a FinQA-family conversational derivative, not an independent evidence-source family.",
            "The pinned release archive exposes labeled train/dev files and only private unlabeled test files.",
        ],
    }


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


def derive_conversation_id(example_id: str) -> str:
    return re.sub(r"_\d+$", "", example_id)


def derive_conversation_form(example_id: str) -> tuple[str, str]:
    prefix = example_id.split("/", 1)[0]
    raw_form = prefix.split("_", 1)[0]
    return raw_form, {"Single": "simple", "Double": "hybrid"}.get(raw_form, raw_form.lower())


def count_supporting_facts(gold_ind) -> int:
    if isinstance(gold_ind, dict):
        return len(gold_ind)
    if isinstance(gold_ind, list):
        return len(gold_ind)
    return 0


def field_summary(rows: list[dict]) -> dict:
    top_fields = Counter()
    annotation_fields = Counter()
    qa_fields = Counter()
    for row in rows:
        top_fields.update(row.keys())
        annotation = row.get("annotation", {})
        if isinstance(annotation, dict):
            annotation_fields.update(annotation.keys())
        qa = row.get("qa")
        if isinstance(qa, dict):
            qa_fields.update(qa.keys())
    return {
        "top_level_fields": sorted(top_fields),
        "annotation_fields": sorted(annotation_fields),
        "qa_fields": sorted(qa_fields),
    }


def build_processed_row(split: str, source_commit: str, source_path: str, row: dict, *, require_labels: bool) -> dict:
    missing_top = [key for key in ["id", "pre_text", "post_text", "table", "annotation"] if key not in row]
    if missing_top:
        raise KeyError(f"{split}:{row.get('id', '<unknown>')} missing top-level keys {missing_top}")

    annotation = row["annotation"]
    if not isinstance(annotation, dict):
        raise ValueError(f"{split}:{row['id']} annotation must be a dict")
    if "cur_dial" not in annotation:
        raise KeyError(f"{split}:{row['id']} missing annotation.cur_dial")
    if require_labels:
        missing_ann = [key for key in ["cur_program", "exe_ans", "gold_ind", "cur_type", "turn_ind", "qa_split"] if key not in annotation]
        if missing_ann:
            raise KeyError(f"{split}:{row['id']} missing labeled annotation keys {missing_ann}")

    pre_text = validate_text_list("pre_text", row["pre_text"])
    post_text = validate_text_list("post_text", row["post_text"])
    table = validate_table(row["table"])
    dialogue_history = validate_text_list("annotation.cur_dial", annotation["cur_dial"])
    if not dialogue_history:
        raise ValueError(f"{split}:{row['id']} cur_dial must be non-empty")

    example_id = row["id"]
    if not isinstance(example_id, str) or not example_id.strip():
        raise ValueError(f"{split}: example id must be a non-empty string")

    conversation_id = derive_conversation_id(example_id)
    raw_form, norm_form = derive_conversation_form(example_id)
    current_question = dialogue_history[-1]
    current_qa_split = annotation.get("qa_split")[-1] if isinstance(annotation.get("qa_split"), list) and annotation.get("qa_split") else None

    processed = {
        "example_id": example_id,
        "conversation_id": conversation_id,
        "dataset_id": DATASET_ID,
        "split": split,
        "turn_index": annotation.get("turn_ind", len(dialogue_history) - 1),
        "current_question": current_question,
        "dialogue_history_questions": dialogue_history,
        "dialogue_history_serialized": serialize_convfinqa_dialogue(dialogue_history),
        "pre_text": pre_text,
        "post_text": post_text,
        "table": table,
        "table_serialized": serialize_finqa_table(table),
        "current_turn_type": annotation.get("cur_type"),
        "conversation_form": norm_form,
        "conversation_form_raw": raw_form,
        "qa_split": annotation.get("qa_split"),
        "current_qa_split": current_qa_split,
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "source_path": source_path,
        "source_filename": row.get("filename"),
        "source_fields_present": {
            "top_level": sorted(row.keys()),
            "annotation": sorted(annotation.keys()),
            "qa": sorted(row.get("qa", {}).keys()) if isinstance(row.get("qa"), dict) else [],
        },
        "source_original_programs": {key: annotation.get(key) for key in ["original_program", "original_program_0", "original_program_1"] if key in annotation},
    }

    if require_labels:
        processed.update(
            {
                "gold_program_tokens": tokenize_source_program(annotation["cur_program"]),
                "gold_program_str": annotation["cur_program"],
                "gold_execution_answer": normalize_finqa_answer(annotation.get("exe_ans")),
                "gold_supporting_facts": annotation.get("gold_ind"),
            }
        )

    return processed


def validate_turn_split(processed_rows: list[dict], *, split: str) -> dict:
    seen_example_ids = set()
    seen_conversation_turn_pairs = set()
    turn_type_counter = Counter()
    history_length_counter = Counter()
    supporting_fact_counter = Counter()
    current_qa_split_counter = Counter()
    conversation_form_counter = Counter()

    for row in processed_rows:
        if row["example_id"] in seen_example_ids:
            raise ValueError(f"Duplicate example_id in {split}: {row['example_id']}")
        seen_example_ids.add(row["example_id"])

        pair = (row["conversation_id"], row["turn_index"])
        if pair in seen_conversation_turn_pairs:
            raise ValueError(f"Duplicate conversation_id/turn_index in {split}: {pair}")
        seen_conversation_turn_pairs.add(pair)

        turn_type_counter[row.get("current_turn_type") or "__missing__"] += 1
        history_length_counter[len(row["dialogue_history_questions"])] += 1
        supporting_fact_counter[count_supporting_facts(row.get("gold_supporting_facts"))] += 1
        current_qa_split_counter[row.get("current_qa_split")] += 1
        conversation_form_counter[row["conversation_form"]] += 1

    return {
        "example_count": len(processed_rows),
        "conversation_count": len({row['conversation_id'] for row in processed_rows}),
        "turn_type_distribution": dict(sorted(turn_type_counter.items(), key=lambda kv: str(kv[0]))),
        "history_length_distribution": dict(sorted(history_length_counter.items())),
        "supporting_fact_count_distribution": dict(sorted(supporting_fact_counter.items())),
        "current_qa_split_distribution": dict(sorted(current_qa_split_counter.items(), key=lambda kv: str(kv[0]))),
        "conversation_form_distribution": dict(sorted(conversation_form_counter.items())),
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    repo_dir, source_commit = clone_repo()
    try:
        if source_commit != PINNED_SOURCE_COMMIT:
            raise RuntimeError(f"Expected pinned commit {PINNED_SOURCE_COMMIT}, got {source_commit}")

        git_copied = copy_git_tracked_sources(repo_dir)
        archive_copied = extract_archive_members(repo_dir)
        write_json(DOWNLOAD_META_PATH, build_download_meta(source_commit, git_copied, archive_copied, repo_dir))

        conversation_rows = {
            split: json.loads((RAW_DIR / Path(source_path).name).read_text(encoding="utf-8"))
            for split, source_path in CONVERSATION_SOURCE_PATHS.items()
        }
        turn_rows = {
            split: json.loads((RAW_DIR / Path(source_path).name).read_text(encoding="utf-8"))
            for split, source_path in TURN_SOURCE_PATHS.items()
        }
        test_turn_private_rows = json.loads((RAW_DIR / Path(UNLABELED_TEST_TURN_SOURCE_PATH).name).read_text(encoding="utf-8"))

        processed_by_split = {}
        validation_by_split = {}
        source_schema = {}
        for split, source_path in TURN_SOURCE_PATHS.items():
            rows = turn_rows[split]
            source_schema[split] = field_summary(rows)
            processed_rows = [build_processed_row(split, source_commit, source_path, row, require_labels=True) for row in rows]
            processed_by_split[split] = processed_rows
            validation_by_split[split] = validate_turn_split(processed_rows, split=split)
            write_jsonl(PROCESSED_DIR / f"{split}.jsonl", processed_rows)

        source_schema["train_conversation"] = field_summary(conversation_rows["train"])
        source_schema["dev_conversation"] = field_summary(conversation_rows["dev"])
        source_schema["test_private_conversation"] = field_summary(conversation_rows["test_private"])
        source_schema["test_private_turn"] = field_summary(test_turn_private_rows)

        for split in ["train", "dev"]:
            expected = {row["id"] for row in conversation_rows[split]}
            observed = {row["conversation_id"] for row in processed_by_split[split]}
            missing = sorted(observed - expected)
            if missing:
                raise ValueError(f"Turn-level rows in {split} reference conversation ids missing from the conversation-level release: {missing[:10]}")

        test_private_annotation_keys = source_schema["test_private_turn"]["annotation_fields"]
        public_test_gold_verified = all(key in test_private_annotation_keys for key in ["cur_program", "exe_ans", "gold_ind"])
        if public_test_gold_verified:
            raise RuntimeError("Pinned ConvFinQA release unexpectedly exposes public test gold. Revisit split policy before publishing.")

        observed_ops = Counter()
        turn_type_inventory = set()
        for rows in processed_by_split.values():
            for row in rows:
                turn_type_inventory.add(row["current_turn_type"])
                body = row["gold_program_tokens"][:-1]
                if len(body) >= 4:
                    for idx in range(0, len(body), 4):
                        observed_ops[body[idx].rstrip("(")] += 1

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
            "structural_tokens": [")", "EOF"],
            "reference_pattern": "^#\\d+$",
            "single_value_program_note": "number_turn supervision can be a single numeric token followed by EOF.",
            "current_turn_type_inventory": sorted(turn_type_inventory),
            "conversation_form_inventory": sorted({row['conversation_form'] for rows in processed_by_split.values() for row in rows}),
            "qa_split_values": sorted({row['current_qa_split'] for rows in processed_by_split.values() for row in rows if row['current_qa_split'] is not None}),
            "observed_operation_frequency": dict(sorted(observed_ops.items())),
        }
        write_json(LABEL_INVENTORY_PATH, label_inventory)

        test_release_summary = {
            "split": "test_private",
            "conversation_file": CONVERSATION_SOURCE_PATHS["test_private"],
            "turn_file": UNLABELED_TEST_TURN_SOURCE_PATH,
            "conversation_count": len(conversation_rows["test_private"]),
            "turn_count": len(test_turn_private_rows),
            "public_test_gold_verified": False,
            "gold_fields_present": [],
            "gold_fields_missing": ["cur_program", "exe_ans", "gold_ind"],
            "annotation_fields_observed": test_private_annotation_keys,
            "published_as_supervised_split": False,
            "note": "The pinned official release provides only input report and conversation history for the private test split. No public gold turn-level supervision is published at this commit.",
        }
        write_json(TEST_RELEASE_SUMMARY_PATH, test_release_summary)

        ingest_summary = {
            "dataset_id": DATASET_ID,
            "source_repo": SOURCE_REPO,
            "source_commit": source_commit,
            "canonical_modeling_unit": "turn_level",
            "supervised_splits": {split: validation_by_split[split]["example_count"] for split in ["train", "dev"]},
            "conversation_counts": {split: len(conversation_rows[split]) for split in ["train", "dev", "test_private"]},
            "turn_counts": {"train": len(turn_rows["train"]), "dev": len(turn_rows["dev"]), "test_private": len(test_turn_private_rows)},
            "published_supervised_test_split": False,
            "public_test_gold_verified": False,
            "source_schema": source_schema,
            "validation_by_split": validation_by_split,
            "finqa_family_note": "ConvFinQA is derived from FinQA and should not be treated as an independent evidence-source family.",
        }
        write_json(INGEST_SUMMARY_PATH, ingest_summary)

        ingest_audit = {
            "dataset_id": DATASET_ID,
            "source_repo": SOURCE_REPO,
            "source_commit": source_commit,
            "validation_by_split": validation_by_split,
            "source_schema": source_schema,
            "public_test_audit": test_release_summary,
            "train_dev_conversation_overlap_sample": sorted({row["id"] for row in conversation_rows["train"]} & {row["id"] for row in conversation_rows["dev"]})[:20],
            "notes": [
                "Canonical processed rows are turn-level and sourced only from train_turn.json and dev_turn.json.",
                "The official test release is private and unlabeled at the pinned commit; no supervised test.jsonl is published.",
            ],
        }
        write_json(INGEST_AUDIT_PATH, ingest_audit)

        print(f"[DONE] Ingested {DATASET_ID}")
        print(f"[INFO] train turns={len(turn_rows['train'])} dev turns={len(turn_rows['dev'])} test_private turns={len(test_turn_private_rows)}")
        print(f"[INFO] public_test_gold_verified={public_test_gold_verified}")
        print(f"[OUT]  {PROCESSED_DIR / 'train.jsonl'}")
        print(f"[OUT]  {PROCESSED_DIR / 'dev.jsonl'}")
        print(f"[OUT]  {TEST_RELEASE_SUMMARY_PATH}")
        print(f"[OUT]  {INGEST_AUDIT_PATH}")
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
