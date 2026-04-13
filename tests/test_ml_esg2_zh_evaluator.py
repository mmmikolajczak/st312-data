import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from multiclass_metrics import compute_multiclass_metrics  # noqa: E402


class MlEsg2ZhEvaluatorTests(unittest.TestCase):
    def test_metrics_are_correct_on_toy_case(self):
        labels = ["Opportunity", "Risk", "CannotDistinguish"]
        gold = ["Opportunity", "Risk", "CannotDistinguish"]
        pred = ["Opportunity", None, "CannotDistinguish"]
        metrics = compute_multiclass_metrics(gold, pred, labels)
        self.assertAlmostEqual(metrics["accuracy"], 2 / 3)
        self.assertAlmostEqual(metrics["weighted_f1"], 2 / 3)
        self.assertIn("Risk -> INVALID_OR_MISSING", metrics["confusion_counts"])


if __name__ == "__main__":
    unittest.main()
