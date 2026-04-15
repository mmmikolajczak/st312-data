import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INGEST_DIR = REPO_ROOT / "scripts" / "datasets" / "regulations_public_test"
if str(INGEST_DIR) not in sys.path:
    sys.path.insert(0, str(INGEST_DIR))

from ingest_regulations_public_test import (  # noqa: E402
    DATASET_ID,
    EXPECTED_VISIBLE_FILES,
    QUERY_PREFIX,
    build_processed_row,
)


class RegulationsIngestTests(unittest.TestCase):
    def test_processed_row_conversion_is_deterministic(self):
        row = {
            "id": "abc123",
            "query": f"{QUERY_PREFIX}What is EMIR?",
            "answer": "EMIR is the European Market Infrastructure Regulation.",
            "text": "What is EMIR?",
        }
        processed = build_processed_row("rev123", "test_regulations.json", row)
        self.assertEqual(processed["example_id"], "abc123")
        self.assertEqual(processed["dataset_id"], DATASET_ID)
        self.assertEqual(processed["split"], "test")
        self.assertEqual(processed["question"], "What is EMIR?")
        self.assertEqual(processed["reference_answer"], "EMIR is the European Market Infrastructure Regulation.")
        self.assertEqual(processed["source_query"], row["query"])
        self.assertEqual(processed["regulation_family"], "EMIR")
        self.assertIsNone(processed["context"])

    def test_processed_row_requires_non_empty_string_fields(self):
        with self.assertRaises(ValueError):
            build_processed_row("rev123", "test_regulations.json", {"id": "x", "query": " ", "answer": "a", "text": "q"})

    def test_download_meta_has_only_expected_visible_files(self):
        meta = json.loads((REPO_ROOT / "data" / "regulations_public_test" / "raw" / "download_meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["source_paths"], EXPECTED_VISIBLE_FILES)
        self.assertTrue(meta["gated_access"])
        self.assertEqual(sorted(meta["source_display_urls"].keys()), sorted(EXPECTED_VISIBLE_FILES))
        self.assertEqual(sorted(meta["source_raw_urls"].keys()), sorted(EXPECTED_VISIBLE_FILES))

    def test_module_publishes_test_only(self):
        spec = json.loads((REPO_ROOT / "datasets" / "regulations_public_test_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["split_policy"]["release_split"], "test")
        self.assertEqual(sorted(spec["processed"]["files"]), ["ingest_summary", "test"])


if __name__ == "__main__":
    unittest.main()
