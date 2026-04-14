from __future__ import annotations

import json

from execute_finqa_program import (
    CANONICAL_OPERATION_TOKENS,
    CLOSE_TOKEN,
    END_TOKEN,
    OFFICIAL_OPERATION_NAMES,
    REFERENCE_PREFIX,
    str_to_num,
)


PROGRAM_KEY_ALIASES = ["program_tokens", "predicted", "program"]
HYPHENATED_OPERATION_ALIASES = {
    "table-max(": "table_max(",
    "table-min(": "table_min(",
    "table-sum(": "table_sum(",
    "table-average(": "table_average(",
}


def tokenize_source_program(original_program: str) -> list[str]:
    original_program = original_program.split(", ")
    program = []
    for tok in original_program:
        cur_tok = ""
        for char in tok:
            if char == ")":
                if cur_tok != "":
                    program.append(cur_tok)
                    cur_tok = ""
            cur_tok += char
            if char in ["(", ")"]:
                program.append(cur_tok)
                cur_tok = ""
        if cur_tok != "":
            program.append(cur_tok)
    program.append(END_TOKEN)
    return program


def detokenize_program_tokens(tokens: list[str]) -> str:
    if not tokens or tokens[-1] != END_TOKEN:
        raise ValueError("Program tokens must end with EOF")
    body = tokens[:-1]
    if len(body) == 1:
        return body[0]
    if len(body) % 4 != 0:
        raise ValueError("Program token body must be divisible into 4-token steps")
    steps = []
    for idx in range(0, len(body), 4):
        op, arg1, arg2, close = body[idx : idx + 4]
        if close != CLOSE_TOKEN:
            raise ValueError("Program step must terminate with ')'")
        steps.append(f"{op}{arg1}, {arg2}{close}")
    return ", ".join(steps)


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


def canonicalize_program_tokens(tokens: list[str]) -> list[str]:
    normalized = []
    for token in tokens:
        if not isinstance(token, str):
            raise TypeError("Program tokens must all be strings")
        value = token.strip()
        if not value:
            raise ValueError("Program tokens may not be empty after trimming")
        if value in OFFICIAL_OPERATION_NAMES:
            value = f"{value}("
        value = HYPHENATED_OPERATION_ALIASES.get(value, value)
        normalized.append(value)
    return normalized


def _is_valid_single_value_token(token: str) -> bool:
    if token.startswith(REFERENCE_PREFIX):
        return False
    if token.lower() in {"yes", "no"}:
        return True
    return str_to_num(token) != "n/a"


def validate_program_tokens(tokens: list[str]) -> tuple[bool, str | None]:
    try:
        normalized = canonicalize_program_tokens(tokens)
    except Exception as exc:
        return False, str(exc)

    if not normalized:
        return False, "Program token list is empty"
    if normalized[-1] != END_TOKEN:
        return False, "Final token must be EOF"

    body = normalized[:-1]
    if len(body) == 1:
        return (_is_valid_single_value_token(body[0]), None if _is_valid_single_value_token(body[0]) else "Single-value programs must contain a numeric or boolean literal")
    if len(body) == 0 or len(body) % 4 != 0:
        return False, "Program body must consist of 4-token steps before EOF"

    for idx in range(0, len(body), 4):
        step_index = idx // 4
        op, arg1, arg2, close = body[idx : idx + 4]

        if op not in CANONICAL_OPERATION_TOKENS:
            return False, f"Invalid operation token: {op}"
        if close != CLOSE_TOKEN:
            return False, "Every step must terminate with ')'"
        if not arg1 or not arg2:
            return False, "Arguments must be non-empty strings"

        for arg in [arg1, arg2]:
            if arg.startswith(REFERENCE_PREFIX):
                ref = arg[len(REFERENCE_PREFIX) :]
                if not ref.isdigit():
                    return False, f"Invalid reference token: {arg}"
                if int(ref) >= step_index:
                    return False, f"Forward/self reference is invalid: {arg}"

    return True, None


def parse_program_prediction(text: str, *, alias_keys: list[str] | None = None, require_dsl_valid: bool = True):
    alias_keys = alias_keys or PROGRAM_KEY_ALIASES
    parsed = extract_first_json_object(text)
    if not isinstance(parsed, dict) or len(parsed) != 1:
        return None

    key, value = next(iter(parsed.items()))
    if key not in alias_keys or not isinstance(value, list):
        return None

    try:
        tokens = canonicalize_program_tokens(value)
    except Exception:
        return None

    if require_dsl_valid:
        valid, _ = validate_program_tokens(tokens)
        if not valid:
            return None

    return tokens
