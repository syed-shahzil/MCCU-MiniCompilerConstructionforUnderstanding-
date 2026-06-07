"""
gui/diagnostics_panel.py
-------------------------
DiagnosticsPanel — displays compiler diagnostics (errors, warnings, info)
in a color-coded scrollable list with icons and recovery indicators.

Each diagnostic row shows:
  - Level icon (✖ / ⚠ / ℹ)
  - Code (e.g. [S004])
  - Phase (Lexical / Syntax / Warning / Info)
  - Message
  - Position (if available)
  - Recovery indicator
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any

from gui.styles import Colors, Fonts
from error_handling.diagnostics import Diagnostic, DiagnosticsCollector


class DiagnosticsPanel(ttk.Frame):
    """
    Scrollable diagnostics display panel.

    Args:
        parent: Parent widget.
    """

    COLUMNS = ("Level", "Code", "Phase", "Message", "Position")
    COL_WIDTHS = (60, 70, 80, 380, 80)

    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(parent, style="TFrame", **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        hdr = ttk.Label(
            self,
            text="  Diagnostics",
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

        anchors = ("center", "center", "center", "w", "center")
        for col, width, anchor in zip(self.COLUMNS, self.COL_WIDTHS, anchors):
            self._tree.heading(col, text=col, anchor="w")
            self._tree.column(col, width=width, anchor=anchor, minwidth=40)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Level color tags
        self._tree.tag_configure(
            "ERROR",   foreground=Colors.ERROR,   background=Colors.ROW_ODD,
        )
        self._tree.tag_configure(
            "WARNING", foreground=Colors.WARNING,  background=Colors.ROW_ODD,
        )
        self._tree.tag_configure(
            "INFO",    foreground=Colors.INFO,     background=Colors.ROW_EVEN,
        )
        self._tree.tag_configure(
            "RECOVERED", foreground=Colors.SUCCESS, background=Colors.ROW_EVEN,
        )

        # Status footer
        self._footer_var = tk.StringVar(value="No diagnostics")
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

    def populate(self, collector: DiagnosticsCollector) -> None:
        """
        Fill the diagnostics table from a DiagnosticsCollector.

        Args:
            collector: DiagnosticsCollector containing all pipeline diagnostics.
        """
        self.clear()
        diagnostics = collector.get_all()

        for i, diag in enumerate(diagnostics):
            pos_str = f"pos {diag.position}" if diag.position is not None else "—"
            tag = "RECOVERED" if diag.recovered else diag.level
            self._tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    diag.icon,
                    f"[{diag.code}]",
                    diag.phase,
                    diag.message,
                    pos_str,
                ),
                tags=(tag,),
            )

        errors = collector.error_count()
        warnings = collector.warning_count()
        info = len(collector.get_info())
        total = len(diagnostics)

        if total == 0:
            self._footer_var.set("  ✔  No diagnostics — compilation clean")
        else:
            parts = []
            if errors:
                parts.append(f"{errors} error{'s' if errors != 1 else ''}")
            if warnings:
                parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
            if info:
                parts.append(f"{info} info")
            self._footer_var.set("  " + "  •  ".join(parts))

    def show_success(self) -> None:
        """Display a clean success state with no diagnostics."""
        self.clear()
        self._tree.insert(
            "", "end", iid="ok",
            values=("✔", "—", "—", "Compilation successful — no errors or warnings", "—"),
            tags=("INFO",),
        )
        self._footer_var.set("  ✔  All clear")

    def clear(self) -> None:
        """Remove all diagnostics rows."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._footer_var.set("No diagnostics")
