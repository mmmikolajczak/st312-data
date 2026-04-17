from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_forecast_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from extract_label_from_json_or_text import extract_label_from_json_or_text  # noqa: E402


def score_completion(pred_text: str, gold_label: str) -> dict[str, float | str | None]:
    extracted = extract_label_from_json_or_text(pred_text)
    if extracted is None:
        return {"parsed_label": None, "reward": 0.0}
    return {
        "parsed_label": extracted["label"],
        "mode": extracted["mode"],
        "reward": 1.0 if extracted["label"] == gold_label else 0.0,
    }


def run_smoke_test() -> None:
    cases = [
        ("json_rise", '{"label":"Rise"}', "Rise"),
        ("text_fall", 'Answer: Fall', "Fall"),
        ("ambiguous", 'Rise or Fall', "Rise"),
        ("wrong", 'Prediction: Rise', "Fall"),
    ]
    rows = []
    for name, pred_text, gold in cases:
        rows.append({"case": name, **score_completion(pred_text, gold)})
    print(json.dumps({"status": "ok", "cases": rows}, indent=2, ensure_ascii=False))


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

    print(json.dumps(score_completion(args.pred_text, args.gold_label), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
