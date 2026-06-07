"""
config/grammar_rules.py
-----------------------
Human-readable grammar rule documentation for each supported SQL statement.

These strings are used by the GUI diagnostics panel and educational displays
to show the user what the expected syntax looks like for a given statement.

Notation:
  - UPPERCASE  = literal SQL keyword
  - lowercase  = user-supplied value
  - [...]      = optional clause
  - (... | ...) = alternatives
  - *          = wildcard
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# BNF-style grammar rules (simplified)
# ---------------------------------------------------------------------------

SELECT_GRAMMAR: str = (
    "SELECT (col1 [, col2 ...] | agg_fn(col | *) | *)\n"
    "FROM   table_name\n"
    "[WHERE  column operator value]\n"
    "[ORDER BY column [ASC | DESC]]\n"
    "[;]"
)

DELETE_GRAMMAR: str = (
    "DELETE FROM table_name\n"
    "WHERE  column operator value\n"
    "[;]"
)

DROP_GRAMMAR: str = (
    "DROP (TABLE | DATABASE) object_name\n"
    "[;]"
)

INSERT_GRAMMAR: str = (
    "INSERT INTO table_name (col1 [, col2 ...])\n"
    "VALUES     (val1  [, val2  ...])\n"
    "[;]"
)

UPDATE_GRAMMAR: str = (
    "UPDATE table_name\n"
    "SET    col1 = val1 [, col2 = val2 ...]\n"
    "[WHERE column operator value]\n"
    "[;]"
)

# ---------------------------------------------------------------------------
# Mapping: first-token keyword → grammar string
# ---------------------------------------------------------------------------

GRAMMAR_MAP: dict[str, str] = {
    "SELECT": SELECT_GRAMMAR,
    "DELETE": DELETE_GRAMMAR,
    "DROP":   DROP_GRAMMAR,
    "INSERT": INSERT_GRAMMAR,
    "UPDATE": UPDATE_GRAMMAR,
}

# ---------------------------------------------------------------------------
# Supported aggregate function signatures (for educational display)
# ---------------------------------------------------------------------------

AGGREGATE_SIGNATURES: dict[str, str] = {
    "COUNT": "COUNT(column | *)",
    "SUM":   "SUM(column)",
    "AVG":   "AVG(column)",
    "MIN":   "MIN(column)",
    "MAX":   "MAX(column)",
}

# ---------------------------------------------------------------------------
# Operator descriptions (for diagnostics panel)
# ---------------------------------------------------------------------------

OPERATOR_DESCRIPTIONS: dict[str, str] = {
    "=":  "Equal to",
    "!=": "Not equal to",
    "<>": "Not equal to (alternative)",
    "<":  "Less than",
    ">":  "Greater than",
    "<=": "Less than or equal to",
    ">=": "Greater than or equal to",
}


def get_grammar(statement_type: str) -> str:
    """
    Return the grammar rule string for a given statement type.

    Args:
        statement_type: e.g. "SELECT", "DELETE"

    Returns:
        A multi-line grammar string, or a generic message if not found.
    """
    return GRAMMAR_MAP.get(
        statement_type.upper(),
        f"No grammar rule defined for statement type '{statement_type}'.",
    )
