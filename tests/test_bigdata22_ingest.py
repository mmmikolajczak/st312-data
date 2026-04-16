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

    def test_split_metadata_is_explicitly_st312_derived(self):
        spec = json.loads((REPO_ROOT / "datasets" / "bigdata22_official_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        split_policy = spec["split_policy"]
        self.assertTrue(split_policy["split_reconstruction_is_st312_derived"])
        self.assertEqual(split_policy["reconstruction_basis"], "target_trading_dates")
        self.assertEqual(split_policy["paper_only_claim"], "chronological_split_without_published_cut_dates")
        self.assertEqual(split_policy["split_source"], "st312_derived_due_to_public_first_party_split_unrecoverable")
        self.assertFalse(split_policy["official_author_split_recovered_from_public_first_party_materials"])

    def test_split_ranges_are_non_overlapping_and_trading_date_based(self):
        summary = json.loads((REPO_ROOT / "data" / "bigdata22_official" / "processed" / "ingest_summary.json").read_text(encoding="utf-8"))
        split_policy = summary["split_policy"]
        ranges = split_policy["split_target_trading_date_ranges"]
        self.assertLess(ranges["train"]["max"], ranges["valid"]["min"])
        self.assertLess(ranges["valid"]["max"], ranges["test"]["min"])
        self.assertEqual(split_policy["target_trading_dates_total"], 250)
        self.assertEqual(split_policy["split_target_trading_date_counts"], {"train": 175, "valid": 25, "test": 50})

    def test_label_threshold_audit_is_present_and_clean(self):
        audit = json.loads((REPO_ROOT / "reports" / "bigdata22_official" / "ingest_audit.json").read_text(encoding="utf-8"))
        threshold_audit = audit["label_threshold_consistency_audit"]
        self.assertGreater(threshold_audit["total_checked_rows"], 0)
        self.assertEqual(threshold_audit["mismatch_count"], 0)
        self.assertEqual(threshold_audit["threshold_consistent_rows"], threshold_audit["total_checked_rows"])

    def test_metadata_records_unrecoverable_official_split(self):
        audit = json.loads((REPO_ROOT / "reports" / "bigdata22_official" / "ingest_audit.json").read_text(encoding="utf-8"))
        split_policy = audit["split_policy"]
        self.assertTrue(split_policy["public_first_party_recovery_search_completed"])
        self.assertFalse(split_policy["official_author_split_recovered_from_public_first_party_materials"])
        joined_notes = " ".join(split_policy["notes"]).lower()
        self.assertIn("no public first-party split files or cut dates were recoverable", joined_notes)

    def test_task_spec_has_explicit_finben_taxonomy(self):
        spec = json.loads((REPO_ROOT / "tasks" / "bigdata22_stock_movement_v0" / "task_spec.json").read_text(encoding="utf-8"))
        taxonomy = spec["taxonomy"]
        self.assertEqual(taxonomy["finben_supercategory"], "Forecasting")
        self.assertEqual(taxonomy["finben_category"], "Stock Movement Prediction")

    def test_publication_metadata_carries_rights_caution(self):
        spec = json.loads((REPO_ROOT / "datasets" / "bigdata22_official_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["hf_publish"]["release_scope"], "hf_repo_standard_public_release_with_upstream_rights_caution")
        self.assertFalse(spec["hf_publish"]["public_release_cleared"])


if __name__ == "__main__":
    unittest.main()
