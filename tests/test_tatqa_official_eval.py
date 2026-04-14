import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_tatqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from wrap_official_tatqa_eval import (  # noqa: E402
    OfficialTATQAMetric,
    processed_row_to_official_ground_truth,
    score_prediction,
    to_official_prediction_dict,
)


class TatqaOfficialEvalTests(unittest.TestCase):
    def test_prediction_wrapper_formats_official_dict(self):
        formatted = to_official_prediction_dict({"q1": {"answer": 17.7, "scale": "percent"}})
        self.assertEqual(formatted, {"q1": [17.7, "percent"]})

    def test_span_example_scores_perfectly(self):
        gold = {"uid": "q1", "answer": ["the modified retrospective method"], "answer_type": "span", "answer_from": "text", "scale": ""}
        score = score_prediction(gold, ["the modified retrospective method"], "")
        self.assertEqual(score["exact_match"], 1.0)
        self.assertEqual(score["f1"], 1.0)
        self.assertEqual(score["scale_score"], 1.0)

    def test_percent_normalization_matches_official_behavior(self):
        gold = {"uid": "q2", "answer": 23.42, "answer_type": "arithmetic", "answer_from": "table-text", "scale": "percent"}
        score = score_prediction(gold, 0.2342, "")
        self.assertEqual(score["exact_match"], 1.0)
        self.assertEqual(score["f1"], 1.0)
        self.assertEqual(score["scale_score"], 0.0)

    def test_empty_prediction_returns_zero(self):
        gold = {"uid": "q3", "answer": 3, "answer_type": "count", "answer_from": "table", "scale": ""}
        score = score_prediction(gold, None, "")
        self.assertEqual(score["exact_match"], 0.0)
        self.assertEqual(score["f1"], 0.0)

    def test_metric_aggregates_processed_row_ground_truth(self):
        row = {
            "example_id": "q4",
            "gold_answer": 5,
            "gold_answer_type_raw": "count",
            "gold_answer_from": "table",
            "gold_scale": ""
        }
        metric = OfficialTATQAMetric()
        metric.add(processed_row_to_official_ground_truth(row), 5, "")
        overall = metric.get_overall_metric()
        self.assertEqual(overall["exact_match"], 1.0)
        self.assertEqual(overall["f1"], 1.0)
        self.assertEqual(overall["scale_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
