"""
parser/insert_update_parser.py
-------------------------------
Parsers for SQL INSERT and UPDATE statements.

Merged and refactored from m4/insert_parser.py and m4/update_parser.py with:
  - Cursor-based navigation (replaces self.pos integer pointer)
  - Both classes inherit from BaseParser
  - UPDATE shares _parse_where_clause from BaseParser
  - Uses centralized ast/nodes.py factories
  - Proper exception types from error_handling/exceptions.py
  - Full type annotations

Supported syntax:
    INSERT INTO table (col1, col2, ...) VALUES (val1, val2, ...) [;]
    UPDATE table SET col1=val1 [, col2=val2 ...] [WHERE col op val] [;]
"""

from __future__ import annotations
from typing import Any

from parser.base_parser import BaseParser
from compiler_ast.nodes import create_insert_ast, create_update_ast
from config.token_types import COMPARISON_OPERATOR_TYPES, OPERATOR_TYPE_TO_SYMBOL
from error_handling.exceptions import (
    MissingIntoKeywordError,
    MissingTableNameError,
    MissingSetKeywordError,
    ColumnValueMismatchError,
    UnexpectedTokenError,
    UnexpectedEndOfInputError,
    ExtraTokensError,
)


# ---------------------------------------------------------------------------
# INSERT Parser
# ---------------------------------------------------------------------------

class InsertParser(BaseParser):
    """
    Parser for SQL INSERT INTO ... VALUES ... statements.

    Usage::

        tokens = [
            ("INSERT","INSERT"), ("INTO","INTO"),
            ("IDENTIFIER","students"), ("LPAREN","("),
            ("IDENTIFIER","name"), ("COMMA",","), ("IDENTIFIER","age"),
            ("RPAREN",")"), ("VALUES","VALUES"), ("LPAREN","("),
            ("STRING","Ali"), ("COMMA",","), ("NUMBER",20),
            ("RPAREN",")"), ("SEMICOLON",";"),
        ]
        ast = InsertParser(tokens).parse()
    """

    def parse(self) -> dict[str, Any]:
        """Parse INSERT statement and return AST dict."""
        # INSERT keyword
        self._cursor.expect("INSERT", context="INSERT keyword")

        # INTO keyword
        if not self._cursor.match("INTO"):
            raise MissingIntoKeywordError(position=self._cursor.position)
        self._cursor.advance()

        # Table name
        if not self._cursor.match("IDENTIFIER"):
            raise MissingTableNameError(position=self._cursor.position)
        table = str(self._cursor.advance().value)

        # Column list: (col1, col2, ...)
        self._cursor.expect("LPAREN", context="'(' before column list")
        columns = self._parse_identifier_list()
        self._cursor.expect("RPAREN", context="')' after column list")

        # VALUES keyword
        self._cursor.expect("VALUES", context="VALUES keyword")

        # Value list: (val1, val2, ...)
        self._cursor.expect("LPAREN", context="'(' before value list")
        values = self._parse_value_list()
        self._cursor.expect("RPAREN", context="')' after value list")

        # Column / value count check
        if len(columns) != len(values):
            raise ColumnValueMismatchError(
                cols=len(columns),
                vals=len(values),
                position=self._cursor.position,
            )

        self._cursor.skip_semicolons()
        self._cursor.ensure_exhausted()

        return create_insert_ast(table=table, columns=columns, values=values)

    def _parse_identifier_list(self) -> list[str]:
        """Parse comma-separated IDENTIFIER tokens until RPAREN."""
        items: list[str] = []
        while True:
            if self._cursor.is_at_end():
                raise UnexpectedEndOfInputError(expected="identifier or ')'")
            if self._cursor.match("RPAREN"):
                break
            if not self._cursor.match("IDENTIFIER"):
                raise UnexpectedTokenError(
                    expected="column name",
                    got=str(self._cursor.peek_value()),
                    position=self._cursor.position,
                )
            items.append(str(self._cursor.advance().value))
            if self._cursor.match("COMMA"):
                self._cursor.advance()
        return items

    def _parse_value_list(self) -> list[str | int | float]:
        """Parse comma-separated literal value tokens until RPAREN."""
        _VALUE_TYPES = {"NUMBER", "FLOAT", "STRING"}
        items: list[str | int | float] = []
        while True:
            if self._cursor.is_at_end():
                raise UnexpectedEndOfInputError(expected="value or ')'")
            if self._cursor.match("RPAREN"):
                break
            tok = self._cursor.peek()
            if tok.type not in _VALUE_TYPES:
                raise UnexpectedTokenError(
                    expected="a literal value (string, integer, or decimal)",
                    got=str(tok.value),
                    position=self._cursor.position,
                )
            items.append(self._cursor.advance().value)
            if self._cursor.match("COMMA"):
                self._cursor.advance()
        return items


# ---------------------------------------------------------------------------
# UPDATE Parser
# ---------------------------------------------------------------------------

class UpdateParser(BaseParser):
    """
    Parser for SQL UPDATE ... SET ... [WHERE ...] statements.

    Usage::

        tokens = [
            ("UPDATE","UPDATE"), ("IDENTIFIER","students"),
            ("SET","SET"), ("IDENTIFIER","age"), ("EQ","="),
            ("NUMBER",21), ("WHERE","WHERE"), ("IDENTIFIER","id"),
            ("EQ","="), ("NUMBER",5), ("SEMICOLON",";"),
        ]
        ast = UpdateParser(tokens).parse()
    """

    def parse(self) -> dict[str, Any]:
        """Parse UPDATE statement and return AST dict."""
        # UPDATE keyword
        self._cursor.expect("UPDATE", context="UPDATE keyword")

        # Table name
        if not self._cursor.match("IDENTIFIER"):
            raise MissingTableNameError(position=self._cursor.position)
        table = str(self._cursor.advance().value)

        # SET keyword
        if not self._cursor.match("SET"):
            raise MissingSetKeywordError(position=self._cursor.position)
        self._cursor.advance()

        # SET assignments: col = val [, col = val ...]
        set_clauses = self._parse_set_clauses()

        # Optional WHERE clause (from BaseParser)
        where = self._parse_where_clause()

        self._cursor.skip_semicolons()
        self._cursor.ensure_exhausted()

        return create_update_ast(table=table, set_clauses=set_clauses, where=where)

    def _parse_set_clauses(self) -> dict[str, str | int | float]:
        """Parse one or more col = val assignments separated by commas."""
        _VALUE_TYPES = {"NUMBER", "FLOAT", "STRING"}
        assignments: dict[str, str | int | float] = {}

        while True:
            # Column name
            if not self._cursor.match("IDENTIFIER"):
                raise UnexpectedTokenError(
                    expected="column name",
                    got=str(self._cursor.peek_value()),
                    position=self._cursor.position,
                )
            col = str(self._cursor.advance().value)

            # = operator
            tok = self._cursor.peek()
            if tok.type not in COMPARISON_OPERATOR_TYPES and tok.type != "EQ":
                raise UnexpectedTokenError(
                    expected="'=' after column name",
                    got=str(tok.value),
                    position=self._cursor.position,
                )
            self._cursor.advance()  # consume operator

            # Value
            val_tok = self._cursor.peek()
            if val_tok.type not in _VALUE_TYPES:
                raise UnexpectedTokenError(
                    expected="a literal value after '='",
                    got=str(val_tok.value),
                    position=self._cursor.position,
                )
            assignments[col] = self._cursor.advance().value

            # Continue if comma follows (and next is not WHERE / end)
            if self._cursor.match("COMMA"):
                self._cursor.advance()
                # After comma, expect another identifier
                if self._cursor.match("WHERE") or self._cursor.is_at_end():
                    break
            else:
                break

        return assignments
