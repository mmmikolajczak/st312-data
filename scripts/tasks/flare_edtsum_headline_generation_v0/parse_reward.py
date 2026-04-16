from __future__ import annotations

"""Offline-only EDTSUM reward utilities.

These helpers are intentionally non-canonical and are meant only for local
experimentation. Benchmark-authoritative comparison should use eval_cached.py,
not the reward totals defined here.
"""

import argparse
import json


def normalize_headline_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


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


def inspect_prediction(text: str) -> dict:
    parsed = extract_first_json_object(text)
    has_json_object = parsed is not None
    valid_json_object = isinstance(parsed, dict)
    valid_answer_key = valid_json_object and len(parsed) == 1 and "answer" in parsed and isinstance(parsed.get("answer"), str)
    answer = parsed.get("answer") if valid_json_object else None
    normalized = normalize_headline_text(answer) if isinstance(answer, str) else ""
    return {
        "has_json_object": has_json_object,
        "valid_json_object": valid_json_object,
        "valid_answer_key": valid_answer_key,
        "nonempty_answer": bool(normalized),
        "answer": answer if isinstance(answer, str) else None,
        "normalized_answer": normalized,
    }


def parse_prediction(text: str) -> dict | None:
    inspected = inspect_prediction(text)
    if not inspected["valid_answer_key"]:
        return None
    return {
        "answer": inspected["answer"],
        "normalized_answer": inspected["normalized_answer"],
        "_format_valid": True,
    }


def format_reward(text: str) -> float:
    return 1.0 if parse_prediction(text) is not None else 0.0


def non_empty_reward(text: str) -> float:
    parsed = parse_prediction(text)
    return 1.0 if parsed and parsed["normalized_answer"] else 0.0


def headline_shape_reward(text: str, reference_answer: str | None = None) -> float:
    parsed = parse_prediction(text)
    if parsed is None:
        return 0.0

    answer = parsed["normalized_answer"]
    if not answer:
        return 0.0

    sentence_like_markers = answer.count(". ") + answer.count("\n")
    max_len = max(160, len(reference_answer) * 2 if reference_answer else 160)
    min_len = 8
    score = 1.0

    if len(answer) < min_len:
        score -= 0.5
    if len(answer) > max_len:
        score -= 0.5
    if sentence_like_markers > 1:
        score -= 0.5
    if answer.endswith("."):
        score -= 0.15

    return max(0.0, score)


def degenerate_output_penalty(text: str) -> float:
    parsed = parse_prediction(text)
    if parsed is None:
        return -1.0
    answer = parsed["normalized_answer"].lower()
    if not answer:
        return -1.0
    if answer in {"n/a", "none", "headline", "summary"}:
        return -1.0
    return 0.0


def total_reward(text: str, reference_answer: str | None = None) -> float:
    return (
        format_reward(text)
        + non_empty_reward(text)
        + headline_shape_reward(text, reference_answer=reference_answer)
        + degenerate_output_penalty(text)
    )


def smoke_test() -> None:
    reference = "Loop Energy Applauds Skywell and Joint Venture Partner InPower for Inclusion of a Commercial Hydrogen Fuel Cell Electric Bus into China's MIIT New Energy Vehicle Index"
    cases = [
        ('{"answer":"Loop Energy applauds Skywell hydrogen fuel cell bus inclusion in MIIT new energy vehicle index"}', True),
        ('Result: {"answer":"Technavio says Europe all-season tire market to reach $3.42 billion by 2024"}', True),
        ('{"answer":"This is a long paragraph summary. It keeps going well beyond a normal headline and should be penalized for not behaving like a title."}', True),
        ('{"answer":""}', True),
        ('{"answer":17}', False),
        ('{"answer":"x","extra":"y"}', False),
        ("not json", False),
    ]
    rows = []
    for text, expected_valid in cases:
        parsed = parse_prediction(text)
        inspected = inspect_prediction(text)
        actual_valid = parsed is not None
        if actual_valid != expected_valid:
            raise AssertionError(f"Unexpected parser result for input: {text}")
        rows.append(
            {
                "input": text,
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "parsed": parsed,
                "inspected": inspected,
                "format_reward": format_reward(text),
                "non_empty_reward": non_empty_reward(text),
                "headline_shape_reward": headline_shape_reward(text, reference),
                "degenerate_output_penalty": degenerate_output_penalty(text),
                "total_reward": total_reward(text, reference),
            }
        )
    print(json.dumps({"status": "ok", "cases": rows}, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--reference-answer", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if args.pred_text is None:
        raise SystemExit("Provide --pred-text or use --smoke-test")

    parsed = parse_prediction(args.pred_text)
    print(f"parsed_prediction={parsed}")
    print(f"format_reward={format_reward(args.pred_text)}")
    print(f"non_empty_reward={non_empty_reward(args.pred_text)}")
    print(f"headline_shape_reward={headline_shape_reward(args.pred_text, args.reference_answer)}")
    print(f"degenerate_output_penalty={degenerate_output_penalty(args.pred_text)}")
    print(f"total_reward={total_reward(args.pred_text, args.reference_answer)}")


if __name__ == "__main__":
    main()
