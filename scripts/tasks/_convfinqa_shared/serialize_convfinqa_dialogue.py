from __future__ import annotations


def serialize_convfinqa_dialogue(dialogue_questions: list[str]) -> str:
    return "\n".join(f"[Turn {idx}] {question}" for idx, question in enumerate(dialogue_questions, start=1))
