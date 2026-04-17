from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_forecast_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from parse_binary_direction import extract_first_json_object, parse_label_prediction  # noqa: E402


def format_reward(pred_text: str) -> float:
    return 0.1 if parse_label_prediction(pred_text) is not None else 0.0


def schema_reward(pred_text: str) -> float:
    parsed = extract_first_json_object(pred_text)
    if not isinstance(parsed, dict):
        return 0.0
    if set(parsed.keys()) != {"label"}:
        return 0.0
    return 0.1 if isinstance(parsed.get("label"), str) else 0.0


def correctness_reward(pred_text: str, gold_label: str) -> float:
    parsed = parse_label_prediction(pred_text)
    if parsed is None:
        return 0.0
    return 0.8 if parsed["label"] == gold_label else 0.0


def reward_breakdown(pred_text: str, gold_label: str) -> dict[str, float | str | None]:
    parsed = parse_label_prediction(pred_text)
    return {
        "parsed_label": parsed["label"] if parsed is not None else None,
        "format_reward": format_reward(pred_text),
        "schema_reward": schema_reward(pred_text),
        "correctness_reward": correctness_reward(pred_text, gold_label),
        "total_reward": format_reward(pred_text) + schema_reward(pred_text) + correctness_reward(pred_text, gold_label),
    }


def run_smoke_test() -> None:
    cases = [
        ("perfect_rise", '{"label":"Rise"}', "Rise"),
        ("perfect_fall", '{"label":"Fall"}', "Fall"),
        ("wrong_label", '{"label":"Fall"}', "Rise"),
        ("extra_key", '{"label":"Rise","note":"x"}', "Rise"),
        ("not_json", 'Rise', "Rise"),
    ]
    results = []
    for name, pred_text, gold in cases:
        results.append({"case": name, **reward_breakdown(pred_text, gold)})
    print(json.dumps({"status": "ok", "cases": results}, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        run_smoke_test()
        return

    if args.pred_text is None or args.gold_label is None:
        raise SystemExit("Provide --pred-text and --gold-label, or use --smoke-test")

    print(json.dumps(reward_breakdown(args.pred_text, args.gold_label), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
