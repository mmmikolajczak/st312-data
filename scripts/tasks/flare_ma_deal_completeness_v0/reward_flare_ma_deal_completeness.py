from __future__ import annotations

import argparse
import json


ALLOWED = {"rumour", "complete"}


def normalize_label(value: str) -> str:
    return str(value).strip().lower()


def extract_label(prediction_text: str) -> str | None:
    raw = prediction_text.strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = None

    if isinstance(parsed, dict) and "label" in parsed:
        candidate = normalize_label(parsed["label"])
        return candidate if candidate in ALLOWED else None

    candidate = normalize_label(raw)
    return candidate if candidate in ALLOWED else None


def score_prediction(prediction_text: str, gold_label: str) -> dict:
    parsed = extract_label(prediction_text)
    format_reward = 1.0 if parsed is not None else 0.0
    correctness_reward = 1.0 if parsed == normalize_label(gold_label) else 0.0
    total_reward = format_reward + correctness_reward

    return {
        "parsed_label": parsed,
        "format_reward": format_reward,
        "correctness_reward": correctness_reward,
        "total_reward": total_reward,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction-text", required=True)
    parser.add_argument("--gold-label", required=True)
    args = parser.parse_args()

    result = score_prediction(args.prediction_text, args.gold_label)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
