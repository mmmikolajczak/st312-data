import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "tatqa_hybrid_qa_structured_v0"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_tatqa_shared"
for path in [TASK_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reward_tatqa_structured import reward_breakdown  # noqa: E402


class TatqaRewardTests(unittest.TestCase):
    def setUp(self):
        self.gold = {
            "example_id": "q1",
            "gold_answer": 17.7,
            "gold_scale": "percent",
            "gold_derivation": "(16.6/93.8 ) * 100",
            "gold_answer_type_raw": "arithmetic",
            "gold_answer_type_norm": "arithmetic",
            "gold_answer_from": "table-text",
            "gold_rel_paragraphs_raw": ["3"],
            "gold_req_comparison": False
        }

    def test_reward_breakdown_prefers_correct_answer_and_scale(self):
        pred = json.dumps(
            {
                "answer": 17.7,
                "scale": "percent",
                "derivation": "(16.6/93.8 ) * 100",
                "answer_type": "arithmetic",
                "answer_from": "table-text",
                "rel_paragraphs": ["3"],
                "req_comparison": False,
            }
        )
        breakdown = reward_breakdown(pred, self.gold)
        self.assertEqual(breakdown["official_exact_match"], 1.0)
        self.assertGreaterEqual(breakdown["total_reward"], 3.5)

    def test_invalid_json_gets_zero_format_reward(self):
        breakdown = reward_breakdown("not json", self.gold)
        self.assertEqual(breakdown["format_reward"], 0.0)
        self.assertEqual(breakdown["official_answer_reward"], 0.0)


if __name__ == "__main__":
    unittest.main()
