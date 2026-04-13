import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_finqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from parse_finqa_program import parse_program_prediction, tokenize_source_program, validate_program_tokens  # noqa: E402


class FinqaProgramParserTests(unittest.TestCase):
    def test_source_program_tokenization(self):
        self.assertEqual(
            tokenize_source_program("subtract(5829, 5735)"),
            ["subtract(", "5829", "5735", ")", "EOF"],
        )

    def test_parser_accepts_valid_json(self):
        pred = parse_program_prediction('{"program_tokens":["subtract(","5829","5735",")","EOF"]}')
        self.assertEqual(pred, ["subtract(", "5829", "5735", ")", "EOF"])

    def test_parser_accepts_alias_key(self):
        pred = parse_program_prediction('Answer: {"predicted":["table-average(","2016","none",")","EOF"]}')
        self.assertEqual(pred, ["table_average(", "2016", "none", ")", "EOF"])

    def test_validator_rejects_forward_reference(self):
        valid, _ = validate_program_tokens(["subtract(", "#0", "10", ")", "EOF"])
        self.assertFalse(valid)

    def test_validator_rejects_invalid_operation(self):
        valid, _ = validate_program_tokens(["sum(", "1", "2", ")", "EOF"])
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
