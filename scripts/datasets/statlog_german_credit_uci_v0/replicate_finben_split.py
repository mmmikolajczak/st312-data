from __future__ import annotations

import argparse

from ingest import SPLIT_REPLICATION_AUDIT_PATH, run_pipeline


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-failure", action="store_true")
    args = ap.parse_args()

    result = run_pipeline(fail_on_split_mismatch=not args.allow_failure)
    split_audit = result["split_audit"]
    print(f"[DONE] Wrote split replication audit to {SPLIT_REPLICATION_AUDIT_PATH}")
    print(f"[INFO] replication_passed={split_audit['replication_passed']}")
    print(f"[INFO] matched_rows_total={split_audit['matched_rows_total']}")
    print(f"[INFO] assigned_split_counts={split_audit['assigned_split_counts']}")


if __name__ == "__main__":
    main()
