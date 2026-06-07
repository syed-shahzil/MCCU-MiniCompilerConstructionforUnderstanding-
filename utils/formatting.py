"""
utils/formatting.py
--------------------
Miscellaneous text formatting helpers used by the GUI and diagnostics layers.
"""

from __future__ import annotations


def truncate(text: str, max_len: int = 40, ellipsis: str = "…") -> str:
    """Truncate *text* to *max_len* characters, appending *ellipsis* if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(ellipsis)] + ellipsis


def pad_right(text: str, width: int) -> str:
    """Right-pad *text* with spaces to exactly *width* characters."""
    return text.ljust(width)


def format_position(position: int | None) -> str:
    """Format a token/char position for user-friendly display."""
    if position is None:
        return "—"
    return f"pos {position}"


def statement_label(stmt_type: str) -> str:
    """Return a human-readable label for a SQL statement type."""
    labels = {
        "SELECT": "SELECT Query",
        "INSERT": "INSERT Statement",
        "UPDATE": "UPDATE Statement",
        "DELETE": "DELETE Statement",
        "DROP":   "DROP Statement",
    }
    return labels.get(stmt_type.upper(), stmt_type.upper())


def status_summary(success: bool, error_count: int, warning_count: int) -> str:
    """Return a one-line compilation status summary string."""
    if success and error_count == 0 and warning_count == 0:
        return "✔  Compilation successful — no errors or warnings"
    if success and warning_count > 0:
        return f"⚠  Successful with {warning_count} warning(s)"
    return f"✖  Failed — {error_count} error(s), {warning_count} warning(s)"
