from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


EXPECTED = {
    "Headline_Trainingdata.json": {
        "rows": 1142,
        "required_keys": {"id", "company", "title", "sentiment"},
    },
    "Headline_Trialdata.json": {
        "rows": 14,
        "required_keys": {"id", "company", "title", "sentiment"},
    },
    "Headlines_Testdata.json": {
        "rows": 491,
        "required_keys": {"id", "company", "title"},
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(path: Path, expected_rows: int, required_keys: set[str]) -> None:
    data = load_json(path)

    if not isinstance(data, list):
        raise ValueError(f"{path.name}: expected top-level list, got {type(data).__name__}")

    if len(data) != expected_rows:
        raise ValueError(f"{path.name}: expected {expected_rows} rows, found {len(data)}")

    if not data:
        raise ValueError(f"{path.name}: file is empty")

    first = data[0]
    if not isinstance(first, dict):
        raise ValueError(f"{path.name}: expected dict rows, got {type(first).__name__}")

    missing = required_keys - set(first.keys())
    if missing:
        raise ValueError(f"{path.name}: missing required keys {sorted(missing)}")

    for i, row in enumerate(data[:10]):
        if not isinstance(row.get("id"), int):
            raise ValueError(f"{path.name}: row {i} has non-int id: {row.get('id')!r}")
        if not isinstance(row.get("company"), str):
            raise ValueError(f"{path.name}: row {i} has non-str company: {row.get('company')!r}")
        if not isinstance(row.get("title"), str):
            raise ValueError(f"{path.name}: row {i} has non-str title: {row.get('title')!r}")

        if "sentiment" in required_keys:
            s = row.get("sentiment")
            if not isinstance(s, (int, float)):
                raise ValueError(f"{path.name}: row {i} has non-numeric sentiment: {s!r}")
            if not (-1.0 <= float(s) <= 1.0):
                raise ValueError(f"{path.name}: row {i} sentiment out of range [-1,1]: {s!r}")

    print(f"[ok] {path.name}: rows={len(data)} sha256={sha256(path)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("semeval-2017-task-5-subtask-2"),
        help="Directory containing the official SemEval raw JSON files.",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=Path("data/cortis2017_tsa/raw"),
        help="Destination raw-data directory in the repo.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files into dest-dir after validation.",
    )
    args = parser.parse_args()

    source_dir = args.source_dir
    dest_dir = args.dest_dir

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    for filename, spec in EXPECTED.items():
        src = source_dir / filename
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")

        validate_file(
            path=src,
            expected_rows=spec["rows"],
            required_keys=spec["required_keys"],
        )

        if args.copy:
            dst = dest_dir / filename
            shutil.copy2(src, dst)
            print(f"[copied] {src} -> {dst}")

    print("[done] official TSA raw files validated.")


if __name__ == "__main__":
    main()
