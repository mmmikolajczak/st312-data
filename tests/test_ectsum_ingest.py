import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INGEST_DIR = REPO_ROOT / "scripts" / "datasets" / "ectsum_official"
if str(INGEST_DIR) not in sys.path:
    sys.path.insert(0, str(INGEST_DIR))

from ingest_ectsum_official import DATASET_ID, SOURCE_COMMIT, build_processed_row  # noqa: E402


class EctsumIngestTests(unittest.TestCase):
    def test_processed_row_conversion_preserves_bullets(self):
        row = build_processed_row(
            "test",
            "ABC_q1_2021.txt",
            ["Revenue rose 10%.", "Margins improved."],
            ["revenue rose 10 percent.", "margins improved."],
        )
        self.assertEqual(row["example_id"], f"{DATASET_ID}__test__ABC_q1_2021")
        self.assertEqual(row["source_commit"], SOURCE_COMMIT)
        self.assertEqual(row["reference_bullets"], ["revenue rose 10 percent.", "margins improved."])
        self.assertEqual(row["source_section"], "prepared_remarks")

    def test_private_scope_metadata_present(self):
        spec = json.loads((REPO_ROOT / "datasets" / "ectsum_official_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertFalse(spec["hf_publish"]["public_release_cleared"])
        self.assertIn("private", spec["hf_publish"]["release_scope"])

    def test_paired_filename_counts_match_processed_release(self):
        summary = json.loads((REPO_ROOT / "data" / "ectsum_official" / "processed" / "ingest_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["row_counts"], {"train": 1681, "val": 249, "test": 495})


if __name__ == "__main__":
    unittest.main()
