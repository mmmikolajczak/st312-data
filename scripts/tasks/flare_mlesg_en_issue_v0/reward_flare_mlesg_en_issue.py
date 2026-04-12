import argparse
import json
import re
from json import JSONDecodeError, JSONDecoder
from typing import Optional


LABELS = [
    "Access to Communications",
    "Biodiversity & Land Use",
    "Packaging Material & Waste",
    "Financing Environmental Impact",
    "Carbon Emissions",
    "Human Capital Development",
    "Ownership & Control",
    "Community Relations",
    "Responsible Investment",
    "Opportunities in Renewable Energy",
    "Consumer Financial Protection",
    "Accounting",
    "Business Ethics",
    "Opportunities in Clean Tech",
    "Toxic Emissions & Waste",
    "Product Carbon Footprint",
    "Opportunities in Green Building",
    "Climate Change Vulnerability",
    "Pay",
    "Water Stress",
    "Supply Chain Labor Standards",
    "Chemical Safety",
    "Board",
    "Opportunities in Nutrition & Health",
    "Access to Health Care",
    "Electronic Waste",
    "Access to Finance",
    "Raw Material Sourcing",
    "Health & Demographic Risk",
    "Labor Management",
    "Controversial Sourcing",
    "Privacy & Data Security",
    "Product Safety & Quality"
]
WHITESPACE_RE = re.compile(r"\s+")
DECODER = JSONDecoder()
NORMALIZED_TO_CANONICAL = {
    WHITESPACE_RE.sub(" ", label.strip()).lower(): label for label in LABELS
}


def normalize_label(value: str) -> str:
    return WHITESPACE_RE.sub(" ", str(value).strip())


def extract_first_json_object(text: str) -> Optional[dict]:
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = DECODER.raw_decode(text[idx:])
        except JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def canonicalize_label(value: str) -> Optional[str]:
    normalized = normalize_label(value).lower()
    return NORMALIZED_TO_CANONICAL.get(normalized)


def parse_prediction(text: str) -> Optional[str]:
    obj = extract_first_json_object(text)
    if obj is None:
        return None
    if set(obj.keys()) != {"issue"}:
        return None
    value = obj.get("issue")
    if not isinstance(value, str):
        return None
    return canonicalize_label(value)


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def correctness_reward(text: str, gold_label: str) -> float:
    pred = parse_prediction(text)
    gold = canonicalize_label(gold_label)
    if pred is None or gold is None:
        return 0.0
    return 1.0 if pred == gold else 0.0


def total_reward(text: str, gold_label: str, w_format: float = 1.0, w_correct: float = 1.0) -> float:
    return w_format * format_reward(text) + w_correct * correctness_reward(text, gold_label)


def smoke_test():
    gold = "Access to Communications"
    cases = [
        {
            "name": "perfect_json",
            "text": '{"issue":"Access to Communications"}',
            "expected_pred": "Access to Communications",
            "expected_format": 1.0,
            "expected_correct": 1.0
        },
        {
            "name": "valid_json_wrong_label",
            "text": '{"issue":"Accounting"}',
            "expected_pred": "Accounting",
            "expected_format": 1.0,
            "expected_correct": 0.0
        },
        {
            "name": "embedded_json_extra_text",
            "text": 'Answer: {"issue":"access   to communications"} Thanks.',
            "expected_pred": "Access to Communications",
            "expected_format": 1.0,
            "expected_correct": 1.0
        },
        {
            "name": "invalid_label",
            "text": '{"issue":"Greenwashing"}',
            "expected_pred": None,
            "expected_format": 0.0,
            "expected_correct": 0.0
        },
        {
            "name": "extra_key",
            "text": '{"issue":"Access to Communications","confidence":0.9}',
            "expected_pred": None,
            "expected_format": 0.0,
            "expected_correct": 0.0
        },
        {
            "name": "non_json_output",
            "text": "Access to Communications",
            "expected_pred": None,
            "expected_format": 0.0,
            "expected_correct": 0.0
        }
    ]

    for case in cases:
        pred = parse_prediction(case["text"])
        rf = format_reward(case["text"])
        rc = correctness_reward(case["text"], gold)
        rt = total_reward(case["text"], gold)
        assert pred == case["expected_pred"], f"{case['name']}: pred={pred}"
        assert rf == case["expected_format"], f"{case['name']}: format={rf}"
        assert rc == case["expected_correct"], f"{case['name']}: correct={rc}"
        assert rt == rf + rc, f"{case['name']}: total={rt}"

    print("[PASS] Smoke test passed")
    for case in cases:
        print(f"- {case['name']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-label", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None or args.gold_label is None:
        raise SystemExit("Provide --pred-text and --gold-label, or use --smoke-test")

    gold = canonicalize_label(args.gold_label)
    if gold is None:
        raise SystemExit("gold-label must be one of the canonical 33 issue labels")

    pred = parse_prediction(args.pred_text)
    print(f"parsed_prediction={pred}")
    print(f"format_reward={format_reward(args.pred_text)}")
    print(f"correctness_reward={correctness_reward(args.pred_text, gold)}")
    print(f"total_reward={total_reward(args.pred_text, gold)}")


if __name__ == "__main__":
    main()
