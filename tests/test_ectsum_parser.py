import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_summ_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from normalize_summary_text import normalize_summary_text, parse_summary_prediction  # noqa: E402


class EctsumParserTests(unittest.TestCase):
    def test_parser_accepts_valid_summary_json(self):
        parsed = parse_summary_prediction('{"summary":"- revenue rose\\n- margins improved"}')
        self.assertEqual(parsed["summary"], "- revenue rose\n- margins improved")
        self.assertTrue(parsed["_format_valid"])

    def test_parser_rejects_extra_keys(self):
        self.assertIsNone(parse_summary_prediction('{"summary":"x","extra":"y"}'))

    def test_normalizer_preserves_bullet_lines(self):
        self.assertEqual(normalize_summary_text(" - a  \n\n -  b "), "- a\n- b")


if __name__ == "__main__":
    unittest.main()
