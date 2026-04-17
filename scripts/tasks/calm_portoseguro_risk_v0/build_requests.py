from __future__ import annotations

import argparse
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/calm_portoseguro_risk_v0/task_spec.json")
SHARED_DIR = Path(__file__).resolve().parents[1] / "_calm_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from calm_binary_wrapper import build_requests  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["test"], default="test")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    build_requests(TASK_SPEC_PATH, args.split, out=args.out, limit=args.limit, include_gold=args.include_gold)


if __name__ == "__main__":
    main()
