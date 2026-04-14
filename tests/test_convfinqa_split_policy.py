import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ConvFinqaSplitPolicyTests(unittest.TestCase):
    def test_dataset_spec_excludes_supervised_test_file(self):
        spec = json.loads((REPO_ROOT / "datasets" / "convfinqa_official_v0" / "dataset_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(spec["processed"]["files"]), ["dev", "ingest_summary", "label_inventory", "train"])
        self.assertEqual(spec["split_policy"]["test_policy"], "raw_only_private_unlabeled_not_published_as_supervised_split")

    def test_task_spec_excludes_test_split(self):
        task_spec = json.loads((REPO_ROOT / "tasks" / "convfinqa_program_generation_v0" / "task_spec.json").read_text(encoding="utf-8"))
        self.assertNotIn("test_file", task_spec["dataset"])

    def test_publish_record_does_not_publish_supervised_test(self):
        publish_record = json.loads((REPO_ROOT / "manifests" / "publish" / "convfinqa_official_v0_publish_record.json").read_text(encoding="utf-8"))
        artifacts = publish_record["artifacts_published"]
        self.assertFalse(any(path.endswith("/test.jsonl") for path in artifacts))
        self.assertFalse(any(path.endswith("/test_requests.jsonl") for path in artifacts))
        self.assertIn("datasets/convfinqa/official/v0/test_release_summary.json", artifacts)

    def test_family_provenance_note_present(self):
        readme = (REPO_ROOT / "datasets" / "convfinqa_official_v0" / "README.md").read_text(encoding="utf-8")
        self.assertIn("FinQA-family conversational derivative", readme)


if __name__ == "__main__":
    unittest.main()
