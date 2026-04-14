import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INGEST_DIR = REPO_ROOT / "scripts" / "datasets" / "convfinqa_official"
FINQA_SHARED = REPO_ROOT / "scripts" / "tasks" / "_finqa_shared"
CONV_SHARED = REPO_ROOT / "scripts" / "tasks" / "_convfinqa_shared"
for path in [INGEST_DIR, FINQA_SHARED, CONV_SHARED]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ingest_convfinqa_official import TURN_SOURCE_PATHS, build_processed_row, derive_conversation_id, validate_turn_split  # noqa: E402
from serialize_convfinqa_dialogue import serialize_convfinqa_dialogue  # noqa: E402


class ConvFinqaIngestTests(unittest.TestCase):
    def test_conversation_id_derivation(self):
        self.assertEqual(derive_conversation_id("Single_JKHY/2009/page_28.pdf-3_0"), "Single_JKHY/2009/page_28.pdf-3")

    def test_dialogue_serialization_is_deterministic(self):
        dialogue = ["How much was revenue?", "What about the difference from cost?"]
        self.assertEqual(
            serialize_convfinqa_dialogue(dialogue),
            "[Turn 1] How much was revenue?\n[Turn 2] What about the difference from cost?",
        )

    def test_processed_row_normalization(self):
        row = {
            "id": "Single_JKHY/2009/page_28.pdf-3_1",
            "filename": "Single_JKHY/2009/page_28.pdf-3",
            "pre_text": ["line 1"],
            "post_text": ["line 2"],
            "table": [["metric", "value"], ["revenue", "120"], ["cost", "20"]],
            "annotation": {
                "cur_dial": ["How much was revenue?", "What is revenue minus cost?"],
                "cur_program": "subtract(120, 20)",
                "exe_ans": 100.0,
                "gold_ind": {"table_1": "revenue row"},
                "cur_type": "program_turn",
                "turn_ind": 1,
                "qa_split": ["program", "program"],
                "original_program": "subtract(120, 20)",
            },
        }
        processed = build_processed_row("train", "commitsha", "data/train_turn.json", row, require_labels=True)
        self.assertEqual(processed["conversation_id"], "Single_JKHY/2009/page_28.pdf-3")
        self.assertEqual(processed["current_question"], "What is revenue minus cost?")
        self.assertEqual(processed["gold_program_tokens"], ["subtract(", "120", "20", ")", "EOF"])
        self.assertEqual(processed["gold_execution_answer"], "100")
        self.assertEqual(processed["gold_supporting_facts"], {"table_1": "revenue row"})
        self.assertEqual(processed["current_qa_split"], "program")

    def test_supporting_facts_preserved_in_validation(self):
        processed = [
            {
                "example_id": "ex1",
                "conversation_id": "conv1",
                "turn_index": 0,
                "current_turn_type": "program_turn",
                "dialogue_history_questions": ["q1"],
                "gold_supporting_facts": {"table_1": "row"},
                "current_qa_split": "program",
                "conversation_form": "simple",
            }
        ]
        summary = validate_turn_split(processed, split="train")
        self.assertEqual(summary["supporting_fact_count_distribution"], {1: 1})

    def test_no_supervised_test_turn_split_path(self):
        self.assertEqual(sorted(TURN_SOURCE_PATHS), ["dev", "train"])


if __name__ == "__main__":
    unittest.main()
