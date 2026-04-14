from __future__ import annotations

import sys
from pathlib import Path


FINQA_SHARED_DIR = Path(__file__).resolve().parents[1] / "_finqa_shared"
if str(FINQA_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(FINQA_SHARED_DIR))

from execute_finqa_program import END_TOKEN, equal_program, execution_matches_gold, program_exact_match  # noqa: E402
from parse_finqa_program import (  # noqa: E402
    PROGRAM_KEY_ALIASES,
    canonicalize_program_tokens,
    detokenize_program_tokens,
    parse_program_prediction,
    tokenize_source_program,
    validate_program_tokens,
)


__all__ = [
    "END_TOKEN",
    "PROGRAM_KEY_ALIASES",
    "canonicalize_program_tokens",
    "detokenize_program_tokens",
    "equal_program",
    "execution_matches_gold",
    "parse_program_prediction",
    "program_exact_match",
    "tokenize_source_program",
    "validate_program_tokens",
]
