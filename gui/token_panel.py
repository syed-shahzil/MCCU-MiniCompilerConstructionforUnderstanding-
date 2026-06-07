"""
gui/token_panel.py
------------------
TokenPanel — a ttk.Treeview-based table widget that displays the classified
token stream in a structured, color-coded tabular format.

Columns: #  |  Lexeme  |  Token Type  |  Category
Row colors map to the token's category (keyword=purple, identifier=cyan, etc.)
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui.styles import Colors, Fonts, CATEGORY_COLORS


class TokenPanel(ttk.Frame):
    """
    Displays the token stream as a styled, scrollable table.

    Args:
        parent: Parent widget.
    """

    COLUMNS = ("#", "Lexeme", "Token Type", "Category")
    COL_WIDTHS = (50, 180, 160, 120)

    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(parent, style="TFrame", **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        # Header label
        hdr = ttk.Label(
            self,
            text="  Token Stream",
            style="Heading.TLabel",
            padding=(0, 6, 0, 6),
        )
        hdr.pack(fill="x", padx=2, pady=(0, 4))

        # Table container
        table_frame = ttk.Frame(self, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Treeview
        self._tree = ttk.Treeview(
            table_frame,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
            style="Treeview",
        )

        # Configure columns
        for col, width in zip(self.COLUMNS, self.COL_WIDTHS):
            self._tree.heading(col, text=col, anchor="w")
            self._tree.column(col, width=width, anchor="w", minwidth=40)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Configure category color tags
        for cat, color in CATEGORY_COLORS.items():
            self._tree.tag_configure(f"cat_{cat}", foreground=color)

        # Alternating row tags
        self._tree.tag_configure("odd",  background=Colors.ROW_ODD)
        self._tree.tag_configure("even", background=Colors.ROW_EVEN)

        # Token count footer
        self._footer_var = tk.StringVar(value="No tokens")
        footer = ttk.Label(
            self,
            textvariable=self._footer_var,
            style="Muted.TLabel",
            padding=(6, 2),
        )
        footer.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, rows: list[tuple[int, str, str, str]]) -> None:
        """
        Fill the table with token data.

        Args:
            rows: List of (position, lexeme, token_type, category) tuples
                  as returned by LexerResult.get_display_rows().
        """
        self.clear()
        for i, (pos, lexeme, tt, cat) in enumerate(rows):
            row_tag = "odd" if i % 2 == 0 else "even"
            cat_tag = f"cat_{cat}"
            self._tree.insert(
                "",
                "end",
                iid=str(i),
                values=(str(pos), lexeme, tt, cat),
                tags=(row_tag, cat_tag),
            )
        count = len(rows)
        self._footer_var.set(f"  {count} token{'s' if count != 1 else ''} generated")

    def clear(self) -> None:
        """Remove all rows from the table."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._footer_var.set("No tokens")
