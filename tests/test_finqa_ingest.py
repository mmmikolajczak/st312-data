import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INGEST_DIR = REPO_ROOT / "scripts" / "datasets" / "finqa_official"
TASK_SHARED = REPO_ROOT / "scripts" / "tasks" / "_finqa_shared"
for path in [INGEST_DIR, TASK_SHARED]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ingest_finqa_official import (  # noqa: E402
    PRIVATE_TEST_PATH,
    PRIVATE_TEST_SUMMARY_PATH,
    PUBLIC_SPLIT_PATHS,
    build_processed_row,
    derive_report_page_id,
    validate_public_splits,
)
from serialize_finqa_table import serialize_finqa_table  # noqa: E402


class FinqaIngestTests(unittest.TestCase):
    def test_report_page_id_derivation(self):
        self.assertEqual(derive_report_page_id("ADI/2009/page_49.pdf-1"), "ADI/2009/page_49.pdf")

    def test_table_serialization_is_deterministic(self):
        table = [["", "2019"], ["revenue", "$ 10"]]
        self.assertEqual(serialize_finqa_table(table), "\t2019\nrevenue\t$ 10")

    def test_processed_row_normalization(self):
        row = {
            "id": "ADI/2009/page_49.pdf-1",
            "filename": "ADI/2009/page_49.pdf",
            "pre_text": ["line 1"],
            "post_text": ["line 2"],
            "table": [["metric", "value"], ["revenue", "$ 10"]],
            "qa": {
                "question": "what is revenue?",
                "program": "divide(10, const_2)",
                "gold_inds": {"table_1": "revenue row"},
                "exe_ans": 5.0,
                "program_re": "divide(10, const_2)",
                "answer": "5",
            },
        }
        processed = build_processed_row("train", "commitsha", "dataset/train.json", row)
        self.assertEqual(processed["report_page_id"], "ADI/2009/page_49.pdf")
        self.assertEqual(processed["gold_program_tokens"], ["divide(", "10", "const_2", ")", "EOF"])
        self.assertEqual(processed["gold_execution_answer"], "5")

    def test_split_level_report_page_non_overlap_validation(self):
        processed_by_split = {
            "train": [{"example_id": "a-1", "report_page_id": "rep1"}],
            "dev": [{"example_id": "b-1", "report_page_id": "rep1"}],
        }
        with self.assertRaisesRegex(ValueError, "report/page overlap"):
            validate_public_splits(processed_by_split)

    def test_private_test_is_not_a_public_split(self):
        self.assertNotIn(PRIVATE_TEST_PATH, PUBLIC_SPLIT_PATHS.values())

    def test_private_test_summary_artifact_exists_and_is_not_supervised(self):
        summary = json.loads(PRIVATE_TEST_SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(summary["split"], "private_test")
        self.assertTrue(summary["no_references"])
        self.assertFalse(summary["published_in_supervised_canonical_dataset"])


if __name__ == "__main__":
    unittest.main()
