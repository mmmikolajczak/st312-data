import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "ectsum_bullet_summarization_v0"
if str(TASK_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_DIR))

from eval_ectsum_cached import build_sanity_predictions, evaluate  # noqa: E402


class EctsumEvalTests(unittest.TestCase):
    def test_default_eval_variant_is_original_paper(self):
        spec = json.loads((REPO_ROOT / "tasks" / "ectsum_bullet_summarization_v0" / "task_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["default_eval_variant"], "ectsum_original")
        self.assertIn("finben_summary", spec["optional_eval_variants"])

    def test_request_builder_shape(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test_requests.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "tasks" / "ectsum_bullet_summarization_v0" / "build_ectsum_requests.py"),
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
            self.assertEqual(row["task_id"], "TA_SUM_ECTSUM_v0")
            self.assertIn("reference_summary", row)

    def test_original_variant_evaluator_shape(self):
        split_path = REPO_ROOT / "data" / "ectsum_official" / "processed" / "test.jsonl"
        with tempfile.TemporaryDirectory() as tmpdir:
            preds_path = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            build_sanity_predictions(split_path, preds_path, limit=2)
            with mock.patch(
                "eval_ectsum_cached.compute_rouge_bertscore",
                return_value={"rouge1": 1.0, "rouge2": 1.0, "rougeL": 1.0, "bertscore_precision": 1.0, "bertscore_recall": 1.0, "bertscore_f1": 1.0},
            ), mock.patch("eval_ectsum_cached.compute_summacconv", return_value={"summacconv": 1.0}):
                report = evaluate("test", "ectsum_original", preds_path, report_path)
            self.assertIn("summacconv", report)
            self.assertIn("num_prec", report)

    def test_finben_variant_evaluator_shape(self):
        split_path = REPO_ROOT / "data" / "ectsum_official" / "processed" / "test.jsonl"
        with tempfile.TemporaryDirectory() as tmpdir:
            preds_path = Path(tmpdir) / "preds.jsonl"
            report_path = Path(tmpdir) / "report.json"
            build_sanity_predictions(split_path, preds_path, limit=2)
            with mock.patch(
                "eval_ectsum_cached.compute_rouge_bertscore",
                return_value={"rouge1": 1.0, "rouge2": 1.0, "rougeL": 1.0, "bertscore_precision": 1.0, "bertscore_recall": 1.0, "bertscore_f1": 1.0},
            ), mock.patch("eval_ectsum_cached.compute_bartscore", return_value={"bartscore": 1.0}):
                report = evaluate("test", "finben_summary", preds_path, report_path)
            self.assertIn("bartscore", report)


if __name__ == "__main__":
    unittest.main()
