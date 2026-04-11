from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


REQUIRED_FILES = ("train.json", "test.json", "train.xml", "test.xml")
DEFAULT_REPO_URL = "https://github.com/mrlamm/textual-analogy-parsing.git"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_nonempty_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def count_xml_sentences(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"<S\\b", text))


def ensure_repo(repo_dir: Path, repo_url: str) -> Path:
    if (repo_dir / ".git").exists():
        return repo_dir

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", repo_url, str(repo_dir)],
        check=True,
    )
    return repo_dir


def resolve_source_data_dir(args: argparse.Namespace) -> tuple[Path, dict]:
    if args.source_dir is not None:
        source_dir = args.source_dir.expanduser().resolve()
        return source_dir, {
            "acquisition_mode": "existing_local_source_dir",
            "source_dir": str(source_dir),
        }

    repo_dir = args.repo_dir.expanduser().resolve()
    if args.clone_if_missing:
        ensure_repo(repo_dir=repo_dir, repo_url=args.repo_url)

    source_dir = (repo_dir / "data").resolve()
    return source_dir, {
        "acquisition_mode": "git_repo_data_dir",
        "repo_dir": str(repo_dir),
        "repo_url": args.repo_url,
        "source_dir": str(source_dir),
        "clone_if_missing": bool(args.clone_if_missing),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Direct path to the author's data/ directory. If provided, repo cloning is skipped.",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path.home() / "Downloads" / "textual-analogy-parsing",
        help="Local clone path for the author repo when using repo-based acquisition.",
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        default=DEFAULT_REPO_URL,
        help="Author repository URL.",
    )
    parser.add_argument(
        "--clone-if-missing",
        action="store_true",
        help="Clone the author repo to --repo-dir if it does not already exist.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/lamm2018_tap/raw"),
        help="Pipeline raw staging directory.",
    )
    args = parser.parse_args()

    source_dir, acquisition_meta = resolve_source_data_dir(args)
    raw_dir = args.raw_dir.expanduser().resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_FILES if not (source_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required source files in {source_dir}: {missing}"
        )

    file_meta: dict[str, dict] = {}
    for name in REQUIRED_FILES:
        src = source_dir / name
        dst = raw_dir / name
        shutil.copy2(src, dst)

        meta = {
            "source_path": str(src),
            "copied_to": str(dst),
            "size_bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
        }
        if name.endswith(".json"):
            meta["nonempty_line_count"] = count_nonempty_lines(dst)
        if name.endswith(".xml"):
            meta["sentence_count_from_xml"] = count_xml_sentences(dst)

        file_meta[name] = meta

    warnings: list[str] = []

    train_json_lines = file_meta["train.json"].get("nonempty_line_count")
    test_json_lines = file_meta["test.json"].get("nonempty_line_count")
    train_xml_sentences = file_meta["train.xml"].get("sentence_count_from_xml")
    test_xml_sentences = file_meta["test.xml"].get("sentence_count_from_xml")

    if train_xml_sentences is not None and train_json_lines is not None:
        if train_xml_sentences != train_json_lines:
            warnings.append(
                f"train.xml sentence count ({train_xml_sentences}) != train.json line count ({train_json_lines})."
            )

    if test_xml_sentences is not None and test_json_lines is not None:
        if test_xml_sentences != test_json_lines:
            warnings.append(
                f"test.xml sentence count ({test_xml_sentences}) != test.json line count ({test_json_lines})."
            )

    if test_json_lines is not None and test_json_lines != 100:
        warnings.append(
            f"test.json contains {test_json_lines} non-empty lines, not 100; "
            "keep this discrepancy visible for later benchmark audit."
        )

    ingest_meta = {
        "dataset_module_id": "lamm2018_tap_v0",
        "dataset_slug": "lamm2018_tap",
        "canonical_source": {
            "type": "github_repository",
            "repo_url": args.repo_url,
            "expected_subdir": "data",
            "expected_files": list(REQUIRED_FILES),
        },
        "acquisition": acquisition_meta,
        "raw_dir": str(raw_dir),
        "split_policy": {
            "type": "author_provided",
            "preserve_official_split": True,
            "notes": "Use train/test exactly as released by the authors.",
        },
        "publication": {
            "status": "blocked_pending_licensing_review",
            "allowed": False,
            "reason": "Underlying text is license-sensitive; do not redistribute text-bearing artifacts until provenance/licensing is cleared.",
        },
        "files": file_meta,
        "warnings": warnings,
    }

    meta_path = raw_dir / "lamm2018_tap_ingest_meta.json"
    meta_path.write_text(
        json.dumps(ingest_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("[DONE] Ingest complete")
    print(f"[META] {meta_path}")
    for name, meta in file_meta.items():
        print(f"[{name}] {meta}")
    if warnings:
        print("[WARNINGS]")
        for warning in warnings:
            print(f" - {warning}")


if __name__ == "__main__":
    main()
