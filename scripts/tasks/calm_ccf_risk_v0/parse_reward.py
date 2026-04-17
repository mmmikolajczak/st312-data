from __future__ import annotations

import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/calm_ccf_risk_v0/task_spec.json")
SHARED_DIR = Path(__file__).resolve().parents[1] / "_calm_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from calm_binary_wrapper import reward_argparser, reward_cli  # noqa: E402


def main() -> None:
    args = reward_argparser().parse_args()
    reward_cli(TASK_SPEC_PATH, smoke_test=args.smoke_test)


if __name__ == "__main__":
    main()
