"""
error_handling/exceptions.py
-----------------------------
Complete exception hierarchy for the MCCU compiler pipeline.

Extends and supersedes m2/exceptions.py, adding exception classes for all
statement types (DELETE, DROP, INSERT, UPDATE) and lexical errors.

All parser exceptions inherit from SQLSyntaxError to allow broad catches,
while preserving fine-grained specificity via subclasses.

Error code constants (L001, S001, etc.) are defined in config/constants.py.
"""

from __future__ import annotations


# ===========================================================================
# Base Exceptions
# ===========================================================================

class MCCUError(Exception):
    """Root exception for all MCCU compiler errors."""

    def __init__(self, message: str, code: str = "", position: int | None = None) -> None:
        self.code: str = code
        self.position: int | None = position
        location = f" at position {position}" if position is not None else ""
        prefix = f"[{code}] " if code else ""
        super().__init__(f"{prefix}{message}{location}")


# ===========================================================================
# Lexical Exceptions
# ===========================================================================

class SQLLexicalError(MCCUError):
    """Raised for errors detected during lexical analysis."""

    def __init__(
        self,
        message: str,
        code: str = "L001",
        position: int | None = None,
        char: str = "",
    ) -> None:
        self.char = char
        super().__init__(message, code=code, position=position)


class EmptyQueryError(SQLLexicalError):
    """Raised when the input query is empty."""

    def __init__(self) -> None:
        super().__init__("Query is empty", code="L003", position=0)


class UnclosedStringError(SQLLexicalError):
    """Raised when a string literal is missing its closing quote."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Unclosed string literal — missing closing quote",
            code="L002",
            position=position,
        )


class IllegalCharacterError(SQLLexicalError):
    """Raised when an illegal character is encountered (without recovery)."""

    def __init__(self, char: str, position: int | None = None) -> None:
        super().__init__(
            f"Illegal character '{char}'",
            code="L001",
            position=position,
            char=char,
        )


# ===========================================================================
# Syntax Exceptions — Base
# ===========================================================================

class SQLSyntaxError(MCCUError):
    """
    Base exception for all SQL syntax errors.

    All parser-specific exceptions inherit from this class so that callers
    can catch SQLSyntaxError broadly or specific subclasses precisely.
    """

    def __init__(self, message: str, code: str = "S001", position: int | None = None) -> None:
        super().__init__(message, code=code, position=position)


class UnexpectedTokenError(SQLSyntaxError):
    """Raised when the parser encounters an unexpected token."""

    def __init__(self, expected: str, got: str, position: int | None = None) -> None:
        super().__init__(
            f"Expected {expected}, but got '{got}'",
            code="S001",
            position=position,
        )
        self.expected = expected
        self.got = got


class UnexpectedEndOfInputError(SQLSyntaxError):
    """Raised when the token stream ends prematurely."""

    def __init__(self, expected: str, position: int | None = None) -> None:
        super().__init__(
            f"Unexpected end of input — expected {expected}",
            code="S002",
            position=position,
        )
        self.expected = expected


class UnsupportedStatementError(SQLSyntaxError):
    """Raised when the first token does not begin a supported statement."""

    def __init__(self, stmt: str, position: int | None = None) -> None:
        super().__init__(
            f"Unsupported statement type '{stmt}'. "
            "Supported: SELECT, INSERT, UPDATE, DELETE, DROP",
            code="S021",
            position=position,
        )


class ExtraTokensError(SQLSyntaxError):
    """Raised when unexpected tokens appear after the end of a statement."""

    def __init__(self, token: str, position: int | None = None) -> None:
        super().__init__(
            f"Unexpected token '{token}' after end of statement",
            code="S022",
            position=position,
        )


# ===========================================================================
# SELECT-specific Syntax Exceptions
# ===========================================================================

class EmptyColumnListError(SQLSyntaxError):
    """Raised when no columns are specified after SELECT."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Expected at least one column or '*' after SELECT",
            code="S006",
            position=position,
        )


class MissingFromClauseError(SQLSyntaxError):
    """Raised when FROM keyword is missing after the column list."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Expected FROM keyword after column list",
            code="S004",
            position=position,
        )


class MissingTableNameError(SQLSyntaxError):
    """Raised when no table identifier follows FROM."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Expected table name (identifier) after FROM",
            code="S005",
            position=position,
        )


class MissingAggregateArgumentError(SQLSyntaxError):
    """Raised when an aggregate function has no valid argument."""

    def __init__(self, func: str, position: int | None = None) -> None:
        super().__init__(
            f"Expected column name or '*' as argument to {func}()",
            code="S007",
            position=position,
        )
        self.func = func


class MissingClosingParenError(SQLSyntaxError):
    """Raised when a closing parenthesis is absent after an aggregate argument."""

    def __init__(self, func: str, position: int | None = None) -> None:
        super().__init__(
            f"Expected ')' after argument in {func}()",
            code="S008",
            position=position,
        )
        self.func = func


class UnknownAggregateFunctionError(SQLSyntaxError):
    """Raised when an unrecognised aggregate function name is encountered."""

    def __init__(self, name: str, position: int | None = None) -> None:
        super().__init__(
            f"Unknown aggregate function '{name}'. "
            "Supported functions: COUNT, SUM, AVG, MIN, MAX",
            code="S009",
            position=position,
        )
        self.name = name


class InvalidWhereClauseError(SQLSyntaxError):
    """Raised when the WHERE clause is malformed."""

    def __init__(self, detail: str, position: int | None = None) -> None:
        super().__init__(
            f"Invalid WHERE clause — {detail}",
            code="S010",
            position=position,
        )


class InvalidOrderByClauseError(SQLSyntaxError):
    """Raised when the ORDER BY clause is malformed."""

    def __init__(self, detail: str, position: int | None = None) -> None:
        super().__init__(
            f"Invalid ORDER BY clause — {detail}",
            code="S011",
            position=position,
        )


# ===========================================================================
# DELETE-specific Syntax Exceptions
# ===========================================================================

class MissingDeleteFromError(SQLSyntaxError):
    """Raised when FROM keyword is missing after DELETE."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__("Expected FROM after DELETE", code="S012", position=position)


class MissingWhereClauseError(SQLSyntaxError):
    """Raised when DELETE statement has no WHERE clause."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "DELETE requires a WHERE clause to avoid deleting all rows",
            code="S013",
            position=position,
        )


class MissingOperatorError(SQLSyntaxError):
    """Raised when a comparison operator is missing in a condition."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__("Missing comparison operator in clause", code="S014", position=position)


class MissingValueError(SQLSyntaxError):
    """Raised when a value is missing after an operator."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__("Missing value after operator", code="S015", position=position)


# ===========================================================================
# DROP-specific Syntax Exceptions
# ===========================================================================

class MissingDropObjectTypeError(SQLSyntaxError):
    """Raised when TABLE or DATABASE keyword is missing after DROP."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Expected TABLE or DATABASE after DROP",
            code="S016",
            position=position,
        )


class MissingObjectNameError(SQLSyntaxError):
    """Raised when the object name is missing after DROP TABLE/DATABASE."""

    def __init__(self, obj_type: str = "", position: int | None = None) -> None:
        label = f"DROP {obj_type}" if obj_type else "DROP"
        super().__init__(
            f"Expected object name after {label}",
            code="S017",
            position=position,
        )


# ===========================================================================
# INSERT-specific Syntax Exceptions
# ===========================================================================

class MissingIntoKeywordError(SQLSyntaxError):
    """Raised when INTO keyword is missing after INSERT."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__("Expected INTO after INSERT", code="S018", position=position)


class ColumnValueMismatchError(SQLSyntaxError):
    """Raised when INSERT column count differs from value count."""

    def __init__(self, cols: int, vals: int, position: int | None = None) -> None:
        super().__init__(
            f"Column count ({cols}) does not match value count ({vals})",
            code="S019",
            position=position,
        )
        self.cols = cols
        self.vals = vals


# ===========================================================================
# UPDATE-specific Syntax Exceptions
# ===========================================================================

class MissingSetKeywordError(SQLSyntaxError):
    """Raised when SET keyword is missing after table name in UPDATE."""

    def __init__(self, position: int | None = None) -> None:
        super().__init__(
            "Expected SET after table name in UPDATE",
            code="S020",
            position=position,
        )
