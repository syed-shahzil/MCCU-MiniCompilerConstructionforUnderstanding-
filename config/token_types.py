"""
config/token_types.py
---------------------
Single source of truth for all token type string constants used throughout
the MCCU pipeline. Every module imports from here instead of hardcoding strings.

Token type naming convention:
  - Keywords use their SQL name:  "SELECT", "FROM", "WHERE", etc.
  - Operators use short names:    "EQ", "NEQ", "LT", "GT", "LTE", "GTE"
  - Punctuation uses descriptive: "COMMA", "SEMICOLON", "LPAREN", etc.
  - Values use category names:    "IDENTIFIER", "NUMBER", "FLOAT", "STRING"
  - Special:                      "ASTERISK", "DOT", "EOF", "UNKNOWN"
"""

# ---------------------------------------------------------------------------
# SQL Keyword token types
# ---------------------------------------------------------------------------
TT_SELECT   = "SELECT"
TT_INSERT   = "INSERT"
TT_UPDATE   = "UPDATE"
TT_DELETE   = "DELETE"
TT_DROP     = "DROP"
TT_CREATE   = "CREATE"
TT_ALTER    = "ALTER"

TT_FROM     = "FROM"
TT_INTO     = "INTO"
TT_WHERE    = "WHERE"
TT_SET      = "SET"
TT_VALUES   = "VALUES"
TT_TABLE    = "TABLE"
TT_DATABASE = "DATABASE"

TT_ORDER    = "ORDER"
TT_BY       = "BY"
TT_ASC      = "ASC"
TT_DESC     = "DESC"

TT_AND      = "AND"
TT_OR       = "OR"
TT_NOT      = "NOT"
TT_AS       = "AS"
TT_DISTINCT = "DISTINCT"
TT_NULL     = "NULL"
TT_IS       = "IS"
TT_IN       = "IN"
TT_LIKE     = "LIKE"
TT_BETWEEN  = "BETWEEN"

# ---------------------------------------------------------------------------
# Value-carrying token types
# ---------------------------------------------------------------------------
TT_IDENTIFIER = "IDENTIFIER"   # e.g. table names, column names
TT_NUMBER     = "NUMBER"       # integer literals: 42
TT_FLOAT      = "FLOAT"        # floating-point literals: 3.14
TT_STRING     = "STRING"       # quoted string literals: 'Alice'

# ---------------------------------------------------------------------------
# Operator token types (typed, not generic "OPERATOR")
# ---------------------------------------------------------------------------
TT_EQ  = "EQ"    # =
TT_NEQ = "NEQ"   # != or <>
TT_LT  = "LT"    # <
TT_GT  = "GT"    # >
TT_LTE = "LTE"   # <=
TT_GTE = "GTE"   # >=

# Arithmetic operators (classified as OPERATOR category in display)
TT_PLUS  = "PLUS"   # +
TT_MINUS = "MINUS"  # -
TT_MUL   = "MUL"    # * (when used as multiply, not SELECT *)
TT_DIV   = "DIV"    # /
TT_MOD   = "MOD"    # %

# ---------------------------------------------------------------------------
# Punctuation / delimiter token types
# ---------------------------------------------------------------------------
TT_COMMA     = "COMMA"      # ,
TT_SEMICOLON = "SEMICOLON"  # ;
TT_LPAREN    = "LPAREN"     # (
TT_RPAREN    = "RPAREN"     # )
TT_LBRACKET  = "LBRACKET"   # [
TT_RBRACKET  = "RBRACKET"   # ]
TT_DOT       = "DOT"        # .
TT_ASTERISK  = "ASTERISK"   # * (SELECT * usage)

# ---------------------------------------------------------------------------
# Special token types
# ---------------------------------------------------------------------------
TT_EOF     = "EOF"      # end-of-stream sentinel
TT_UNKNOWN = "UNKNOWN"  # illegal/unrecognised character (error recovery)
TT_KEYWORD = "KEYWORD"  # generic keyword catch-all (used in display layer)

# ---------------------------------------------------------------------------
# Display category names (used by GUI token table)
# ---------------------------------------------------------------------------
CAT_KEYWORD    = "Keyword"
CAT_IDENTIFIER = "Identifier"
CAT_OPERATOR   = "Operator"
CAT_DELIMITER  = "Delimiter"
CAT_CONSTANT   = "Constant"
CAT_UNKNOWN    = "Unknown"

# ---------------------------------------------------------------------------
# Operator token types as a set (for fast membership tests)
# ---------------------------------------------------------------------------
COMPARISON_OPERATOR_TYPES: frozenset[str] = frozenset({
    TT_EQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE,
})

ARITHMETIC_OPERATOR_TYPES: frozenset[str] = frozenset({
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_MOD,
})

ALL_OPERATOR_TYPES: frozenset[str] = COMPARISON_OPERATOR_TYPES | ARITHMETIC_OPERATOR_TYPES

# ---------------------------------------------------------------------------
# Delimiter token types as a set
# ---------------------------------------------------------------------------
DELIMITER_TYPES: frozenset[str] = frozenset({
    TT_COMMA, TT_SEMICOLON, TT_LPAREN, TT_RPAREN,
    TT_LBRACKET, TT_RBRACKET, TT_DOT,
})

# ---------------------------------------------------------------------------
# Value token types as a set
# ---------------------------------------------------------------------------
VALUE_TYPES: frozenset[str] = frozenset({
    TT_NUMBER, TT_FLOAT, TT_STRING, TT_IDENTIFIER,
})

# ---------------------------------------------------------------------------
# Mapping: raw operator string → token type
# ---------------------------------------------------------------------------
OPERATOR_SYMBOL_TO_TYPE: dict[str, str] = {
    "=":  TT_EQ,
    "!=": TT_NEQ,
    "<>": TT_NEQ,
    "<":  TT_LT,
    ">":  TT_GT,
    "<=": TT_LTE,
    ">=": TT_GTE,
    "+":  TT_PLUS,
    "-":  TT_MINUS,
    "/":  TT_DIV,
    "%":  TT_MOD,
}

# ---------------------------------------------------------------------------
# Mapping: operator token type → display string
# ---------------------------------------------------------------------------
OPERATOR_TYPE_TO_SYMBOL: dict[str, str] = {
    TT_EQ:    "=",
    TT_NEQ:   "!=",
    TT_LT:    "<",
    TT_GT:    ">",
    TT_LTE:   "<=",
    TT_GTE:   ">=",
    TT_PLUS:  "+",
    TT_MINUS: "-",
    TT_MUL:   "*",
    TT_DIV:   "/",
    TT_MOD:   "%",
}
