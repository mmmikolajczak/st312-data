import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_convfinqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_convfinqa_program import parse_program_prediction, validate_program_tokens  # noqa: E402


class ConvFinqaParserTests(unittest.TestCase):
    def test_parser_accepts_valid_json(self):
        pred = parse_program_prediction('{"program_tokens":["subtract(","5829","5735",")","EOF"]}')
        self.assertEqual(pred, ["subtract(", "5829", "5735", ")", "EOF"])

    def test_parser_accepts_single_number_program(self):
        pred = parse_program_prediction('{"program_tokens":["206588","EOF"]}')
        self.assertEqual(pred, ["206588", "EOF"])

    def test_parser_accepts_alias_key(self):
        pred = parse_program_prediction('Answer: {"predicted":["206588","EOF"]}')
        self.assertEqual(pred, ["206588", "EOF"])

    def test_validator_rejects_invalid_operation(self):
        valid, _ = validate_program_tokens(["sum(", "1", "2", ")", "EOF"])
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
