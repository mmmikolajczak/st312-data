import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "ml_esg1_zh_issue_v0"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_ml_esg_shared"
for path in [TASK_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from normalize_labels import canonicalize_label_list  # noqa: E402
from reward_ml_esg1_zh_issue import parse_prediction  # noqa: E402


class MlEsgZhParserTests(unittest.TestCase):
    def test_label_normalization(self):
        labels = canonicalize_label_list([" s13 ", "E01", "e01"], allowed_labels={"E01", "S13"})
        self.assertEqual(labels, ["E01", "S13"])

    def test_parser_accepts_valid_json(self):
        pred = parse_prediction('{"esg_categories":["s13","E01","E01"]}')
        self.assertEqual(pred, ["E01", "S13"])

    def test_parser_accepts_alias_key(self):
        pred = parse_prediction('Answer: {"labels":["E01"]}')
        self.assertEqual(pred, ["E01"])

    def test_parser_rejects_invalid_labels(self):
        self.assertIsNone(parse_prediction('{"esg_categories":["ZZ99"]}'))

    def test_parser_rejects_malformed_json(self):
        self.assertIsNone(parse_prediction('{"esg_categories":["E01"]'))

    def test_parser_rejects_extra_keys(self):
        self.assertIsNone(parse_prediction('{"esg_categories":["E01"],"extra":1}'))


if __name__ == "__main__":
    unittest.main()
