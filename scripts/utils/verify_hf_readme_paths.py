from __future__ import annotations

import argparse
import re
from pathlib import Path

from huggingface_hub import HfApi


PATH_RE = re.compile(r"`((?:datasets|tasks|reports|manifests)/[^`]+)`")


def extract_section_paths(readme_text: str, heading: str) -> list[str]:
    lines = readme_text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx + 1
            break
    if start is None:
        raise ValueError(f"Section heading not found: {heading}")

    end = len(lines)
    for idx in range(start, len(lines)):
        if idx > start and lines[idx].startswith("### "):
            end = idx
            break

    section_text = "\n".join(lines[start:end])
    return PATH_RE.findall(section_text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--repo-type", default="dataset")
    ap.add_argument("--readme", default="manifests/hf_repo/README.md")
    ap.add_argument("--section-heading", required=True)
    args = ap.parse_args()

    readme_path = Path(args.readme)
    readme_text = readme_path.read_text(encoding="utf-8")
    expected_paths = extract_section_paths(readme_text, args.section_heading)
    if not expected_paths:
        raise SystemExit(f"No artifact paths found under section: {args.section_heading}")

    api = HfApi()
    published_paths = set(api.list_repo_files(repo_id=args.repo_id, repo_type=args.repo_type))
    missing_paths = [path for path in expected_paths if path not in published_paths]

    if missing_paths:
        raise SystemExit(
            "[FAIL] Missing published HF paths for section "
            f"{args.section_heading}: {', '.join(missing_paths)}"
        )

    print(f"[OK] Verified {len(expected_paths)} HF paths for {args.section_heading}")
    for path in expected_paths:
        print(path)


if __name__ == "__main__":
    main()
