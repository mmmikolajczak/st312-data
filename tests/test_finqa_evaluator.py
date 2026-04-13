import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "finqa_program_generation_v0"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_finqa_shared"
for path in [TASK_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from eval_finqa_cached import load_predictions  # noqa: E402


class FinqaEvaluatorTests(unittest.TestCase):
    def test_official_prediction_format_is_loaded(self):
        payload = [
            {
                "id": "ETR/2016/page_23.pdf-2",
                "predicted": ["subtract(", "5829", "5735", ")", "EOF"],
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "predictions.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            pred_by_id, fmt = load_predictions(path)
            self.assertEqual(fmt, "official_prediction_json")
            self.assertEqual(pred_by_id["ETR/2016/page_23.pdf-2"], payload[0]["predicted"])


if __name__ == "__main__":
    unittest.main()
