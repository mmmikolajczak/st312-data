import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_lfqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_longform_answer import normalize_answer_text, parse_answer_prediction  # noqa: E402


class RegulationsParserTests(unittest.TestCase):
    def test_parser_accepts_valid_json(self):
        parsed = parse_answer_prediction('{"answer":"The obligation applies to counterparties."}')
        self.assertEqual(parsed["answer"], "The obligation applies to counterparties.")
        self.assertEqual(parsed["normalized_answer"], "The obligation applies to counterparties.")
        self.assertTrue(parsed["_format_valid"])

    def test_parser_rejects_extra_keys(self):
        self.assertIsNone(parse_answer_prediction('{"answer":"x","reason":"y"}'))

    def test_parser_rejects_non_string_answer(self):
        self.assertIsNone(parse_answer_prediction('{"answer":17}'))

    def test_parser_extracts_embedded_json_object(self):
        parsed = parse_answer_prediction('Answer: {"answer":"EMIR covers derivatives reporting."}')
        self.assertEqual(parsed["answer"], "EMIR covers derivatives reporting.")

    def test_normalizer_collapses_whitespace(self):
        self.assertEqual(normalize_answer_text("  A   B\nC  "), "A B C")


if __name__ == "__main__":
    unittest.main()
