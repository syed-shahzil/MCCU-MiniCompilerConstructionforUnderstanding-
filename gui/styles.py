"""
gui/styles.py
-------------
Centralized ttk.Style theme and color palette for the MCCU application.

Defines:
  - Color palette (dark mode, violet accent)
  - Font stack (Consolas for code, Segoe UI for UI)
  - apply_theme(root): call once at startup to configure all widget styles

Color palette inspired by VS Code Dark+ theme with a violet/indigo accent.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, font as tkfont


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

class Colors:
    # Base surfaces
    BG_DARK      = "#0d0d1a"    # window background
    BG_SURFACE   = "#12122b"    # panel / frame background
    BG_CARD      = "#1a1a3e"    # card / elevated surface
    BG_INPUT     = "#0a0a1f"    # text editor background
    BG_HOVER     = "#252550"    # hover state

    # Accent (violet / indigo family)
    ACCENT       = "#7c3aed"    # primary accent — violet
    ACCENT_LIGHT = "#9d5ff5"    # lighter accent (hover)
    ACCENT_DIM   = "#4c2680"    # dimmed accent (pressed)
    ACCENT_GLOW  = "#3d1f80"    # subtle glow background

    # Semantic colors
    SUCCESS      = "#10b981"    # green
    ERROR        = "#ef4444"    # red
    WARNING      = "#f59e0b"    # amber
    INFO         = "#38bdf8"    # sky blue

    # Text colors
    TEXT_PRIMARY   = "#e2e8f0"  # main body text
    TEXT_SECONDARY = "#94a3b8"  # subdued labels
    TEXT_ACCENT    = "#a78bfa"  # accent text (violet-light)
    TEXT_CODE      = "#c9d1d9"  # code / monospace text
    TEXT_MUTED     = "#475569"  # very subdued

    # Token category colors (for table rows)
    TOK_KEYWORD    = "#c084fc"  # purple
    TOK_IDENTIFIER = "#67e8f9"  # cyan
    TOK_OPERATOR   = "#fbbf24"  # amber
    TOK_DELIMITER  = "#94a3b8"  # slate
    TOK_CONSTANT   = "#86efac"  # green
    TOK_UNKNOWN    = "#f87171"  # red

    # Borders / separators
    BORDER       = "#2d2d5e"
    BORDER_LIGHT = "#3d3d6e"

    # Treeview row alternation
    ROW_ODD      = "#13132e"
    ROW_EVEN     = "#0f0f26"
    ROW_SELECT   = "#3b1f8c"
    ROW_SELECT_FG = "#ffffff"


# ---------------------------------------------------------------------------
# Font Definitions
# ---------------------------------------------------------------------------

class Fonts:
    # Monospace (code / tokens)
    CODE_LARGE  = ("Consolas", 13)
    CODE_MEDIUM = ("Consolas", 11)
    CODE_SMALL  = ("Consolas", 10)

    # UI text
    UI_TITLE    = ("Segoe UI", 22, "bold")
    UI_SUBTITLE = ("Segoe UI", 11)
    UI_HEADING  = ("Segoe UI", 13, "bold")
    UI_BODY     = ("Segoe UI", 11)
    UI_SMALL    = ("Segoe UI", 10)
    UI_LABEL    = ("Segoe UI", 10, "bold")

    # Button
    BTN_PRIMARY = ("Segoe UI", 12, "bold")
    BTN_SMALL   = ("Segoe UI", 10)

    # Tab labels
    TAB_LABEL   = ("Segoe UI", 11, "bold")


# ---------------------------------------------------------------------------
# Token category → color mapping
# ---------------------------------------------------------------------------

CATEGORY_COLORS: dict[str, str] = {
    "Keyword":    Colors.TOK_KEYWORD,
    "Identifier": Colors.TOK_IDENTIFIER,
    "Operator":   Colors.TOK_OPERATOR,
    "Delimiter":  Colors.TOK_DELIMITER,
    "Constant":   Colors.TOK_CONSTANT,
    "Unknown":    Colors.TOK_UNKNOWN,
}


# ---------------------------------------------------------------------------
# Theme Application
# ---------------------------------------------------------------------------

def apply_theme(root: tk.Tk) -> None:
    """
    Configure ttk.Style for the MCCU dark theme.

    Call once after creating the root window, before building widgets.
    """
    style = ttk.Style(root)

    # Use 'clam' as base — most customisable built-in theme
    style.theme_use("clam")

    c = Colors
    f = Fonts

    # --- TFrame ---
    style.configure(
        "TFrame",
        background=c.BG_SURFACE,
    )
    style.configure(
        "Card.TFrame",
        background=c.BG_CARD,
        relief="flat",
    )
    style.configure(
        "Dark.TFrame",
        background=c.BG_DARK,
    )

    # --- TLabel ---
    style.configure(
        "TLabel",
        background=c.BG_SURFACE,
        foreground=c.TEXT_PRIMARY,
        font=f.UI_BODY,
    )
    style.configure(
        "Title.TLabel",
        background=c.BG_DARK,
        foreground=c.TEXT_ACCENT,
        font=f.UI_TITLE,
    )
    style.configure(
        "Subtitle.TLabel",
        background=c.BG_DARK,
        foreground=c.TEXT_SECONDARY,
        font=f.UI_SUBTITLE,
    )
    style.configure(
        "Heading.TLabel",
        background=c.BG_CARD,
        foreground=c.TEXT_ACCENT,
        font=f.UI_HEADING,
    )
    style.configure(
        "Stat.TLabel",
        background=c.BG_CARD,
        foreground=c.TEXT_PRIMARY,
        font=f.UI_SMALL,
    )
    style.configure(
        "StatValue.TLabel",
        background=c.BG_CARD,
        foreground=c.TEXT_ACCENT,
        font=("Segoe UI", 10, "bold"),
    )
    style.configure(
        "Muted.TLabel",
        background=c.BG_SURFACE,
        foreground=c.TEXT_MUTED,
        font=f.UI_SMALL,
    )
    style.configure(
        "Dark.TLabel",
        background=c.BG_DARK,
        foreground=c.TEXT_SECONDARY,
        font=f.UI_SMALL,
    )

    # --- TButton ---
    style.configure(
        "Primary.TButton",
        background=c.ACCENT,
        foreground="#ffffff",
        font=f.BTN_PRIMARY,
        borderwidth=0,
        focusthickness=0,
        padding=(18, 7),
    )
    style.map(
        "Primary.TButton",
        background=[("active", c.ACCENT_LIGHT), ("pressed", c.ACCENT_DIM)],
        foreground=[("active", "#ffffff")],
    )
    style.configure(
        "Secondary.TButton",
        background=c.BG_CARD,
        foreground=c.TEXT_SECONDARY,
        font=f.BTN_SMALL,
        borderwidth=1,
        relief="flat",
        padding=(10, 5),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", c.BG_HOVER)],
        foreground=[("active", c.TEXT_PRIMARY)],
    )

    # --- TNotebook ---
    style.configure(
        "TNotebook",
        background=c.BG_DARK,
        borderwidth=0,
        tabmargins=[0, 0, 0, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background=c.BG_CARD,
        foreground=c.TEXT_SECONDARY,
        font=f.TAB_LABEL,
        padding=(14, 6),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", c.ACCENT_DIM), ("active", c.BG_HOVER)],
        foreground=[("selected", c.TEXT_ACCENT), ("active", c.TEXT_PRIMARY)],
    )

    # --- Treeview ---
    style.configure(
        "Treeview",
        background=c.BG_SURFACE,
        foreground=c.TEXT_PRIMARY,
        fieldbackground=c.BG_SURFACE,
        font=f.CODE_MEDIUM,
        rowheight=28,
        borderwidth=0,
    )
    # Token table uses a slightly compact row height so demo queries can show
    # all token rows without visible table scrollbars. Other Treeviews keep
    # the original spacing.
    style.configure(
        "Token.Treeview",
        background=c.BG_SURFACE,
        foreground=c.TEXT_PRIMARY,
        fieldbackground=c.BG_SURFACE,
        font=f.CODE_MEDIUM,
        rowheight=24,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background=c.BG_CARD,
        foreground=c.TEXT_ACCENT,
        font=f.UI_LABEL,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", c.ROW_SELECT)],
        foreground=[("selected", c.ROW_SELECT_FG)],
    )
    style.map(
        "Token.Treeview",
        background=[("selected", c.ROW_SELECT)],
        foreground=[("selected", c.ROW_SELECT_FG)],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", c.BG_HOVER)],
    )

    # --- TScrollbar ---
    style.configure(
        "Vertical.TScrollbar",
        background=c.BG_CARD,
        troughcolor=c.BG_DARK,
        arrowcolor=c.TEXT_MUTED,
        borderwidth=0,
        width=10,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", c.ACCENT_DIM)],
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=c.BG_CARD,
        troughcolor=c.BG_DARK,
        arrowcolor=c.TEXT_MUTED,
        borderwidth=0,
        width=10,
    )

    # --- TSeparator ---
    style.configure(
        "TSeparator",
        background=c.BORDER,
    )

    # Configure root window
    root.configure(bg=c.BG_DARK)
