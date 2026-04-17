import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "flare_sm_cikm_stock_movement_v0"
if str(TASK_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_DIR))

from eval_flare_sm_cikm_cached import compute_accuracy, compute_mcc, evaluate  # noqa: E402


REQUEST_SCRIPT = REPO_ROOT / "scripts" / "tasks" / "flare_sm_cikm_stock_movement_v0" / "build_flare_sm_cikm_requests.py"


class FlareSmCikmEvalTests(unittest.TestCase):
    def test_request_builder_emits_expected_shape(self):
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
            self.assertEqual(row["task_id"], "TA_FORECAST_FLARE_SM_CIKM_v0")
            self.assertEqual(len(row["messages"]), 2)
            self.assertIn("gold_label_text", row)

    def test_metric_helpers(self):
        self.assertTrue(math.isclose(compute_accuracy([1, 0, 1], [1, 0, 0]), 2 / 3))
        self.assertTrue(math.isclose(compute_mcc([1, 1, 0, 0], [1, 0, 0, 0]), 0.5773502691896258))

    def test_default_variant_reports_accuracy(self):
        split_path = REPO_ROOT / "data" / "flare_sm_cikm_public" / "processed" / "test.jsonl"
        rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines()]
        sample = [rows[0], next(row for row in rows if row["gold_label_text"] != rows[0]["gold_label_text"])]
        with tempfile.TemporaryDirectory() as tmpdir:
            preds = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            preds.write_text(
                "\n".join(
                    json.dumps({"example_id": row["example_id"], "output_text": json.dumps({"label": row["gold_label_text"]})}, ensure_ascii=False)
                    for row in sample
                )
                + "\n",
                encoding="utf-8",
            )
            report = evaluate("test", "cikm18_original_like", preds, report_path)
            self.assertEqual(report["accuracy"], 1.0)
            self.assertNotIn("mcc", report)

    def test_finben_variant_reports_accuracy_and_mcc(self):
        split_path = REPO_ROOT / "data" / "flare_sm_cikm_public" / "processed" / "test.jsonl"
        rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines()]
        sample = [rows[0], next(row for row in rows if row["gold_label_text"] != rows[0]["gold_label_text"])]
        with tempfile.TemporaryDirectory() as tmpdir:
            preds = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            preds.write_text(
                "\n".join(
                    json.dumps({"example_id": row["example_id"], "output_text": row["gold_label_text"]}, ensure_ascii=False)
                    for row in sample
                )
                + "\n",
                encoding="utf-8",
            )
            report = evaluate("test", "finben_compatible", preds, report_path)
            self.assertEqual(report["accuracy"], 1.0)
            self.assertEqual(report["mcc"], 1.0)

    def test_task_spec_records_wrapper_based_provenance(self):
        spec = json.loads((REPO_ROOT / "tasks" / "flare_sm_cikm_stock_movement_v0" / "task_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["taxonomy"]["finben_supercategory"], "Forecasting")
        self.assertEqual(spec["taxonomy"]["finben_category"], "Stock Movement Prediction")
        self.assertEqual(spec["default_eval_variant"], "cikm18_original_like")
        self.assertEqual(spec["optional_eval_variants"], ["finben_compatible"])


if __name__ == "__main__":
    unittest.main()
