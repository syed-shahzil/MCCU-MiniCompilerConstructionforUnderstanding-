"""
parser/drop_parser.py
----------------------
Parser for SQL DROP statements.

Refactored from m3/delete_drop_parser/drop_parser.py with:
  - Cursor-based navigation (replaces index-based helpers)
  - Inherits BaseParser
  - Uses centralized DROP_OBJECT_TYPES from config/constants.py

Supported syntax:
    DROP (TABLE | DATABASE) object_name [;]
"""

from __future__ import annotations
from typing import Any

from parser.base_parser import BaseParser
from ast.nodes import create_drop_ast
from config.constants import DROP_OBJECT_TYPES
from error_handling.exceptions import (
    MissingDropObjectTypeError,
    MissingObjectNameError,
    ExtraTokensError,
)


class DropParser(BaseParser):
    """
    Parser for SQL DROP statements.

    Usage::

        tokens = [("DROP","DROP"), ("TABLE","TABLE"),
                  ("IDENTIFIER","students"), ("SEMICOLON",";")]
        ast = DropParser(tokens).parse()
        # -> {"type":"DROP","object_type":"TABLE","name":"students"}
    """

    def parse(self) -> dict[str, Any]:
        """Parse DROP statement and return AST dict."""
        # Consume DROP keyword
        self._cursor.expect("DROP", context="DROP keyword")

        # Object type: TABLE or DATABASE
        object_type = self._parse_object_type()

        # Object name
        if not self._cursor.match("IDENTIFIER"):
            raise MissingObjectNameError(
                obj_type=object_type,
                position=self._cursor.position,
            )
        name_token = self._cursor.advance()
        name = str(name_token.value)

        self._cursor.skip_semicolons()
        self._cursor.ensure_exhausted()

        return create_drop_ast(object_type=object_type, name=name)

    def _parse_object_type(self) -> str:
        """
        Parse and return the object type keyword (TABLE or DATABASE).

        Raises:
            MissingDropObjectTypeError: If next token is neither TABLE nor DATABASE.
        """
        token = self._cursor.peek()
        token_upper = str(token.value).upper()

        # Accept either as own token type or as IDENTIFIER with matching value
        if token.type in DROP_OBJECT_TYPES or token_upper in DROP_OBJECT_TYPES:
            self._cursor.advance()
            return token_upper

        # Also accept keyword type match
        if token.type == "KEYWORD" and token_upper in DROP_OBJECT_TYPES:
            self._cursor.advance()
            return token_upper

        raise MissingDropObjectTypeError(position=self._cursor.position)
