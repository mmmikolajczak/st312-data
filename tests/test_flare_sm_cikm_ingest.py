import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class FlareSmCikmIngestTests(unittest.TestCase):
    def test_raw_schema_summary_records_wrapper_source_and_counts(self):
        summary = json.loads((REPO_ROOT / "reports" / "flare_sm_cikm_public" / "raw_schema_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["source_repo"], "TheFinAI/flare-sm-cikm")
        self.assertTrue(summary["original_first_party_release_publicly_unrecoverable"])
        self.assertEqual(summary["split_row_counts"], {"train": 3396, "valid": 431, "test": 1143})

    def test_processed_rows_preserve_wrapper_split(self):
        train_row = json.loads((REPO_ROOT / "data" / "flare_sm_cikm_public" / "processed" / "train.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(train_row["dataset_id"], "flare_sm_cikm_public_v0")
        self.assertEqual(train_row["split"], "train")
        self.assertIn("query", train_row)
        self.assertIn("context_text", train_row)

    def test_label_mapping_is_derived_and_consistent(self):
        label_inventory = json.loads((REPO_ROOT / "data" / "flare_sm_cikm_public" / "processed" / "label_inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(label_inventory["wrapper_gold_to_label_text"], {"0": "Rise", "1": "Fall"})
        crosstab = label_inventory["wrapper_answer_gold_crosstab_by_split"]
        self.assertEqual(crosstab["train"]["0"]["answer"], "Rise")
        self.assertEqual(crosstab["train"]["1"]["answer"], "Fall")

    def test_dataset_spec_records_wrapper_based_provenance(self):
        spec = json.loads((REPO_ROOT / "datasets" / "flare_sm_cikm_public_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertTrue(spec["provenance"]["original_first_party_release_publicly_unrecoverable"])
        self.assertFalse(spec["split_policy"]["split_reconstruction_is_st312_derived"])
        self.assertEqual(spec["split_policy"]["split_source"], "thefinai_wrapper_release")
        self.assertEqual(spec["hf_publish"]["release_scope"], "hf_repo_standard_public_release_with_upstream_rights_caution")


if __name__ == "__main__":
    unittest.main()
