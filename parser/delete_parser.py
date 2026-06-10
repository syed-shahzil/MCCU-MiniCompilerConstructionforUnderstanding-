"""
parser/delete_parser.py
------------------------
Parser for SQL DELETE statements.

Refactored from m3/delete_drop_parser/delete_parser.py with:
  - Cursor-based navigation (replaces index-based helpers)
  - Inherits BaseParser (shares _parse_where_clause)
  - Uses unified token standard
  - Proper exception types from error_handling/exceptions.py

Supported syntax:
    DELETE FROM table_name WHERE column op value [;]
"""

from __future__ import annotations
from typing import Any

from parser.base_parser import BaseParser
from compiler_ast.nodes import create_delete_ast
from error_handling.exceptions import (
    MissingDeleteFromError,
    MissingTableNameError,
    MissingWhereClauseError,
)


class DeleteParser(BaseParser):
    """
    Parser for SQL DELETE statements.

    Usage::

        tokens = [
            ("DELETE","DELETE"), ("FROM","FROM"),
            ("IDENTIFIER","students"), ("WHERE","WHERE"),
            ("IDENTIFIER","id"), ("EQ","="), ("NUMBER",5), ("SEMICOLON",";")
        ]
        ast = DeleteParser(tokens).parse()
        # -> {"type":"DELETE","table":"students","where":{"column":"id","operator":"=","value":5}}
    """

    def parse(self) -> dict[str, Any]:
        """Parse DELETE statement and return AST dict."""
        # Consume DELETE keyword
        self._cursor.expect("DELETE", context="DELETE keyword")

        # Consume FROM keyword
        if not self._cursor.match("FROM"):
            raise MissingDeleteFromError(position=self._cursor.position)
        self._cursor.advance()

        # Table name
        if not self._cursor.match("IDENTIFIER"):
            raise MissingTableNameError(position=self._cursor.position)
        table_token = self._cursor.advance()
        table = str(table_token.value)

        # WHERE clause (mandatory for DELETE)
        if not self._cursor.match("WHERE"):
            raise MissingWhereClauseError(position=self._cursor.position)

        where = self._parse_where_clause()

        self._cursor.skip_semicolons()
        self._cursor.ensure_exhausted()

        return create_delete_ast(table=table, where=where)  # type: ignore[arg-type]
