import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_SHARED = REPO_ROOT / "scripts" / "datasets" / "_ml_esg_shared"
if str(DATASET_SHARED) not in sys.path:
    sys.path.insert(0, str(DATASET_SHARED))

from audit_dynamic_esg_release import build_duration_ingest_audit  # noqa: E402
from validate_dynamic_esg_release import (  # noqa: E402
    build_processed_duration_row,
    validate_and_build_duration_rows,
)


class MlEsg3ZhIngestTests(unittest.TestCase):
    def test_singleton_impact_duration_normalization(self):
        row = {
            "pk": 474,
            "URL": "https://example.com/item",
            "News_Headline": "Headline",
            "Impact_Duration": [" >5 "],
        }
        processed = build_processed_duration_row(
            dataset_id="ml_esg3_zh_official_v0",
            split="dev",
            source_repo="ymntseng/DynamicESG",
            source_commit="commitsha",
            source_path="data/ML-ESG-3_Chinese/Dev.json",
            row=row,
        )
        self.assertEqual(processed["article_id"], "dynamicesg_bt_474")
        self.assertEqual(processed["example_id"], "ml_esg3_zh_official_v0__dev__dynamicesg_bt_474")
        self.assertEqual(processed["impact_duration"], ">5")
        self.assertEqual(processed["source_impact_duration_list"], [" >5 "])

    def test_duplicate_article_id_detection(self):
        rows = [
            {"pk": 1, "URL": "https://a", "News_Headline": "h1", "Impact_Duration": [">5"]},
            {"pk": 1, "URL": "https://b", "News_Headline": "h2", "Impact_Duration": ["2~5"]},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate article_id"):
            validate_and_build_duration_rows(
                dataset_id="ml_esg3_zh_official_v0",
                split="train",
                source_repo="ymntseng/DynamicESG",
                source_commit="commitsha",
                source_path="data/ML-ESG-3_Chinese/Train.json",
                rows=rows,
            )

    def test_rejects_non_singleton_duration_list(self):
        rows = [
            {"pk": 1, "URL": "https://a", "News_Headline": "h1", "Impact_Duration": [">5", "2~5"]},
        ]
        with self.assertRaisesRegex(ValueError, "exactly one label"):
            validate_and_build_duration_rows(
                dataset_id="ml_esg3_zh_official_v0",
                split="train",
                source_repo="ymntseng/DynamicESG",
                source_commit="commitsha",
                source_path="data/ML-ESG-3_Chinese/Train.json",
                rows=rows,
            )

    def test_audit_reports_expected_inventory(self):
        audit = build_duration_ingest_audit(
            {
                "train": [
                    {
                        "example_id": "a",
                        "article_id": "dynamicesg_bt_1",
                        "split": "train",
                        "headline": "Headline 1",
                        "url": "https://one",
                        "impact_duration": ">5",
                    }
                ],
                "test": [
                    {
                        "example_id": "b",
                        "article_id": "dynamicesg_bt_2",
                        "split": "test",
                        "headline": "Headline 2",
                        "url": "https://two",
                        "impact_duration": "2~5",
                    }
                ],
            },
            {
                "train": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "Impact_Duration": 0}},
                "test": {"missing_field_counts": {"pk": 0, "URL": 0, "News_Headline": 0, "Impact_Duration": 0}},
            },
        )
        self.assertEqual(audit["label_inventory"], ["2~5", ">5"])


if __name__ == "__main__":
    unittest.main()
