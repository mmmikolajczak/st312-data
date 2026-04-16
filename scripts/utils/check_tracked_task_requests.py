from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(".")


def main() -> None:
    result = subprocess.run(
        ["git", "ls-files", "tasks/*/requests/*.jsonl"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    print("=" * 88)
    print("ST312 tracked task-request artifact check")
    print("=" * 88)

    if tracked:
        print(f"[ERROR] Found {len(tracked)} tracked request artifact(s) under tasks/*/requests/:")
        for path in tracked:
            print(f"  - {path}")
        print("-" * 88)
        print("Result: FAIL")
        print("=" * 88)
        sys.exit(1)

    print("[OK] No tracked task request JSONL artifacts found.")
    print("-" * 88)
    print("Result: PASS")
    print("=" * 88)


if __name__ == "__main__":
    main()
