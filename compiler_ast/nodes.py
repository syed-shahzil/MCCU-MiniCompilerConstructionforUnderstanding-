"""
ast/nodes.py
------------
Factory functions for all AST node dictionaries used in the MCCU pipeline.

Extends and supersedes m2/ast_nodes.py with support for all five statement
types: SELECT, DELETE, DROP, INSERT, UPDATE.

Every function returns a plain Python dict so the AST can be serialised to
JSON, logged, or handed to downstream modules (visualizer, GUI) without
special class imports.

Keeping node creation centralised here means parsers never build raw dicts
inline, and the shape of each node can be changed in one place.
"""

from __future__ import annotations
from typing import Any


# ===========================================================================
# SELECT nodes
# ===========================================================================

def create_select_ast(
    *,
    table: str,
    columns: list[str] | None = None,
    aggregate: dict[str, str] | None = None,
    where: dict[str, Any] | None = None,
    order_by: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Build the root AST node for a SELECT statement.

    Exactly one of `columns` or `aggregate` must be provided.

    Args:
        table:     Target table name.
        columns:   List of selected column names (may include '*').
        aggregate: Aggregate node from :func:`create_aggregate_node`.
        where:     WHERE condition node from :func:`create_where_node`.
        order_by:  ORDER BY node from :func:`create_order_by_node`.

    Returns:
        dict with key 'type' == 'SELECT'.

    Raises:
        ValueError: If neither or both of columns/aggregate are given.
    """
    if columns is None and aggregate is None:
        raise ValueError("create_select_ast requires either 'columns' or 'aggregate'.")
    if columns is not None and aggregate is not None:
        raise ValueError("Provide only one of 'columns' or 'aggregate' to create_select_ast.")

    node: dict[str, Any] = {"type": "SELECT", "table": table}

    if columns is not None:
        node["columns"] = columns
    else:
        node["aggregate"] = aggregate  # type: ignore[assignment]

    if where is not None:
        node["where"] = where
    if order_by is not None:
        node["order_by"] = order_by

    return node


# ===========================================================================
# DELETE nodes
# ===========================================================================

def create_delete_ast(
    *,
    table: str,
    where: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the root AST node for a DELETE statement.

    Args:
        table: Target table name.
        where: WHERE condition node from :func:`create_where_node`.

    Returns:
        dict with key 'type' == 'DELETE'.
    """
    return {
        "type": "DELETE",
        "table": table,
        "where": where,
    }


# ===========================================================================
# DROP nodes
# ===========================================================================

def create_drop_ast(
    *,
    object_type: str,
    name: str,
) -> dict[str, str]:
    """
    Build the root AST node for a DROP statement.

    Args:
        object_type: "TABLE" or "DATABASE".
        name:        Name of the object being dropped.

    Returns:
        dict with key 'type' == 'DROP'.
    """
    return {
        "type": "DROP",
        "object_type": object_type.upper(),
        "name": name,
    }


# ===========================================================================
# INSERT nodes
# ===========================================================================

def create_insert_ast(
    *,
    table: str,
    columns: list[str],
    values: list[str | int | float],
) -> dict[str, Any]:
    """
    Build the root AST node for an INSERT statement.

    Args:
        table:   Target table name.
        columns: List of column names.
        values:  List of literal values (str, int, or float).

    Returns:
        dict with key 'type' == 'INSERT'.
    """
    return {
        "type": "INSERT",
        "table": table,
        "columns": columns,
        "values": values,
    }


# ===========================================================================
# UPDATE nodes
# ===========================================================================

def create_update_ast(
    *,
    table: str,
    set_clauses: dict[str, str | int | float],
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the root AST node for an UPDATE statement.

    Args:
        table:       Target table name.
        set_clauses: Mapping of column name → new value.
        where:       Optional WHERE condition node.

    Returns:
        dict with key 'type' == 'UPDATE'.
    """
    node: dict[str, Any] = {
        "type": "UPDATE",
        "table": table,
        "set": set_clauses,
    }
    if where is not None:
        node["where"] = where
    return node




# ===========================================================================
# Error / recovery nodes
# ===========================================================================

def create_error_ast(
    *,
    phase: str,
    message: str,
    invalid_tokens: list[dict[str, Any]] | None = None,
    details: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build an AST placeholder for graceful GUI display when compilation fails.

    This does not replace the real AST for valid input. It is only used when
    lexical/syntax errors prevent normal parsing, so the AST panel can still
    show where the pipeline broke instead of going blank.
    """
    return {
        "type": "ERROR",
        "phase": phase,
        "message": message,
        "invalid_tokens": invalid_tokens or [],
        "details": details or [],
    }


# ===========================================================================
# Shared clause nodes
# ===========================================================================

def create_where_node(
    *,
    column: str,
    operator: str,
    value: str | int | float,
) -> dict[str, Any]:
    """
    Build an AST node representing a WHERE condition.

    Args:
        column:   Left-hand-side column name.
        operator: Comparison operator string (e.g. '>', '=', '!=').
        value:    Right-hand-side literal value.

    Returns:
        dict with keys 'column', 'operator', 'value'.
    """
    return {
        "column": column,
        "operator": operator,
        "value": value,
    }


def create_order_by_node(
    *,
    column: str,
    direction: str = "ASC",
) -> dict[str, str]:
    """
    Build an AST node representing an ORDER BY clause.

    Args:
        column:    Column to sort by.
        direction: 'ASC' or 'DESC'. Defaults to 'ASC'.

    Returns:
        dict with keys 'column', 'direction'.
    """
    return {
        "column": column,
        "direction": direction.upper(),
    }


def create_aggregate_node(
    *,
    function: str,
    column: str,
) -> dict[str, str]:
    """
    Build an AST node representing an aggregate function call.

    Args:
        function: Aggregate function name (e.g. 'COUNT', 'AVG').
        column:   Column argument, or '*' for COUNT(*).

    Returns:
        dict with keys 'function', 'column'.
    """
    return {
        "function": function.upper(),
        "column": column,
    }
