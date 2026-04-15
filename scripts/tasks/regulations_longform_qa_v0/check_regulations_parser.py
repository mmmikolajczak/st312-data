from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_lfqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_longform_answer import parse_answer_prediction  # noqa: E402


def run_smoke_test() -> None:
    cases = [
        ('{"answer":"EMIR sets reporting obligations."}', True),
        ('Result: {"answer":"Funds are generally the counterparties."}', True),
        ('{"answer":17}', False),
        ('{"answer":"x","extra":"y"}', False),
        ('not json', False),
    ]
    results = []
    for text, expected_valid in cases:
        parsed = parse_answer_prediction(text)
        actual_valid = parsed is not None
        results.append(
            {
                "input": text,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "parsed": parsed,
            }
        )
        if actual_valid != expected_valid:
            raise AssertionError(f"Unexpected parser result for input: {text}")

    print(json.dumps({"status": "ok", "cases": results}, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if not args.smoke_test:
        raise SystemExit("Use --smoke-test")
    run_smoke_test()


if __name__ == "__main__":
    main()
