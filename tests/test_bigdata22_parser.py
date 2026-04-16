import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_forecast_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from parse_binary_direction import normalize_binary_direction, parse_label_prediction  # noqa: E402


class BigData22ParserTests(unittest.TestCase):
    def test_normalize_binary_direction(self):
        self.assertEqual(normalize_binary_direction("Rise"), "Rise")
        self.assertEqual(normalize_binary_direction(" fall "), "Fall")
        self.assertIsNone(normalize_binary_direction("Flat"))

    def test_parse_label_prediction_accepts_valid_json(self):
        pred = parse_label_prediction('{"label":"Rise"}')
        self.assertEqual(pred["label"], "Rise")

    def test_parse_label_prediction_rejects_invalid_label(self):
        self.assertIsNone(parse_label_prediction('{"label":"Flat"}'))
        self.assertIsNone(parse_label_prediction('{"answer":"Rise"}'))


if __name__ == "__main__":
    unittest.main()
