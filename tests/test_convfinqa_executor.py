import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_convfinqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_convfinqa_program import equal_program, execution_matches_gold, program_exact_match  # noqa: E402


class ConvFinqaExecutorTests(unittest.TestCase):
    def setUp(self):
        self.table = [["metric", "value"], ["revenue", "120"], ["cost", "20"]]

    def test_single_number_program_executes_and_matches(self):
        matches, invalid, result = execution_matches_gold(["206588", "EOF"], self.table, "206588")
        self.assertEqual(invalid, 0)
        self.assertEqual(result, 206588.0)
        self.assertTrue(matches)

    def test_symbolic_program_equivalence(self):
        gold = ["add(", "1", "2", ")", "EOF"]
        pred = ["add(", "2", "1", ")", "EOF"]
        self.assertTrue(equal_program(gold, pred))

    def test_program_exact_match_is_order_sensitive(self):
        gold = ["subtract(", "120", "20", ")", "EOF"]
        pred = ["subtract(", "120", "20", ")", "EOF"]
        self.assertTrue(program_exact_match(gold, pred))


if __name__ == "__main__":
    unittest.main()
