import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "ml_esg3_zh_impact_duration_v0"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_ml_esg_shared"
for path in [TASK_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from normalize_labels import canonicalize_single_label  # noqa: E402
from reward_ml_esg3_zh_impact_duration import parse_prediction  # noqa: E402


class MlEsg3ZhParserTests(unittest.TestCase):
    def test_single_label_normalization(self):
        label = canonicalize_single_label(" >5 ", [">5", "2~5"])
        self.assertEqual(label, ">5")

    def test_parser_accepts_valid_json(self):
        pred = parse_prediction('{"impact_duration":"2~5"}')
        self.assertEqual(pred, "2~5")

    def test_parser_accepts_alias_key(self):
        pred = parse_prediction('Answer: {"duration":" >5 "}')
        self.assertEqual(pred, ">5")

    def test_parser_rejects_invalid_labels(self):
        self.assertIsNone(parse_prediction('{"impact_duration":"1~2"}'))

    def test_parser_rejects_malformed_json(self):
        self.assertIsNone(parse_prediction('{"impact_duration":"2~5"'))

    def test_parser_rejects_extra_keys(self):
        self.assertIsNone(parse_prediction('{"impact_duration":"2~5","extra":1}'))


if __name__ == "__main__":
    unittest.main()
