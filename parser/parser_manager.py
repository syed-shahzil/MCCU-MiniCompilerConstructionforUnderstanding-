"""
parser/parser_manager.py
-------------------------
ParserManager — automatically selects and invokes the correct parser
based on the first token of the typed token stream.

The GUI calls run_parser() and receives a ParseResult. It never needs to
know which parser was used — the manager handles all routing.

Routing table:
    SELECT → SelectParser
    DELETE → DeleteParser
    DROP   → DropParser
    INSERT → InsertParser
    UPDATE → UpdateParser
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Type

from parser.select_parser import SelectParser
from parser.delete_parser import DeleteParser
from parser.drop_parser import DropParser
from parser.insert_update_parser import InsertParser, UpdateParser
from parser.base_parser import BaseParser
from error_handling.exceptions import (
    SQLSyntaxError,
    UnsupportedStatementError,
    MCCUError,
)


# ---------------------------------------------------------------------------
# Parser registry: first-token keyword → parser class
# ---------------------------------------------------------------------------

PARSER_REGISTRY: dict[str, Type[BaseParser]] = {
    "SELECT": SelectParser,
    "DELETE": DeleteParser,
    "DROP":   DropParser,
    "INSERT": InsertParser,
    "UPDATE": UpdateParser,
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    """
    Complete result of the parsing phase.

    Attributes:
        ast:            The parsed AST dictionary, or None on failure.
        statement_type: The SQL statement type (e.g. "SELECT").
        parser_name:    The class name of the parser used.
        error:          Exception instance if parsing failed, else None.
        success:        True if parsing completed without errors.
    """
    ast: dict[str, Any] | None
    statement_type: str
    parser_name: str
    error: Exception | None = None
    success: bool = True

    @property
    def ast_node_count(self) -> int:
        """Rough count of AST nodes (recursive dict values)."""
        if self.ast is None:
            return 0
        return _count_nodes(self.ast)

    def __repr__(self) -> str:
        return (
            f"ParseResult(type={self.statement_type!r}, "
            f"parser={self.parser_name!r}, "
            f"success={self.success}, "
            f"nodes={self.ast_node_count})"
        )


def _count_nodes(obj: Any, depth: int = 0) -> int:
    """Recursively count meaningful nodes in an AST dict."""
    if depth > 10:
        return 1
    if isinstance(obj, dict):
        return 1 + sum(_count_nodes(v, depth + 1) for v in obj.values())
    if isinstance(obj, list):
        return sum(_count_nodes(item, depth + 1) for item in obj)
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_parser(tokens: list[tuple[str, Any]]) -> ParseResult:
    """
    Automatically select and run the appropriate parser for the token stream.

    Args:
        tokens: List of (token_type, token_value) tuples from the lexer.

    Returns:
        A ParseResult containing the AST (or error information).
    """
    if not tokens:
        return ParseResult(
            ast=None,
            statement_type="UNKNOWN",
            parser_name="None",
            error=UnsupportedStatementError("(empty)"),
            success=False,
        )

    first_type = tokens[0][0].upper()
    statement_type = first_type

    parser_class = PARSER_REGISTRY.get(first_type)

    if parser_class is None:
        err = UnsupportedStatementError(stmt=first_type)
        return ParseResult(
            ast=None,
            statement_type=statement_type,
            parser_name="None",
            error=err,
            success=False,
        )

    parser = parser_class(tokens)

    try:
        ast = parser.parse()
        return ParseResult(
            ast=ast,
            statement_type=statement_type,
            parser_name=parser.parser_name,
            success=True,
        )
    except MCCUError as exc:
        return ParseResult(
            ast=None,
            statement_type=statement_type,
            parser_name=parser.parser_name,
            error=exc,
            success=False,
        )
    except Exception as exc:
        return ParseResult(
            ast=None,
            statement_type=statement_type,
            parser_name=parser.parser_name,
            error=exc,
            success=False,
        )


def get_supported_statements() -> list[str]:
    """Return list of supported SQL statement keywords."""
    return list(PARSER_REGISTRY.keys())
