"""
parser/select_parser.py
------------------------
Parser for SQL SELECT statements.

Refactored from m2/select_parser.py with:
  - Updated imports to use new project structure
  - Inherits from BaseParser (shares WHERE clause parsing)
  - Uses centralized ast/nodes.py factories
  - Uses centralized error_handling/exceptions.py

Supported syntax:
    SELECT col1 [, col2 ...] | agg_fn(col|*) | *
    FROM   table_name
    [WHERE  column op value]
    [ORDER BY column [ASC|DESC]]
    [;]
"""

from __future__ import annotations
from typing import Any

from parser.base_parser import BaseParser
from ast.nodes import (
    create_select_ast,
    create_order_by_node,
    create_aggregate_node,
)
from config.constants import (
    AGGREGATE_FUNCTIONS,
    ORDER_DIRECTIONS,
    DEFAULT_ORDER_DIRECTION,
    WILDCARD,
)
from config.token_types import OPERATOR_TYPE_TO_SYMBOL, COMPARISON_OPERATOR_TYPES
from error_handling.exceptions import (
    EmptyColumnListError,
    InvalidOrderByClauseError,
    InvalidWhereClauseError,
    MissingAggregateArgumentError,
    MissingClosingParenError,
    MissingFromClauseError,
    MissingTableNameError,
    UnexpectedEndOfInputError,
    UnexpectedTokenError,
    UnknownAggregateFunctionError,
)


class SelectParser(BaseParser):
    """
    Parser for SQL SELECT statements.

    Usage::

        tokens = [("SELECT","SELECT"), ("IDENTIFIER","name"),
                  ("FROM","FROM"), ("IDENTIFIER","students"), ("SEMICOLON",";")]
        ast = SelectParser(tokens).parse()
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> dict[str, Any]:
        """Parse SELECT statement and return AST dict."""
        self._expect_select_keyword()
        columns, aggregate = self._parse_select_list()
        table = self._parse_from_clause()
        where = self._parse_where_clause()
        order_by = self._parse_order_by_clause()
        self._cursor.skip_semicolons()

        return create_select_ast(
            table=table,
            columns=columns,
            aggregate=aggregate,
            where=where,
            order_by=order_by,
        )

    # ------------------------------------------------------------------
    # Clause parsers
    # ------------------------------------------------------------------

    def _expect_select_keyword(self) -> None:
        self._cursor.expect("SELECT", context="SELECT keyword at start of query")

    def _parse_select_list(self) -> tuple[list[str] | None, dict[str, str] | None]:
        """Parse column list or aggregate function after SELECT."""
        if self._cursor.is_at_end():
            raise EmptyColumnListError(position=self._cursor.position)

        current = self._cursor.peek()

        # SELECT * ...
        if current.type == "ASTERISK":
            self._cursor.advance()
            return ([WILDCARD], None)

        # SELECT agg_fn(...) ...
        if self._is_aggregate_identifier():
            aggregate = self._parse_aggregate_function()
            return (None, aggregate)

        # SELECT col1, col2, ...
        if current.type == "IDENTIFIER":
            columns = self._parse_column_list()
            return (columns, None)

        raise EmptyColumnListError(position=self._cursor.position)

    def _parse_column_list(self) -> list[str]:
        """Parse a comma-separated list of column identifiers."""
        columns: list[str] = []

        while True:
            token = self._cursor.peek()
            if token.type == "IDENTIFIER":
                self._cursor.advance()
                columns.append(str(token.value))
            elif token.type == "ASTERISK":
                self._cursor.advance()
                columns.append(WILDCARD)
            else:
                raise UnexpectedTokenError(
                    expected="column name or '*'",
                    got=str(token.value),
                    position=self._cursor.position,
                )

            if self._cursor.match("COMMA"):
                self._cursor.advance()
                continue
            break

        if not columns:
            raise EmptyColumnListError(position=self._cursor.position)
        return columns

    def _parse_aggregate_function(self) -> dict[str, str]:
        """Parse an aggregate function call: FUNC(column) or FUNC(*)."""
        func_token = self._cursor.advance()
        func_name = str(func_token.value).upper()

        if func_name not in AGGREGATE_FUNCTIONS:
            raise UnknownAggregateFunctionError(name=func_name, position=self._cursor.position - 1)

        self._cursor.expect("LPAREN", context=f"'(' after {func_name}")

        arg_token = self._cursor.peek()
        if arg_token.type == "ASTERISK":
            self._cursor.advance()
            column = WILDCARD
        elif arg_token.type == "IDENTIFIER":
            self._cursor.advance()
            column = str(arg_token.value)
        else:
            raise MissingAggregateArgumentError(func=func_name, position=self._cursor.position)

        if not self._cursor.match("RPAREN"):
            raise MissingClosingParenError(func=func_name, position=self._cursor.position)
        self._cursor.advance()

        return create_aggregate_node(function=func_name, column=column)

    def _parse_from_clause(self) -> str:
        """Parse FROM clause and return the table name."""
        if not self._cursor.match("FROM"):
            raise MissingFromClauseError(position=self._cursor.position)
        self._cursor.advance()  # consume FROM

        if self._cursor.is_at_end() or not self._cursor.match("IDENTIFIER"):
            raise MissingTableNameError(position=self._cursor.position)

        table_token = self._cursor.advance()
        return str(table_token.value)

    def _parse_order_by_clause(self) -> dict[str, str] | None:
        """Optionally parse an ORDER BY clause."""
        if not self._cursor.match("ORDER"):
            return None
        self._cursor.advance()  # consume ORDER

        if not self._cursor.match("BY"):
            raise InvalidOrderByClauseError(
                detail="expected BY after ORDER",
                position=self._cursor.position,
            )
        self._cursor.advance()  # consume BY

        col_token = self._cursor.peek()
        if col_token.type != "IDENTIFIER":
            raise InvalidOrderByClauseError(
                detail=f"expected column name after ORDER BY, got '{col_token.value}'",
                position=self._cursor.position,
            )
        self._cursor.advance()
        column = str(col_token.value)

        direction = DEFAULT_ORDER_DIRECTION
        dir_token = self._cursor.peek()
        if dir_token.type in ("ASC", "DESC") or (
            dir_token.type == "IDENTIFIER"
            and str(dir_token.value).upper() in ORDER_DIRECTIONS
        ):
            self._cursor.advance()
            direction = str(dir_token.value).upper()

        return create_order_by_node(column=column, direction=direction)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_aggregate_identifier(self) -> bool:
        """True when current token looks like an aggregate function call."""
        current = self._cursor.peek()
        if current.type != "IDENTIFIER":
            return False
        if str(current.value).upper() not in AGGREGATE_FUNCTIONS:
            return False
        next_token = self._cursor.lookahead(1)
        return next_token.type == "LPAREN"
