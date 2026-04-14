import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INGEST_DIR = REPO_ROOT / "scripts" / "datasets" / "tatqa_official"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_tatqa_shared"
for path in [INGEST_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ingest_tatqa_official import (  # noqa: E402
    CANONICAL_SPLIT_SOURCE_PATHS,
    ORIGINAL_TEST_SOURCE_PATH,
    normalize_answer_type,
    parse_rel_paragraph_orders,
    validate_question,
)
from serialize_tatqa_paragraphs import serialize_tatqa_paragraphs  # noqa: E402
from serialize_tatqa_table import serialize_tatqa_table  # noqa: E402


class TatqaIngestTests(unittest.TestCase):
    def test_table_serialization_is_deterministic(self):
        table = [["", "2019 %"], ["Rate of inflation", "2.9"]]
        self.assertEqual(serialize_tatqa_table(table), "\t2019 %\nRate of inflation\t2.9")

    def test_paragraph_serialization_is_deterministic(self):
        paragraphs = [{"uid": "p2", "order": 2, "text": "Second"}, {"uid": "p1", "order": 1, "text": "First"}]
        self.assertEqual(serialize_tatqa_paragraphs(paragraphs), "[P1] First\n\n[P2] Second")

    def test_answer_type_normalization(self):
        self.assertEqual(normalize_answer_type("counting"), "count")
        self.assertEqual(normalize_answer_type("multi-span"), "multi-span")

    def test_rel_paragraph_orders_are_parsed(self):
        self.assertEqual(parse_rel_paragraph_orders(["2", "x", 4]), [2, 4])

    def test_question_validation_and_flattening_fields(self):
        question = {
            "uid": "q1",
            "order": 3,
            "question": "How much?",
            "answer": 17.7,
            "derivation": "a-b",
            "answer_type": "arithmetic",
            "answer_from": "table-text",
            "rel_paragraphs": ["2"],
            "req_comparison": False,
            "scale": "percent",
        }
        normalized = validate_question(question, require_labels=True)
        self.assertEqual(normalized["uid"], "q1")
        self.assertEqual(normalized["answer_type_norm"], "arithmetic")
        self.assertEqual(normalized["rel_paragraph_orders"], [2])

    def test_canonical_test_source_uses_test_gold(self):
        self.assertEqual(CANONICAL_SPLIT_SOURCE_PATHS["test"], "dataset_raw/tatqa_dataset_test_gold.json")
        self.assertEqual(ORIGINAL_TEST_SOURCE_PATH, "dataset_raw/tatqa_dataset_test.json")

    def test_processed_rows_do_not_contain_tagop_side_fields(self):
        row = json.loads((REPO_ROOT / "data" / "tatqa_official" / "processed" / "test.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotIn("gold_facts_raw", row)
        self.assertNotIn("gold_consts_raw", row)
        self.assertNotIn("gold_mappings_raw", row)


if __name__ == "__main__":
    unittest.main()
