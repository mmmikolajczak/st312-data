import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class BigData22IngestTests(unittest.TestCase):
    def test_raw_schema_summary_confirms_archive_shape(self):
        summary = json.loads((REPO_ROOT / "reports" / "bigdata22_official" / "raw_schema_summary.json").read_text(encoding="utf-8"))
        self.assertFalse(summary["explicit_split_files_present"])
        self.assertTrue(summary["labels_materialized_in_release"])
        self.assertIn("bigdata22", summary["archive_top_level_families"])
        self.assertIn("acl18", summary["archive_top_level_families"])
        self.assertIn("cikm18", summary["archive_top_level_families"])

    def test_processed_rows_are_chronological_and_binary(self):
        train_path = REPO_ROOT / "data" / "bigdata22_official" / "processed" / "train.jsonl"
        rows = [json.loads(line) for line in train_path.read_text(encoding="utf-8").splitlines()[:20]]
        self.assertTrue(all(row["gold_label_text"] in {"Rise", "Fall"} for row in rows))
        self.assertTrue(all(row["split"] == "train" for row in rows))
        self.assertTrue(all(len(row["price_history_rows"]) == 30 for row in rows))
        self.assertTrue(all(row["target_date"] > row["history_end_date"] for row in rows))

    def test_publication_metadata_carries_rights_caution(self):
        spec = json.loads((REPO_ROOT / "datasets" / "bigdata22_official_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["hf_publish"]["release_scope"], "hf_repo_standard_public_release_with_upstream_rights_caution")
        self.assertFalse(spec["hf_publish"]["public_release_cleared"])


if __name__ == "__main__":
    unittest.main()
