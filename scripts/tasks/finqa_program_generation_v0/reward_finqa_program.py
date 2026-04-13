from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TASK_SPEC_PATH = Path("tasks/finqa_program_generation_v0/task_spec.json")
SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "_finqa_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from execute_finqa_program import END_TOKEN, equal_program, execution_matches_gold  # noqa: E402
from parse_finqa_program import parse_program_prediction, validate_program_tokens  # noqa: E402


TASK_SPEC = json.loads(TASK_SPEC_PATH.read_text(encoding="utf-8"))


def format_reward(text: str) -> float:
    tokens = parse_program_prediction(text, require_dsl_valid=False)
    return 0.5 if tokens is not None and tokens[-1] == END_TOKEN else 0.0


def dsl_validity_reward(text: str) -> float:
    tokens = parse_program_prediction(text, require_dsl_valid=False)
    if tokens is None:
        return 0.0
    valid, _ = validate_program_tokens(tokens)
    return 0.5 if valid else 0.0


def execution_reward(text: str, gold_program_tokens: list[str], table: list[list[str]], gold_execution_answer: object) -> float:
    tokens = parse_program_prediction(text, require_dsl_valid=True)
    if tokens is None:
        return 0.0
    matches, _, _ = execution_matches_gold(tokens, table, gold_execution_answer)
    return 2.0 if matches else 0.0


def program_match_reward(text: str, gold_program_tokens: list[str]) -> float:
    tokens = parse_program_prediction(text, require_dsl_valid=True)
    if tokens is None:
        return 0.0
    return 0.5 if equal_program(gold_program_tokens, tokens) else 0.0


def total_reward(text: str, gold_program_tokens: list[str], table: list[list[str]], gold_execution_answer: object) -> float:
    return (
        format_reward(text)
        + dsl_validity_reward(text)
        + execution_reward(text, gold_program_tokens, table, gold_execution_answer)
        + program_match_reward(text, gold_program_tokens)
    )


def reward_breakdown(text: str, gold_program_tokens: list[str], table: list[list[str]], gold_execution_answer: object) -> dict:
    tokens_any = parse_program_prediction(text, require_dsl_valid=False)
    tokens_valid = parse_program_prediction(text, require_dsl_valid=True)
    execution_match, invalid_flag, execution_result = (
        execution_matches_gold(tokens_valid, table, gold_execution_answer) if tokens_valid is not None else (False, 1, "n/a")
    )
    return {
        "parsed_program_tokens": tokens_any,
        "dsl_valid_program_tokens": tokens_valid,
        "gold_program_tokens": gold_program_tokens,
        "gold_execution_answer": gold_execution_answer,
        "predicted_execution_result": execution_result,
        "execution_invalid_flag": invalid_flag,
        "execution_match": execution_match,
        "format_reward": format_reward(text),
        "dsl_validity_reward": dsl_validity_reward(text),
        "execution_reward": execution_reward(text, gold_program_tokens, table, gold_execution_answer),
        "program_match_reward": program_match_reward(text, gold_program_tokens),
        "total_reward": total_reward(text, gold_program_tokens, table, gold_execution_answer),
    }


def smoke_test() -> None:
    table = [
        ["metric", "value"],
        ["revenue", "120"],
        ["cost", "20"],
    ]
    gold_program_tokens = ["subtract(", "120", "20", ")", "EOF"]
    gold_execution_answer = "100"

    cases = [
        ("perfect_json", '{"program_tokens":["subtract(","120","20",")","EOF"]}'),
        ("embedded_json", 'Answer: {"program_tokens":["subtract(","120","20",")","EOF"]}'),
        ("invalid_eof", '{"program_tokens":["subtract(","120","20",")"]}'),
        ("invalid_op", '{"program_tokens":["sum(","120","20",")","EOF"]}'),
        ("wrong_program", '{"program_tokens":["add(","120","20",")","EOF"]}'),
        ("extra_key", '{"program_tokens":["subtract(","120","20",")","EOF"],"note":"x"}'),
    ]

    for name, text in cases:
        print("=" * 72)
        print(name)
        print(json.dumps(reward_breakdown(text, gold_program_tokens, table, gold_execution_answer), indent=2, ensure_ascii=False))
    print("[PASS] Smoke test passed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--gold-program-tokens-json", type=str, default=None)
    ap.add_argument("--table-json", type=str, default=None)
    ap.add_argument("--gold-exe-ans-json", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if not all([args.pred_text, args.gold_program_tokens_json, args.table_json, args.gold_exe_ans_json]):
        raise SystemExit("Provide prediction text, gold program tokens, table JSON, and gold execution answer JSON, or use --smoke-test")

    gold_program_tokens = json.loads(args.gold_program_tokens_json)
    table = json.loads(args.table_json)
    gold_execution_answer = json.loads(args.gold_exe_ans_json)
    print(json.dumps(reward_breakdown(args.pred_text, gold_program_tokens, table, gold_execution_answer), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
