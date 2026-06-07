"""
parser/base_parser.py
---------------------
Abstract base class for all MCCU SQL parsers.

Every concrete parser (SelectParser, DeleteParser, etc.) inherits from
BaseParser and must implement the parse() method. The base class owns
the TokenCursor and provides common utilities shared across parsers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from parser.cursor import TokenCursor
from config.token_types import OPERATOR_TYPE_TO_SYMBOL
from config.constants import WHERE_VALUE_TYPES


class BaseParser(ABC):
    """
    Abstract base for all SQL statement parsers.

    Subclasses receive a list of typed token tuples from the lexer pipeline
    and are responsible for producing a structured AST dictionary.

    Args:
        tokens: List of (token_type, token_value) tuples.
    """

    def __init__(self, tokens: list[tuple[str, Any]]) -> None:
        self._cursor: TokenCursor = TokenCursor(tokens)

    @abstractmethod
    def parse(self) -> dict[str, Any]:
        """
        Parse the token stream and return an AST dictionary.

        Returns:
            AST dict with at minimum the key 'type'.

        Raises:
            SQLSyntaxError (or subclass): On any syntactic violation.
        """
        ...

    # ------------------------------------------------------------------
    # Shared parsing utilities available to all subclasses
    # ------------------------------------------------------------------

    def _parse_where_clause(self) -> dict[str, Any] | None:
        """
        Optionally parse a WHERE clause.  Returns None if no WHERE token.

        Shared by SelectParser, DeleteParser, UpdateParser.

        Returns:
            A where-node dict, or None.

        Raises:
            InvalidWhereClauseError: If the clause is malformed.
            MissingOperatorError:    If no valid operator follows the column.
            MissingValueError:       If no value follows the operator.
        """
        from error_handling.exceptions import InvalidWhereClauseError
        from ast.nodes import create_where_node
        from config.token_types import COMPARISON_OPERATOR_TYPES

        if not self._cursor.match("WHERE"):
            return None

        self._cursor.advance()  # consume WHERE

        # Column name
        col_token = self._cursor.peek()
        if col_token.type != "IDENTIFIER":
            raise InvalidWhereClauseError(
                detail=f"expected column name, got '{col_token.value}'",
                position=self._cursor.position,
            )
        self._cursor.advance()
        column = str(col_token.value)

        # Operator
        op_token = self._cursor.peek()
        if op_token.type not in COMPARISON_OPERATOR_TYPES:
            raise InvalidWhereClauseError(
                detail=f"expected a comparison operator, got '{op_token.value}'",
                position=self._cursor.position,
            )
        self._cursor.advance()
        operator = OPERATOR_TYPE_TO_SYMBOL.get(op_token.type, str(op_token.value))

        # Value
        val_token = self._cursor.peek()
        if val_token.type not in WHERE_VALUE_TYPES:
            raise InvalidWhereClauseError(
                detail=f"expected a value after operator, got '{val_token.value}'",
                position=self._cursor.position,
            )
        self._cursor.advance()
        raw_value = val_token.value
        value: str | int | float = (
            int(raw_value)
            if isinstance(raw_value, str) and raw_value.isdigit()
            else raw_value
        )

        return create_where_node(column=column, operator=operator, value=value)

    @property
    def parser_name(self) -> str:
        """Return the class name of this parser."""
        return self.__class__.__name__
