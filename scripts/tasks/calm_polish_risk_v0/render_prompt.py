from __future__ import annotations

import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/calm_polish_risk_v0/task_spec.json")
SHARED_DIR = Path(__file__).resolve().parents[1] / "_calm_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from calm_binary_wrapper import load_task_spec, render_user_prompt as shared_render_user_prompt  # noqa: E402


TASK_SPEC = load_task_spec(TASK_SPEC_PATH)


def render_user_prompt(row: dict) -> str:
    return shared_render_user_prompt(row, TASK_SPEC)
