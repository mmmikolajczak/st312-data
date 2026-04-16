import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = REPO_ROOT / "scripts" / "tasks" / "ectsum_bullet_summarization_v0"
if str(TASK_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_DIR))
SHARED_DIR = REPO_ROOT / "scripts" / "tasks" / "_summ_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from eval_ectsum_cached import build_sanity_predictions, evaluate  # noqa: E402
from compute_num_prec import compute_num_prec  # noqa: E402
from run_rouge_bertscore import compute_rouge_bertscore  # noqa: E402


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

    def test_live_rouge_bertscore_wrapper_on_identical_pair(self):
        metrics = compute_rouge_bertscore(
            ["Revenue rose 10% year over year."],
            ["Revenue rose 10% year over year."],
            bertscore_model="bert-base-uncased",
        )
        self.assertEqual(metrics["rouge1"], 1.0)
        self.assertEqual(metrics["rouge2"], 1.0)
        self.assertEqual(metrics["rougeL"], 1.0)
        self.assertGreater(metrics["bertscore_f1"], 0.99)

    def test_num_prec_uses_source_only_values(self):
        source_lines = ["Revenue increased to 10 million dollars in 2024."]
        reference_bullets = ["Revenue reached 12 million dollars."]
        predicted_summary = "- Revenue was 10 million.\n- Outlook is 12 million."
        self.assertTrue(math.isclose(compute_num_prec(source_lines, reference_bullets, predicted_summary), 0.5))

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
