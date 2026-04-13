from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SOURCE_REPO = "ymntseng/DynamicESG"
SOURCE_REPO_URL = "https://github.com/ymntseng/DynamicESG.git"


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


def clone_repo(
    repo_url: str = SOURCE_REPO_URL,
    checkout_commit: str | None = None,
) -> tuple[Path, str, str | None]:
    temp_dir = Path(tempfile.mkdtemp(prefix="dynamic_esg_clone_"))
    subprocess.run(["git", "clone", repo_url, str(temp_dir)], check=True)
    if checkout_commit is not None:
        subprocess.run(["git", "-C", str(temp_dir), "checkout", checkout_commit], check=True)

    commit = (
        subprocess.run(
            ["git", "-C", str(temp_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
    )
    branch = (
        subprocess.run(
            ["git", "-C", str(temp_dir), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
    )
    return temp_dir, commit, branch or None


def copy_source_files(repo_dir: Path, source_paths: list[str], raw_dir: Path) -> dict[str, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    copied = {}
    for source_path in source_paths:
        src = repo_dir / source_path
        if not src.exists():
            raise FileNotFoundError(f"Missing source file in cloned repo: {src}")
        dst = raw_dir / Path(source_path).name
        shutil.copy2(src, dst)
        copied[source_path] = dst
    return copied


def build_download_meta(
    *,
    source_commit: str,
    source_branch_at_download: str | None,
    source_paths: list[str],
    copied_files: dict[str, Path],
    download_method: str,
) -> dict:
    file_sizes_bytes = {path: copied_files[path].stat().st_size for path in source_paths}
    sha256_by_file = {path: sha256_file(copied_files[path]) for path in source_paths}
    return {
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "source_branch_at_download": source_branch_at_download,
        "source_paths": source_paths,
        "source_display_urls": {
            path: github_display_url(source_commit, path) for path in source_paths
        },
        "source_raw_urls": {
            path: github_raw_url(source_commit, path) for path in source_paths
        },
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "file_sizes_bytes": file_sizes_bytes,
        "sha256_by_file": sha256_by_file,
        "download_method": download_method,
    }


def download_release_files(
    raw_dir: Path,
    source_paths: list[str],
    *,
    checkout_commit: str | None = None,
) -> tuple[dict, dict[str, Path]]:
    repo_dir, source_commit, source_branch_at_download = clone_repo(checkout_commit=checkout_commit)
    try:
        copied_files = copy_source_files(repo_dir, source_paths, raw_dir)
        meta = build_download_meta(
            source_commit=source_commit,
            source_branch_at_download=source_branch_at_download,
            source_paths=source_paths,
            copied_files=copied_files,
            download_method="git_clone_copy",
        )
        return meta, copied_files
    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)


def write_download_meta(path: Path, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
