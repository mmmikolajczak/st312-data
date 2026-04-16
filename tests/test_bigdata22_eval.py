import json
import math
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "bigdata22_stock_movement_v0"
if str(TASK_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_DIR))

from eval_bigdata22_cached import build_sanity_predictions, compute_accuracy, compute_mcc, evaluate  # noqa: E402


REQUEST_SCRIPT = REPO_ROOT / "scripts" / "tasks" / "bigdata22_stock_movement_v0" / "build_bigdata22_requests.py"


class BigData22EvalTests(unittest.TestCase):
    def test_request_builder_emits_canonical_rows(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test_requests.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    str(REQUEST_SCRIPT),
                    "--split",
                    "test",
                    "--limit",
                    "1",
                    "--include-gold",
                    "--out",
                    str(out_path),
                ],
                check=True,
                cwd=REPO_ROOT,
            )
            row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["task_id"], "TA_FORECAST_BIGDATA22_v0")
            self.assertIn("gold_label_text", row)
            self.assertEqual(len(row["messages"]), 2)

    def test_compute_binary_metrics(self):
        y_true = [1, 1, 0, 0]
        y_pred = [1, 0, 0, 0]
        self.assertTrue(math.isclose(compute_accuracy(y_true, y_pred), 0.75))
        self.assertTrue(math.isclose(compute_mcc(y_true, y_pred), 0.5773502691896258))

    def test_sanity_predictions_and_eval(self):
        split_path = REPO_ROOT / "data" / "bigdata22_official" / "processed" / "test.jsonl"
        with tempfile.TemporaryDirectory() as tmpdir:
            preds_path = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            gold_rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines()]
            rise_row = next(row for row in gold_rows if row["gold_label_text"] == "Rise")
            fall_row = next(row for row in gold_rows if row["gold_label_text"] == "Fall")
            preds_path.write_text(
                "\n".join(
                    json.dumps(
                        {"example_id": row["example_id"], "output_text": json.dumps({"label": row["gold_label_text"]})},
                        ensure_ascii=False,
                    )
                    for row in [rise_row, fall_row]
                )
                + "\n",
                encoding="utf-8",
            )
            report = evaluate("test", preds_path, report_path)
            self.assertEqual(report["accuracy"], 1.0)
            self.assertEqual(report["mcc"], 1.0)
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()
