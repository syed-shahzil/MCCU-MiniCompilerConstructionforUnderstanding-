"""
ast/visualizer.py
-----------------
Renders any MCCU AST dictionary into:
  1. A plain-text tree string (for diagnostics/info display)
  2. A list of (label, parent_id, node_id) tuples for ttk.Treeview insertion

The visualizer is statement-aware — it knows the shape of each AST type and
renders it with clear, educational labels rather than raw key names.

Example output for SELECT:

    SELECT
    ├── Columns
    │   ├── name
    │   └── age
    ├── FROM  →  students
    └── WHERE
        └── age  >  20
"""

from __future__ import annotations
from typing import Any


# ---------------------------------------------------------------------------
# Tree node dataclass (for Treeview)
# ---------------------------------------------------------------------------

class TreeNode:
    """Represents a single node to be inserted into ttk.Treeview."""
    _counter: int = 0

    def __init__(self, label: str, parent_id: str = "") -> None:
        TreeNode._counter += 1
        self.node_id: str = f"n{TreeNode._counter}"
        self.label: str = label
        self.parent_id: str = parent_id

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_tree_nodes(ast: dict[str, Any]) -> list[TreeNode]:
    """
    Convert an AST dictionary into a flat list of TreeNode objects for
    insertion into ttk.Treeview (parent → child relationships).

    Args:
        ast: AST dictionary with a 'type' key.

    Returns:
        Ordered list of TreeNode objects (root first).
    """
    TreeNode.reset_counter()
    nodes: list[TreeNode] = []
    stmt_type = ast.get("type", "UNKNOWN")

    builder = _BUILDERS.get(stmt_type, _build_generic)
    builder(ast, parent_id="", nodes=nodes)
    return nodes


def render_text_tree(ast: dict[str, Any]) -> str:
    """
    Render the AST as a plain-text tree string using box-drawing characters.

    Args:
        ast: AST dictionary with a 'type' key.

    Returns:
        A multi-line string showing the tree structure.
    """
    lines: list[str] = []
    stmt_type = ast.get("type", "UNKNOWN")
    text_builder = _TEXT_BUILDERS.get(stmt_type, _text_generic)
    text_builder(ast, lines=lines, prefix="", is_last=True)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal tree-building helpers (Treeview)
# ---------------------------------------------------------------------------

def _add(nodes: list[TreeNode], label: str, parent_id: str) -> str:
    """Add a TreeNode and return its ID."""
    n = TreeNode(label=label, parent_id=parent_id)
    nodes.append(n)
    return n.node_id


def _build_select(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, "SELECT", parent_id)

    # Columns or Aggregate
    if "columns" in ast:
        cols_id = _add(nodes, "Columns", root_id)
        for col in ast["columns"]:
            _add(nodes, str(col), cols_id)
    elif "aggregate" in ast:
        agg = ast["aggregate"]
        agg_id = _add(nodes, f"Aggregate  →  {agg['function']}({agg['column']})", root_id)

    # FROM
    _add(nodes, f"FROM  →  {ast.get('table', '?')}", root_id)

    # WHERE
    if "where" in ast:
        w = ast["where"]
        where_id = _add(nodes, "WHERE", root_id)
        _add(nodes, f"{w['column']}  {w['operator']}  {w['value']}", where_id)

    # ORDER BY
    if "order_by" in ast:
        ob = ast["order_by"]
        ob_id = _add(nodes, "ORDER BY", root_id)
        _add(nodes, f"{ob['column']}  {ob['direction']}", ob_id)


def _build_delete(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, "DELETE", parent_id)
    _add(nodes, f"FROM  →  {ast.get('table', '?')}", root_id)
    if "where" in ast:
        w = ast["where"]
        where_id = _add(nodes, "WHERE", root_id)
        _add(nodes, f"{w['column']}  {w['operator']}  {w['value']}", where_id)


def _build_drop(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, "DROP", parent_id)
    _add(nodes, f"Object Type  →  {ast.get('object_type', '?')}", root_id)
    _add(nodes, f"Name  →  {ast.get('name', '?')}", root_id)


def _build_insert(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, "INSERT INTO", parent_id)
    _add(nodes, f"Table  →  {ast.get('table', '?')}", root_id)

    cols_id = _add(nodes, "Columns", root_id)
    for col in ast.get("columns", []):
        _add(nodes, str(col), cols_id)

    vals_id = _add(nodes, "Values", root_id)
    for val in ast.get("values", []):
        _add(nodes, repr(val), vals_id)


def _build_update(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, "UPDATE", parent_id)
    _add(nodes, f"Table  →  {ast.get('table', '?')}", root_id)

    set_id = _add(nodes, "SET", root_id)
    for col, val in ast.get("set", {}).items():
        _add(nodes, f"{col}  =  {val!r}", set_id)

    if "where" in ast:
        w = ast["where"]
        where_id = _add(nodes, "WHERE", root_id)
        _add(nodes, f"{w['column']}  {w['operator']}  {w['value']}", where_id)


def _build_generic(ast: dict[str, Any], parent_id: str, nodes: list[TreeNode]) -> None:
    root_id = _add(nodes, ast.get("type", "UNKNOWN"), parent_id)
    for key, val in ast.items():
        if key == "type":
            continue
        _add(nodes, f"{key}  →  {val!r}", root_id)


_BUILDERS = {
    "SELECT": _build_select,
    "DELETE": _build_delete,
    "DROP":   _build_drop,
    "INSERT": _build_insert,
    "UPDATE": _build_update,
}


# ---------------------------------------------------------------------------
# Internal text-tree helpers (plain string output)
# ---------------------------------------------------------------------------

_BRANCH = "├── "
_LAST   = "└── "
_PIPE   = "│   "
_SPACE  = "    "


def _text_select(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    lines.append(f"{prefix}{'└── ' if is_last else '├── '}SELECT")
    child_prefix = prefix + (_SPACE if is_last else _PIPE)
    children = _select_children(ast)
    for i, (label, sub) in enumerate(children):
        last = (i == len(children) - 1)
        conn = _LAST if last else _BRANCH
        if sub is None:
            lines.append(f"{child_prefix}{conn}{label}")
        else:
            lines.append(f"{child_prefix}{conn}{label}")
            sub_prefix = child_prefix + (_SPACE if last else _PIPE)
            for j, item in enumerate(sub):
                item_last = (j == len(sub) - 1)
                lines.append(f"{sub_prefix}{_LAST if item_last else _BRANCH}{item}")


def _select_children(ast: dict) -> list[tuple[str, list | None]]:
    children = []
    if "columns" in ast:
        children.append(("Columns", ast["columns"]))
    elif "aggregate" in ast:
        agg = ast["aggregate"]
        children.append((f"Aggregate  →  {agg['function']}({agg['column']})", None))
    children.append((f"FROM  →  {ast.get('table', '?')}", None))
    if "where" in ast:
        w = ast["where"]
        children.append(("WHERE", [f"{w['column']}  {w['operator']}  {w['value']}"]))
    if "order_by" in ast:
        ob = ast["order_by"]
        children.append(("ORDER BY", [f"{ob['column']}  ({ob['direction']})"]))
    return children


def _text_delete(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    conn = _LAST if is_last else _BRANCH
    lines.append(f"{prefix}{conn}DELETE")
    p = prefix + (_SPACE if is_last else _PIPE)
    w = ast.get("where", {})
    lines.append(f"{p}{_BRANCH}FROM  →  {ast.get('table', '?')}")
    lines.append(f"{p}{_LAST}WHERE")
    lines.append(f"{p}{_SPACE}{_LAST}{w.get('column','?')}  {w.get('operator','?')}  {w.get('value','?')}")


def _text_drop(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    conn = _LAST if is_last else _BRANCH
    lines.append(f"{prefix}{conn}DROP")
    p = prefix + (_SPACE if is_last else _PIPE)
    lines.append(f"{p}{_BRANCH}Object Type  →  {ast.get('object_type','?')}")
    lines.append(f"{p}{_LAST}Name  →  {ast.get('name','?')}")


def _text_insert(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    conn = _LAST if is_last else _BRANCH
    lines.append(f"{prefix}{conn}INSERT INTO  →  {ast.get('table','?')}")
    p = prefix + (_SPACE if is_last else _PIPE)
    cols = ast.get("columns", [])
    vals = ast.get("values", [])
    lines.append(f"{p}{_BRANCH}Columns  ({len(cols)})")
    for i, c in enumerate(cols):
        lines.append(f"{p}{_PIPE}{_LAST if i==len(cols)-1 else _BRANCH}{c}")
    lines.append(f"{p}{_LAST}Values  ({len(vals)})")
    for i, v in enumerate(vals):
        lines.append(f"{p}{_SPACE}{_LAST if i==len(vals)-1 else _BRANCH}{v!r}")


def _text_update(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    conn = _LAST if is_last else _BRANCH
    lines.append(f"{prefix}{conn}UPDATE  →  {ast.get('table','?')}")
    p = prefix + (_SPACE if is_last else _PIPE)
    set_items = list(ast.get("set", {}).items())
    has_where = "where" in ast
    lines.append(f"{p}{_LAST if not has_where else _BRANCH}SET")
    sp = p + (_SPACE if not has_where else _PIPE)
    for i, (col, val) in enumerate(set_items):
        lines.append(f"{sp}{_LAST if i==len(set_items)-1 else _BRANCH}{col}  =  {val!r}")
    if has_where:
        w = ast["where"]
        lines.append(f"{p}{_LAST}WHERE")
        lines.append(f"{p}{_SPACE}{_LAST}{w['column']}  {w['operator']}  {w['value']}")


def _text_generic(ast: dict, lines: list, prefix: str, is_last: bool) -> None:
    conn = _LAST if is_last else _BRANCH
    lines.append(f"{prefix}{conn}{ast.get('type','UNKNOWN')}")
    p = prefix + (_SPACE if is_last else _PIPE)
    items = [(k, v) for k, v in ast.items() if k != "type"]
    for i, (k, v) in enumerate(items):
        last = (i == len(items) - 1)
        lines.append(f"{p}{_LAST if last else _BRANCH}{k}  →  {v!r}")


_TEXT_BUILDERS = {
    "SELECT": _text_select,
    "DELETE": _text_delete,
    "DROP":   _text_drop,
    "INSERT": _text_insert,
    "UPDATE": _text_update,
}
