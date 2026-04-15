import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "regulations_longform_qa_v0"
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_lfqa_shared"
for path in [TASK_DIR, SHARED_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from eval_regulations_cached import build_sanity_predictions, evaluate  # noqa: E402


REQUEST_SCRIPT = REPO_ROOT / "scripts" / "tasks" / "regulations_longform_qa_v0" / "build_regulations_requests.py"


class RegulationsEvalTests(unittest.TestCase):
    def test_request_builder_emits_canonical_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test_requests.jsonl"
            import subprocess

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
            self.assertIn("example_id", row)
            self.assertEqual(row["task_id"], "TA_LFQA_REGULATIONS_FINBEN_v0")
            self.assertEqual(len(row["messages"]), 2)
            self.assertIn("reference_answer", row)

    def test_sanity_predictions_emit_json_answer_rows(self):
        split_path = REPO_ROOT / "data" / "regulations_public_test" / "processed" / "test.jsonl"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "preds.jsonl"
            build_sanity_predictions(split_path, out_path, limit=2)
            rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertIn("example_id", rows[0])
            self.assertIn("output_text", rows[0])
            self.assertIn('"answer"', rows[0]["output_text"])

    def test_evaluate_reports_expected_fields(self):
        split_path = REPO_ROOT / "data" / "regulations_public_test" / "processed" / "test.jsonl"
        with tempfile.TemporaryDirectory() as tmpdir:
            preds_path = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            build_sanity_predictions(split_path, preds_path, limit=2)
            with mock.patch(
                "eval_regulations_cached.compute_rouge_bertscore",
                return_value={
                    "rouge1": 1.0,
                    "rouge2": 1.0,
                    "rougeL": 1.0,
                    "bertscore_precision": 1.0,
                    "bertscore_recall": 1.0,
                    "bertscore_f1": 1.0,
                },
            ):
                report = evaluate("test", preds_path, report_path)
            self.assertEqual(report["split"], "test")
            self.assertIn("rouge1", report)
            self.assertIn("bertscore_f1", report)
            self.assertGreater(report["format_valid_rate"], 0.0)
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()
