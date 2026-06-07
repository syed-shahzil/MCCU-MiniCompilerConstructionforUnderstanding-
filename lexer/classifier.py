"""
lexer/classifier.py
--------------------
Token classifier — converts raw string fragments produced by lexer.py into
typed (token_type, token_value) tuples using the unified token standard.

Refactored from m1/SQL_Tokenizer_Project/classifier.py with improvements:
  - Returns a list of tuples instead of printing
  - Uses config/keywords.py (no file I/O)
  - Uses config/token_types.py constants
  - Structural keywords get their own token type (e.g. "SELECT", "FROM")
  - Generic SQL keywords get the "KEYWORD" type
  - Numeric strings are parsed to int or float
  - Operators are classified into typed tokens (EQ, GT, LTE, etc.)
"""

from __future__ import annotations
import re

from config.token_types import (
    TT_IDENTIFIER, TT_NUMBER, TT_FLOAT, TT_STRING, TT_KEYWORD,
    TT_COMMA, TT_SEMICOLON, TT_LPAREN, TT_RPAREN,
    TT_LBRACKET, TT_RBRACKET, TT_DOT, TT_ASTERISK, TT_UNKNOWN,
    OPERATOR_SYMBOL_TO_TYPE,
)
from config.keywords import SQL_KEYWORDS, is_structural_keyword
from lexer.lexer import RawToken


# Regex pattern for a valid identifier
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Single-character delimiter → token type mapping
_DELIMITER_MAP: dict[str, str] = {
    ",": TT_COMMA,
    ";": TT_SEMICOLON,
    "(": TT_LPAREN,
    ")": TT_RPAREN,
    "[": TT_LBRACKET,
    "]": TT_RBRACKET,
    ".": TT_DOT,
    "*": TT_ASTERISK,
}


def classify(raw_tokens: list[RawToken]) -> list[tuple[str, str | int | float]]:
    """
    Classify a list of RawToken objects into typed (type, value) tuples.

    The output format is the unified token standard consumed by all parsers.

    Args:
        raw_tokens: List of RawToken objects from lexer.scan().

    Returns:
        List of (token_type, token_value) tuples.
    """
    result: list[tuple[str, str | int | float]] = []

    for rt in raw_tokens:
        raw = rt.value
        tt, tv = _classify_one(raw)
        result.append((tt, tv))

    return result


def _classify_one(raw: str) -> tuple[str, str | int | float]:
    """Classify a single raw string fragment into (type, value)."""

    # --- String literal ---
    if raw.startswith("'") and raw.endswith("'") and len(raw) >= 2:
        # Strip the surrounding quotes for the stored value
        return TT_STRING, raw[1:-1]

    # --- Operator (two-char or single-char) ---
    if raw in OPERATOR_SYMBOL_TO_TYPE:
        return OPERATOR_SYMBOL_TO_TYPE[raw], raw

    # --- Delimiter / punctuation ---
    if raw in _DELIMITER_MAP:
        return _DELIMITER_MAP[raw], raw

    # --- Numeric literal ---
    if _is_integer(raw):
        return TT_NUMBER, int(raw)

    if _is_float(raw):
        return TT_FLOAT, float(raw)

    # --- Keyword or identifier ---
    upper = raw.upper()
    if upper in SQL_KEYWORDS:
        if is_structural_keyword(upper):
            # Structural keywords become their own token type
            return upper, upper
        else:
            # Generic SQL keyword
            return TT_KEYWORD, upper

    # --- Identifier ---
    if _IDENTIFIER_PATTERN.match(raw):
        return TT_IDENTIFIER, raw

    # --- Unknown / unrecognised ---
    return TT_UNKNOWN, raw


def _is_integer(s: str) -> bool:
    """Return True if s represents a whole integer."""
    return s.isdigit()


def _is_float(s: str) -> bool:
    """Return True if s represents a floating-point number."""
    if s.count(".") != 1:
        return False
    parts = s.split(".")
    return all(p.isdigit() for p in parts if p)


def get_display_category(token_type: str) -> str:
    """
    Return a human-friendly category name for GUI display.

    Args:
        token_type: A TT_* token type string.

    Returns:
        A category label: "Keyword", "Identifier", "Operator",
        "Delimiter", "Constant", or "Unknown".
    """
    from config.token_types import (
        ALL_OPERATOR_TYPES, DELIMITER_TYPES, VALUE_TYPES,
        TT_UNKNOWN, TT_KEYWORD, TT_IDENTIFIER,
        TT_NUMBER, TT_FLOAT, TT_STRING,
    )
    from config.keywords import STRUCTURAL_KEYWORDS

    if token_type in STRUCTURAL_KEYWORDS or token_type == TT_KEYWORD:
        return "Keyword"
    if token_type == TT_IDENTIFIER:
        return "Identifier"
    if token_type in ALL_OPERATOR_TYPES:
        return "Operator"
    if token_type in DELIMITER_TYPES or token_type == TT_ASTERISK:
        return "Delimiter"
    if token_type in (TT_NUMBER, TT_FLOAT, TT_STRING):
        return "Constant"
    if token_type == TT_UNKNOWN:
        return "Unknown"
    return "Keyword"   # Default for unrecognised structural tokens
