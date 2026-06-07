"""
config/constants.py
-------------------
Central store for all shared runtime constants across the MCCU pipeline.

Merges and supersedes:
  - m2/constants.py
  - m3/delete_drop_parser/constants.py

No module should define its own local versions of these values.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Aggregate functions
# ---------------------------------------------------------------------------

AGGREGATE_FUNCTIONS: frozenset[str] = frozenset({
    "COUNT", "SUM", "AVG", "MIN", "MAX",
})

# ---------------------------------------------------------------------------
# Comparison operators (raw string form)
# ---------------------------------------------------------------------------

SUPPORTED_OPERATORS: frozenset[str] = frozenset({
    "=", "!=", "<>", "<", ">", "<=", ">=",
})

# ---------------------------------------------------------------------------
# DROP object types
# ---------------------------------------------------------------------------

DROP_OBJECT_TYPES: frozenset[str] = frozenset({
    "TABLE", "DATABASE",
})

# ---------------------------------------------------------------------------
# ORDER BY directions
# ---------------------------------------------------------------------------

ORDER_DIRECTIONS: frozenset[str] = frozenset({"ASC", "DESC"})
DEFAULT_ORDER_DIRECTION: str = "ASC"

# ---------------------------------------------------------------------------
# Wildcard symbol
# ---------------------------------------------------------------------------

WILDCARD: str = "*"

# ---------------------------------------------------------------------------
# Token value types accepted as literal values in WHERE / VALUES clauses
# (token type strings, not Python types)
# ---------------------------------------------------------------------------

LITERAL_VALUE_TYPES: frozenset[str] = frozenset({
    "NUMBER", "FLOAT", "STRING",
})

# Token types that may appear on the right side of WHERE conditions
WHERE_VALUE_TYPES: frozenset[str] = frozenset({
    "NUMBER", "FLOAT", "STRING", "IDENTIFIER",
})

# ---------------------------------------------------------------------------
# Error & warning codes
# ---------------------------------------------------------------------------

class ErrorCodes:
    """Namespace for diagnostic error/warning code constants."""

    # Lexical errors  (L-prefix)
    L001 = "L001"   # Unknown / illegal character
    L002 = "L002"   # Unclosed string literal
    L003 = "L003"   # Empty query
    L004 = "L004"   # Invalid numeric literal

    # Syntax errors  (S-prefix)
    S001 = "S001"   # Unexpected token
    S002 = "S002"   # Unexpected end of input
    S003 = "S003"   # Missing SELECT keyword
    S004 = "S004"   # Missing FROM keyword
    S005 = "S005"   # Missing table name
    S006 = "S006"   # Empty column list
    S007 = "S007"   # Missing aggregate argument
    S008 = "S008"   # Missing closing parenthesis
    S009 = "S009"   # Unknown aggregate function
    S010 = "S010"   # Invalid WHERE clause
    S011 = "S011"   # Invalid ORDER BY clause
    S012 = "S012"   # Missing DELETE FROM keyword
    S013 = "S013"   # Missing WHERE clause (DELETE)
    S014 = "S014"   # Missing operator
    S015 = "S015"   # Missing value
    S016 = "S016"   # Missing DROP object type
    S017 = "S017"   # Missing object name (DROP)
    S018 = "S018"   # Missing INTO keyword (INSERT)
    S019 = "S019"   # Column/value count mismatch (INSERT)
    S020 = "S020"   # Missing SET keyword (UPDATE)
    S021 = "S021"   # Unsupported statement type
    S022 = "S022"   # Extra tokens after end of statement

    # Warnings  (W-prefix)
    W001 = "W001"   # Redundant whitespace
    W002 = "W002"   # Missing trailing semicolon
    W003 = "W003"   # Keyword used as identifier (case mismatch)

    # Info  (I-prefix)
    I001 = "I001"   # Error recovery applied
    I002 = "I002"   # Unknown character skipped


ERROR_MESSAGES: dict[str, str] = {
    # Lexical
    ErrorCodes.L001: "Unknown character '{char}' at position {pos}",
    ErrorCodes.L002: "Unclosed string literal — missing closing quote",
    ErrorCodes.L003: "Query is empty",
    ErrorCodes.L004: "Invalid numeric literal '{token}'",
    # Syntax
    ErrorCodes.S001: "Unexpected token '{got}' — expected {expected}",
    ErrorCodes.S002: "Unexpected end of input — expected {expected}",
    ErrorCodes.S003: "Expected SELECT keyword at start of query",
    ErrorCodes.S004: "Expected FROM keyword after column list",
    ErrorCodes.S005: "Expected table name (identifier) after FROM",
    ErrorCodes.S006: "Expected at least one column or '*' after SELECT",
    ErrorCodes.S007: "Expected column name or '*' as argument to {func}()",
    ErrorCodes.S008: "Expected ')' after argument in {func}()",
    ErrorCodes.S009: "Unknown aggregate function '{name}'. Supported: COUNT, SUM, AVG, MIN, MAX",
    ErrorCodes.S010: "Invalid WHERE clause — {detail}",
    ErrorCodes.S011: "Invalid ORDER BY clause — {detail}",
    ErrorCodes.S012: "Expected FROM after DELETE",
    ErrorCodes.S013: "DELETE requires a WHERE clause",
    ErrorCodes.S014: "Missing comparison operator in clause",
    ErrorCodes.S015: "Missing value after operator",
    ErrorCodes.S016: "Expected TABLE or DATABASE after DROP",
    ErrorCodes.S017: "Expected object name after DROP {obj_type}",
    ErrorCodes.S018: "Expected INTO after INSERT",
    ErrorCodes.S019: "Column count ({cols}) does not match value count ({vals})",
    ErrorCodes.S020: "Expected SET after table name in UPDATE",
    ErrorCodes.S021: "Unsupported statement type '{stmt}'. Supported: SELECT, INSERT, UPDATE, DELETE, DROP",
    ErrorCodes.S022: "Unexpected token '{token}' after end of statement",
    # Warnings
    ErrorCodes.W001: "Redundant whitespace detected",
    ErrorCodes.W002: "Statement is missing a trailing semicolon",
    ErrorCodes.W003: "Keyword '{word}' used as identifier",
    # Info
    ErrorCodes.I001: "Error recovery applied: {detail}",
    ErrorCodes.I002: "Unknown character '{char}' skipped during recovery",
}
