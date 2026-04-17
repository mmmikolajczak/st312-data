from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_calm_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from fineval_cra_ingest import run_ingest  # noqa: E402


def main() -> None:
    result = run_ingest("travelinsurance")
    print(f"[DONE] Reconstructed {result['config']['dataset_id']}")
    print(f"[INFO] split_summaries={result['split_summaries']}")
    print(f"[OUT]  data/{result['config']['data_slug']}/processed/test.jsonl")


if __name__ == "__main__":
    main()
