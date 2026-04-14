import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_tatqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_tatqa_prediction import parse_prediction_text  # noqa: E402


class TatqaParserTests(unittest.TestCase):
    def test_parser_accepts_valid_json(self):
        pred = parse_prediction_text(
            '{"answer":17.7,"scale":"percent","derivation":"x","answer_type":"arithmetic","answer_from":"table-text","rel_paragraphs":["2"],"req_comparison":false}'
        )
        self.assertEqual(pred["scale"], "percent")
        self.assertEqual(pred["answer_type"], "arithmetic")

    def test_parser_normalizes_aliases(self):
        pred = parse_prediction_text(
            'Answer: {"answer":["A","B"],"scale":"","derivation":"","answer_type":"spans","answer_from":"text","rel_paragraphs":[2],"req_comparison":false}'
        )
        self.assertEqual(pred["answer_type"], "multi-span")
        self.assertEqual(pred["rel_paragraphs"], ["2"])

    def test_parser_rejects_extra_keys(self):
        pred = parse_prediction_text(
            '{"answer":1,"scale":"","derivation":"","answer_type":"count","answer_from":"table","rel_paragraphs":[],"req_comparison":false,"note":"x"}'
        )
        self.assertIsNone(pred)

    def test_parser_rejects_invalid_scale(self):
        pred = parse_prediction_text(
            '{"answer":1,"scale":"trillion","derivation":"","answer_type":"count","answer_from":"table","rel_paragraphs":[],"req_comparison":false}'
        )
        self.assertIsNone(pred)


if __name__ == "__main__":
    unittest.main()
