import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_ml_esg_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from multilabel_metrics import compute_multilabel_metrics, label_set_f1  # noqa: E402


class MlEsgZhEvaluatorTests(unittest.TestCase):
    def test_example_f1_is_order_invariant(self):
        self.assertEqual(label_set_f1(["E01", "S13"], ["S13", "E01"]), 1.0)

    def test_metrics_are_correct_on_toy_case(self):
        labels = ["E01", "S13"]
        gold = [["E01", "S13"], ["E01"]]
        pred = [["S13", "E01"], []]
        metrics = compute_multilabel_metrics(gold, pred, labels)
        self.assertAlmostEqual(metrics["subset_accuracy"], 0.5)
        self.assertAlmostEqual(metrics["example_f1_mean"], 0.5)
        self.assertAlmostEqual(metrics["avg_predicted_label_count"], 1.0)
        self.assertAlmostEqual(metrics["avg_gold_label_count"], 1.5)
        self.assertAlmostEqual(metrics["micro_f1"], 0.8)


if __name__ == "__main__":
    unittest.main()
