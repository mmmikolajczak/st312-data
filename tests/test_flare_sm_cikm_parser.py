import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_forecast_shared"
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "flare_sm_cikm_stock_movement_v0"
for path in [SHARED_DIR, TASK_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from extract_label_from_json_or_text import extract_label_from_json_or_text  # noqa: E402
from parse_binary_direction import parse_label_prediction  # noqa: E402
from reward_cikm18_finben import score_completion  # noqa: E402
from reward_cikm18_label import reward_breakdown  # noqa: E402


class FlareSmCikmParserTests(unittest.TestCase):
    def test_strict_json_parser_accepts_only_schema(self):
        self.assertEqual(parse_label_prediction('{"label":"Rise"}')["label"], "Rise")
        self.assertIsNone(parse_label_prediction('{"label":"Rise","extra":1}'))
        self.assertIsNone(parse_label_prediction("Rise"))

    def test_lenient_extractor_supports_json_and_text(self):
        self.assertEqual(extract_label_from_json_or_text('{"label":"Fall"}')["label"], "Fall")
        self.assertEqual(extract_label_from_json_or_text("Prediction: Rise")["label"], "Rise")
        self.assertIsNone(extract_label_from_json_or_text("Rise or Fall"))

    def test_default_reward_prefers_strict_json(self):
        good = reward_breakdown('{"label":"Rise"}', "Rise")
        extra = reward_breakdown('{"label":"Rise","x":1}', "Rise")
        self.assertEqual(good["total_reward"], 1.0)
        self.assertLess(extra["total_reward"], 1.0)

    def test_finben_reward_is_lenient(self):
        self.assertEqual(score_completion("Prediction: Fall", "Fall")["reward"], 1.0)
        self.assertEqual(score_completion("Rise or Fall", "Fall")["reward"], 0.0)


if __name__ == "__main__":
    unittest.main()
