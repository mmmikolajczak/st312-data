from __future__ import annotations

import argparse
import json
from typing import Any


ALLOWED_LABELS = {"good", "bad"}


def extract_json_object(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def inspect_prediction(text: str, variant: str = "uci_cost_sensitive_default") -> dict:
    obj = extract_json_object(text)
    info = {
        "valid_json_object": isinstance(obj, dict),
        "valid_label_key": False,
        "nonempty_label": False,
        "label": None,
        "accepted_key": None,
    }
    if not isinstance(obj, dict):
        return info

    accepted_keys = ["label"] if variant == "uci_cost_sensitive_default" else ["label", "answer"]
    for key in accepted_keys:
        value = obj.get(key)
        if isinstance(value, str):
            normalized = value.strip().lower()
            info["accepted_key"] = key
            if normalized:
                info["nonempty_label"] = True
            if normalized in ALLOWED_LABELS and len(obj.keys()) == 1:
                info["valid_label_key"] = True
                info["label"] = normalized
                return info
    return info


def parse_prediction(text: str, variant: str = "uci_cost_sensitive_default") -> dict | None:
    inspected = inspect_prediction(text, variant=variant)
    if not inspected["valid_label_key"]:
        return None
    return {"label": inspected["label"], "_format_valid": True}


def cost(actual: str, predicted: str) -> int:
    if actual == predicted:
        return 0
    if actual == "good" and predicted == "bad":
        return 1
    if actual == "bad" and predicted == "good":
        return 5
    return 5


def format_reward(text: str, variant: str = "uci_cost_sensitive_default") -> float:
    return 1.0 if inspect_prediction(text, variant=variant)["valid_json_object"] else 0.0


def label_valid_reward(text: str, variant: str = "uci_cost_sensitive_default") -> float:
    return 1.0 if inspect_prediction(text, variant=variant)["valid_label_key"] else 0.0


def cost_aware_decision_reward(text: str, gold_label: str, variant: str = "uci_cost_sensitive_default") -> float:
    parsed = parse_prediction(text, variant=variant)
    if parsed is None:
        return 0.0
    return 1.0 - (cost(gold_label, parsed["label"]) / 5.0)


def total_reward(text: str, gold_label: str, variant: str = "uci_cost_sensitive_default") -> float:
    return (
        0.2 * format_reward(text, variant=variant)
        + 0.2 * label_valid_reward(text, variant=variant)
        + 0.6 * cost_aware_decision_reward(text, gold_label, variant=variant)
    )


def smoke_test(variant: str) -> dict:
    cases = [
        ('{"label":"good"}', "good"),
        ('Lead {"label":"bad"}', "bad"),
        ('{"answer":"good"}', "good"),
        ('{"label":"hold"}', "bad"),
        ("not json", "good"),
    ]
    report = {"status": "ok", "variant": variant, "cases": []}
    for text, gold in cases:
        report["cases"].append(
            {
                "input": text,
                "gold": gold,
                "variant": variant,
                "parsed": parse_prediction(text, variant=variant),
                "inspected": inspect_prediction(text, variant=variant),
                "format_reward": format_reward(text, variant=variant),
                "label_valid_reward": label_valid_reward(text, variant=variant),
                "cost_aware_decision_reward": cost_aware_decision_reward(text, gold, variant=variant),
                "total_reward": total_reward(text, gold, variant=variant),
            }
        )
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--variant",
        choices=["uci_cost_sensitive_default", "finben_optional_f1_mcc"],
        default="uci_cost_sensitive_default",
    )
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        print(json.dumps(smoke_test(args.variant), indent=2, ensure_ascii=False))
        return

    raise SystemExit("Use --smoke-test for a local parser/reward sanity check.")


if __name__ == "__main__":
    main()
