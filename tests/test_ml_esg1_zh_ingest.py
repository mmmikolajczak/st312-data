import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_SHARED = REPO_ROOT / "scripts" / "datasets" / "_ml_esg_shared"
if str(DATASET_SHARED) not in sys.path:
    sys.path.insert(0, str(DATASET_SHARED))

from audit_dynamic_esg_release import build_ingest_audit  # noqa: E402
from download_dynamic_esg_release import build_download_meta  # noqa: E402
from validate_dynamic_esg_release import (  # noqa: E402
    build_processed_row,
    validate_and_build_rows,
)


class MlEsgZhIngestTests(unittest.TestCase):
    def test_download_meta_construction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir)
            source_paths = ["data/ML-ESG-1_Chinese/Train.json"]
            copied_path = raw_dir / "Train.json"
            copied_path.write_text("[]", encoding="utf-8")
            meta = build_download_meta(
                source_commit="abc123",
                source_branch_at_download="master",
                source_paths=source_paths,
                copied_files={source_paths[0]: copied_path},
                download_method="git_clone_copy",
            )
            self.assertEqual(meta["source_repo"], "ymntseng/DynamicESG")
            self.assertEqual(meta["source_commit"], "abc123")
            self.assertIn("raw.githubusercontent.com", meta["source_raw_urls"][source_paths[0]])

    def test_processed_row_is_deterministic(self):
        row = {
            "pk": 675,
            "URL": "https://example.com/item",
            "News_Headline": "Headline",
            "ESG_Category": ["S13", "E01", "E01"],
        }
        processed = build_processed_row(
            dataset_id="ml_esg1_zh_official_v0",
            split="train",
            source_repo="ymntseng/DynamicESG",
            source_commit="commitsha",
            source_path="data/ML-ESG-1_Chinese/Train.json",
            row=row,
        )
        self.assertEqual(processed["article_id"], "dynamicesg_bt_675")
        self.assertEqual(processed["example_id"], "ml_esg1_zh_official_v0__train__dynamicesg_bt_675")
        self.assertEqual(processed["labels"], ["E01", "S13"])
        self.assertEqual(processed["text"], "Headline")

    def test_duplicate_article_id_detection(self):
        rows = [
            {"pk": 1, "URL": "https://a", "News_Headline": "h1", "ESG_Category": ["E01"]},
            {"pk": 1, "URL": "https://b", "News_Headline": "h2", "ESG_Category": ["S13"]},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate article_id"):
            validate_and_build_rows(
                dataset_id="ml_esg1_zh_official_v0",
                split="train",
                source_repo="ymntseng/DynamicESG",
                source_commit="commitsha",
                source_path="data/ML-ESG-1_Chinese/Train.json",
                rows=rows,
            )

    def test_audit_reports_cross_split_overlap(self):
        processed_train = [
            {
                "example_id": "a",
                "article_id": "dynamicesg_bt_1",
                "split": "train",
                "headline": "Headline 1",
                "url": "https://one",
                "labels": ["E01"],
                "label_count": 1,
            }
        ]
        processed_test = [
            {
                "example_id": "b",
                "article_id": "dynamicesg_bt_1",
                "split": "test",
                "headline": "Headline 1",
                "url": "https://one",
                "labels": ["E01", "S13"],
                "label_count": 2,
            }
        ]
        audit = build_ingest_audit(
            {"train": processed_train, "test": processed_test},
            {
                "train": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "ESG_Category": 0}},
                "test": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "ESG_Category": 0}},
            },
        )
        self.assertEqual(audit["cross_split_duplicate_article_ids"]["train__test"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
