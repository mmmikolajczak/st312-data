import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_SHARED = REPO_ROOT / "scripts" / "datasets" / "_ml_esg_shared"
if str(DATASET_SHARED) not in sys.path:
    sys.path.insert(0, str(DATASET_SHARED))

from audit_dynamic_esg_release import build_single_label_ingest_audit  # noqa: E402
from validate_dynamic_esg_release import (  # noqa: E402
    build_processed_single_label_row,
    validate_and_build_single_label_rows,
)


class MlEsg2ZhIngestTests(unittest.TestCase):
    def test_singleton_impact_type_normalization(self):
        row = {
            "pk": 2236,
            "URL": "https://example.com/item",
            "News_Headline": "Headline",
            "Impact_Type": [" Opportunity "],
        }
        processed = build_processed_single_label_row(
            dataset_id="ml_esg2_zh_official_v0",
            split="dev",
            source_repo="ymntseng/DynamicESG",
            source_commit="commitsha",
            source_path="data/ML-ESG-2_Chinese/Dev.json",
            row=row,
        )
        self.assertEqual(processed["article_id"], "dynamicesg_bt_2236")
        self.assertEqual(processed["example_id"], "ml_esg2_zh_official_v0__dev__dynamicesg_bt_2236")
        self.assertEqual(processed["impact_type"], "Opportunity")
        self.assertEqual(processed["source_impact_type_list"], [" Opportunity "])

    def test_duplicate_article_id_detection(self):
        rows = [
            {"pk": 1, "URL": "https://a", "News_Headline": "h1", "Impact_Type": ["Opportunity"]},
            {"pk": 1, "URL": "https://b", "News_Headline": "h2", "Impact_Type": ["Risk"]},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate article_id"):
            validate_and_build_single_label_rows(
                dataset_id="ml_esg2_zh_official_v0",
                split="train",
                source_repo="ymntseng/DynamicESG",
                source_commit="commitsha",
                source_path="data/ML-ESG-2_Chinese/Train.json",
                rows=rows,
            )

    def test_rejects_non_singleton_impact_list(self):
        rows = [
            {"pk": 1, "URL": "https://a", "News_Headline": "h1", "Impact_Type": ["Opportunity", "Risk"]},
        ]
        with self.assertRaisesRegex(ValueError, "exactly one label"):
            validate_and_build_single_label_rows(
                dataset_id="ml_esg2_zh_official_v0",
                split="train",
                source_repo="ymntseng/DynamicESG",
                source_commit="commitsha",
                source_path="data/ML-ESG-2_Chinese/Train.json",
                rows=rows,
            )

    def test_audit_reports_expected_inventory(self):
        audit = build_single_label_ingest_audit(
            {
                "train": [
                    {
                        "example_id": "a",
                        "article_id": "dynamicesg_bt_1",
                        "split": "train",
                        "headline": "Headline 1",
                        "url": "https://one",
                        "impact_type": "Opportunity",
                    }
                ],
                "test": [
                    {
                        "example_id": "b",
                        "article_id": "dynamicesg_bt_2",
                        "split": "test",
                        "headline": "Headline 2",
                        "url": "https://two",
                        "impact_type": "Risk",
                    }
                ],
            },
            {
                "train": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "Impact_Type": 0}},
                "test": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "Impact_Type": 0}},
            },
        )
        self.assertEqual(audit["label_inventory"], ["Opportunity", "Risk"])


if __name__ == "__main__":
    unittest.main()
