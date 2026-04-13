import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_finqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from execute_finqa_program import equal_program, eval_program, execution_matches_gold  # noqa: E402
from normalize_finqa_answer import normalize_finqa_answer  # noqa: E402


class FinqaExecutorTests(unittest.TestCase):
    def setUp(self):
        self.table = [
            ["metric", "2016", "2015"],
            ["revenue", "10", "5"],
            ["cost", "3", "2"],
        ]

    def test_all_operations_execute(self):
        cases = [
            (["add(", "1", "2", ")", "EOF"], 3.0),
            (["subtract(", "5", "2", ")", "EOF"], 3.0),
            (["multiply(", "3", "4", ")", "EOF"], 12.0),
            (["divide(", "8", "2", ")", "EOF"], 4.0),
            (["greater(", "8", "2", ")", "EOF"], "yes"),
            (["exp(", "2", "3", ")", "EOF"], 8.0),
            (["table_max(", "revenue", "none", ")", "EOF"], 10.0),
            (["table_min(", "revenue", "none", ")", "EOF"], 5.0),
            (["table_sum(", "revenue", "none", ")", "EOF"], 15.0),
            (["table_average(", "revenue", "none", ")", "EOF"], 7.5),
        ]
        for program, expected in cases:
            invalid, result = eval_program(program, self.table)
            self.assertEqual(invalid, 0)
            self.assertEqual(result, expected)

    def test_answer_normalization(self):
        self.assertEqual(normalize_finqa_answer(127.40000), "127.4")
        self.assertEqual(normalize_finqa_answer("yes"), "yes")

    def test_execution_match_uses_canonical_normalization(self):
        program = ["divide(", "10", "4", ")", "EOF"]
        matches, invalid, result = execution_matches_gold(program, self.table, "2.5")
        self.assertEqual(invalid, 0)
        self.assertEqual(result, 2.5)
        self.assertTrue(matches)

    def test_symbolic_program_equivalence(self):
        gold = ["add(", "1", "2", ")", "EOF"]
        pred = ["add(", "2", "1", ")", "EOF"]
        self.assertTrue(equal_program(gold, pred))


if __name__ == "__main__":
    unittest.main()
