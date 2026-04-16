from __future__ import annotations

"""Offline-only StockNet ACL18 reward utilities.

These helpers are intentionally non-canonical and are meant only for local
experimentation. Benchmark-authoritative comparison should use eval_cached.py
with accuracy and MCC, not the reward totals defined here.
"""

import argparse
import json


ALLOWED_LABELS = {"rise": "Rise", "fall": "Fall"}


def extract_first_json_object(text: str):
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                snippet = text[start : idx + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    return None
    return None


def normalize_label(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    return ALLOWED_LABELS.get(value.strip().lower())


def inspect_prediction(text: str, variant: str = "paper_default") -> dict:
    parsed = extract_first_json_object(text)
    valid_json_object = isinstance(parsed, dict)
    accepted_keys = {"label"} if variant == "paper_default" else {"label", "answer"}
    if not valid_json_object or len(parsed) != 1:
        return {
            "valid_json_object": valid_json_object,
            "valid_label_key": False,
            "nonempty_label": False,
            "label": None,
        }
    key = next(iter(parsed.keys()))
    if key not in accepted_keys:
        return {
            "valid_json_object": True,
            "valid_label_key": False,
            "nonempty_label": False,
            "label": None,
        }
    label = normalize_label(parsed.get(key))
    return {
        "valid_json_object": True,
        "valid_label_key": label is not None,
        "nonempty_label": label is not None,
        "label": label,
        "accepted_key": key,
    }


def parse_prediction(text: str, variant: str = "paper_default") -> dict | None:
    inspected = inspect_prediction(text, variant=variant)
    if not inspected["valid_label_key"]:
        return None
    return {"label": inspected["label"], "_format_valid": True}


def format_reward(text: str, variant: str = "paper_default") -> float:
    return 1.0 if inspect_prediction(text, variant=variant)["valid_json_object"] else 0.0


def label_valid_reward(text: str, variant: str = "paper_default") -> float:
    return 1.0 if inspect_prediction(text, variant=variant)["valid_label_key"] else 0.0


def exact_match_reward(text: str, gold_label: str, variant: str = "paper_default") -> float:
    parsed = parse_prediction(text, variant=variant)
    return 1.0 if parsed and parsed["label"] == gold_label else 0.0


def malformed_output_penalty(text: str, variant: str = "paper_default") -> float:
    return -1.0 if parse_prediction(text, variant=variant) is None else 0.0


def total_reward(text: str, gold_label: str, variant: str = "paper_default") -> float:
    return (
        format_reward(text, variant=variant)
        + label_valid_reward(text, variant=variant)
        + exact_match_reward(text, gold_label=gold_label, variant=variant)
        + malformed_output_penalty(text, variant=variant)
    )


def smoke_test(variant: str) -> None:
    cases = [
        ('{"label":"Rise"}', "Rise", True),
        ('Lead: {"label":"Fall"}', "Fall", True),
        ('{"answer":"Rise"}', "Rise", variant != "paper_default"),
        ('{"label":"Hold"}', "Rise", False),
        ('{"label":"Rise","extra":"x"}', "Rise", False),
        ("not json", "Fall", False),
    ]
    rows = []
    for text, gold, expected_valid in cases:
        parsed = parse_prediction(text, variant=variant)
        actual_valid = parsed is not None
        if actual_valid != expected_valid:
            raise AssertionError(f"Unexpected parser result for input: {text}")
        rows.append(
            {
                "input": text,
                "variant": variant,
                "gold": gold,
                "parsed": parsed,
                "inspected": inspect_prediction(text, variant=variant),
                "format_reward": format_reward(text, variant=variant),
                "label_valid_reward": label_valid_reward(text, variant=variant),
                "exact_match_reward": exact_match_reward(text, gold, variant=variant),
                "malformed_output_penalty": malformed_output_penalty(text, variant=variant),
                "total_reward": total_reward(text, gold, variant=variant),
            }
        )
    print(json.dumps({"status": "ok", "cases": rows}, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=str, default=None)
    ap.add_argument("--variant", choices=["paper_default", "finben_acl18_optional"], default="paper_default")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test(args.variant)
        return
    if args.pred_text is None or args.gold_label is None:
        raise SystemExit("Provide --pred-text and --gold-label, or use --smoke-test")

    print(f"inspected={inspect_prediction(args.pred_text, variant=args.variant)}")
    print(f"parsed={parse_prediction(args.pred_text, variant=args.variant)}")
    print(f"format_reward={format_reward(args.pred_text, variant=args.variant)}")
    print(f"label_valid_reward={label_valid_reward(args.pred_text, variant=args.variant)}")
    print(f"exact_match_reward={exact_match_reward(args.pred_text, args.gold_label, variant=args.variant)}")
    print(f"malformed_output_penalty={malformed_output_penalty(args.pred_text, variant=args.variant)}")
    print(f"total_reward={total_reward(args.pred_text, args.gold_label, variant=args.variant)}")


if __name__ == "__main__":
    main()
