"""
gui/main_window.py
------------------
MainWindow — the top-level Tkinter application window for MCCU.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  Header: MCCU title + subtitle                          │
  ├─────────────────────────────────────────────────────────┤
  │  Query editor (multi-line Text) + action buttons        │
  ├─────────────────────────────────────────────────────────┤
  │  Stats bar: Type | Parser | Tokens | AST Nodes | Status │
  ├───────────────────────────────────┬─────────────────────┤
  │  Notebook tabs:                   │  Grammar rule panel  │
  │   [Tokens] [AST] [Diagnostics]    │  (right sidebar)     │
  └───────────────────────────────────┴─────────────────────┘

The entire compiler pipeline is invoked by _run_analysis() which calls
run_lexer() → run_parser() → renders results into the three tab panels.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Any

from gui.styles import Colors, Fonts, apply_theme
from gui.token_panel import TokenPanel
from gui.ast_panel import ASTPanel
from gui.diagnostics_panel import DiagnosticsPanel
from lexer.pipeline import run_lexer
from parser.parser_manager import run_parser
from error_handling.diagnostics import DiagnosticsCollector
from compiler_ast.nodes import create_error_ast
from config.grammar_rules import get_grammar
from utils.formatting import statement_label, status_summary


# ---------------------------------------------------------------------------
# Example queries for the placeholder / quick-load feature
# ---------------------------------------------------------------------------

EXAMPLE_QUERIES = {
    "SELECT (basic)":      "SELECT name, age FROM students WHERE age > 20 ORDER BY age DESC;",
    "SELECT (aggregate)":  "SELECT COUNT(*) FROM orders WHERE status = 'active';",
    "INSERT":              "INSERT INTO students (name, age) VALUES ('Ali', 20);",
    "UPDATE":              "UPDATE students SET age = 21, grade = 'A' WHERE id = 5;",
    "DELETE":              "DELETE FROM students WHERE id = 10;",
    "DROP TABLE":          "DROP TABLE temp_data;",
    "DROP DATABASE":       "DROP DATABASE test_db;",
    "Error — missing FROM":"SELECT name students;",
    "Error — invalid char":"SELECT name FROM students WHERE id @= 5;",
}


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow:
    """
    The root application window for MCCU.

    Usage::

        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
    """

    APP_TITLE   = "MCCU — Mini Compiler Construction for Understanding"
    # Keep the app large for demos, but still inside the usable desktop area.
    MIN_WIDTH   = 1100
    MIN_HEIGHT  = 660

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._setup_window()
        apply_theme(root)
        self._build_ui()
        self._load_example("SELECT (basic)")

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self._root.title(self.APP_TITLE)
        self._root.configure(bg=Colors.BG_DARK)

        # Responsive startup size: large enough for screenshots, but always
        # kept inside the visible screen area so the bottom panels/footer do
        # not go behind the taskbar or outside the display.
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        margin_x = 40
        margin_y = 90

        available_w = max(960, sw - margin_x)
        available_h = max(640, sh - margin_y)
        win_w = min(1380, available_w)
        win_h = min(860, available_h)

        min_w = min(self.MIN_WIDTH, available_w)
        min_h = min(self.MIN_HEIGHT, available_h)
        self._root.minsize(min_w, min_h)

        x = max((sw - win_w) // 2, 0)
        y = max((sh - win_h) // 2, 0)
        self._root.geometry(f"{int(win_w)}x{int(win_h)}+{int(x)}+{int(y)}")

        # On Windows this maximizes inside the usable work area (not true
        # fullscreen), giving the token table and AST maximum space while still
        # keeping the taskbar/bottom content visible.
        try:
            self._root.state("zoomed")
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Main vertical container
        main = tk.Frame(self._root, bg=Colors.BG_DARK)
        main.pack(fill="both", expand=True)

        self._build_header(main)
        self._build_input_section(main)
        self._build_stats_bar(main)
        self._build_results_section(main)

    def _build_header(self, parent: tk.Frame) -> None:
        """App title and subtitle bar."""
        header = tk.Frame(parent, bg=Colors.BG_DARK, pady=0)
        header.pack(fill="x", padx=0)

        # Accent top border
        border = tk.Frame(header, bg=Colors.ACCENT, height=3)
        border.pack(fill="x")

        # Title area
        title_row = tk.Frame(header, bg=Colors.BG_DARK, padx=18, pady=6)
        title_row.pack(fill="x")

        # Left: title + subtitle
        left = tk.Frame(title_row, bg=Colors.BG_DARK)
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="MCCU",
            font=Fonts.UI_TITLE,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_ACCENT,
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Mini Compiler Construction for Understanding  ·  SQL Lexical & Syntax Analysis",
            font=Fonts.UI_SUBTITLE,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

        # Right: version badge
        badge = tk.Frame(title_row, bg=Colors.ACCENT_DIM, padx=12, pady=6)
        badge.pack(side="right", anchor="center")
        tk.Label(
            badge,
            text="v1.0  |  Phase 1 + Phase 2",
            font=Fonts.UI_SMALL,
            bg=Colors.ACCENT_DIM,
            fg=Colors.TEXT_ACCENT,
        ).pack()

        # Bottom separator
        tk.Frame(header, bg=Colors.BORDER, height=1).pack(fill="x")

    def _build_input_section(self, parent: tk.Frame) -> None:
        """Query editor with action buttons and example loader."""
        section = tk.Frame(parent, bg=Colors.BG_DARK, padx=14, pady=4)
        section.pack(fill="x")

        # Row: label + example loader
        top_row = tk.Frame(section, bg=Colors.BG_DARK)
        top_row.pack(fill="x", pady=(0, 3))

        tk.Label(
            top_row,
            text="SQL Query Editor",
            font=Fonts.UI_HEADING,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_ACCENT,
        ).pack(side="left", anchor="w")

        # Example query dropdown
        tk.Label(
            top_row,
            text="Load example:",
            font=Fonts.UI_SMALL,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_SECONDARY,
        ).pack(side="right", padx=(0, 6))

        self._example_var = tk.StringVar(value="SELECT (basic)")
        example_menu = ttk.Combobox(
            top_row,
            textvariable=self._example_var,
            values=list(EXAMPLE_QUERIES.keys()),
            state="readonly",
            width=26,
            font=Fonts.UI_SMALL,
        )
        example_menu.pack(side="right", padx=(0, 6))
        example_menu.bind("<<ComboboxSelected>>", self._on_example_selected)

        # Text editor
        editor_frame = tk.Frame(section, bg=Colors.BORDER, padx=1, pady=1)
        editor_frame.pack(fill="x")

        self._editor = tk.Text(
            editor_frame,
            height=2,
            font=Fonts.CODE_LARGE,
            bg=Colors.BG_INPUT,
            fg=Colors.TEXT_CODE,
            insertbackground=Colors.ACCENT,
            selectbackground=Colors.ROW_SELECT,
            selectforeground=Colors.ROW_SELECT_FG,
            relief="flat",
            padx=12,
            pady=5,
            wrap="word",
            undo=True,
        )
        self._editor.pack(fill="x")
        # Bind Ctrl+Return to analyze
        self._editor.bind("<Control-Return>", lambda e: self._run_analysis())

        # Button row
        btn_row = tk.Frame(section, bg=Colors.BG_DARK, pady=2)
        btn_row.pack(fill="x")

        # Analyze button
        self._analyze_btn = ttk.Button(
            btn_row,
            text="▶  Analyze Query",
            style="Primary.TButton",
            command=self._run_analysis,
        )
        self._analyze_btn.pack(side="left")

        # Clear button
        ttk.Button(
            btn_row,
            text="⟳  Clear",
            style="Secondary.TButton",
            command=self._clear_all,
        ).pack(side="left", padx=(10, 0))

        # Keyboard hint
        tk.Label(
            btn_row,
            text="Ctrl+Enter to analyze",
            font=Fonts.UI_SMALL,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_MUTED,
        ).pack(side="right")

    def _build_stats_bar(self, parent: tk.Frame) -> None:
        """Compilation stats bar between editor and results."""
        bar = tk.Frame(parent, bg=Colors.BG_CARD, padx=14, pady=4)
        bar.pack(fill="x")

        self._stat_vars: dict[str, tk.StringVar] = {}
        stats = [
            ("Statement", "—"),
            ("Parser",    "—"),
            ("Tokens",    "—"),
            ("AST Nodes", "—"),
            ("Status",    "Awaiting input"),
        ]

        for i, (label, default) in enumerate(stats):
            cell = tk.Frame(bar, bg=Colors.BG_CARD, padx=12, pady=1)
            cell.pack(side="left", fill="y")

            tk.Label(
                cell,
                text=label,
                font=("Segoe UI", 9),
                bg=Colors.BG_CARD,
                fg=Colors.TEXT_MUTED,
            ).pack(anchor="w")

            var = tk.StringVar(value=default)
            self._stat_vars[label] = var

            color = Colors.TEXT_ACCENT if label != "Status" else Colors.TEXT_SECONDARY
            lbl = tk.Label(
                cell,
                textvariable=var,
                font=("Segoe UI", 10, "bold"),
                bg=Colors.BG_CARD,
                fg=color,
            )
            lbl.pack(anchor="w")
            if label == "Status":
                self._status_label = lbl

            if i < len(stats) - 1:
                tk.Frame(bar, bg=Colors.BORDER, width=1).pack(side="left", fill="y", padx=4)

    def _build_results_section(self, parent: tk.Frame) -> None:
        """Notebook tabs + right sidebar for grammar rules."""
        container = tk.Frame(parent, bg=Colors.BG_DARK)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        tk.Frame(container, bg=Colors.BORDER, height=1).pack(fill="x")

        inner = tk.Frame(container, bg=Colors.BG_DARK)
        inner.pack(fill="both", expand=True, padx=10, pady=4)
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0, minsize=238)

        # ---- Left: Notebook ----
        notebook_frame = tk.Frame(inner, bg=Colors.BG_DARK)
        notebook_frame.grid(row=0, column=0, sticky="nsew")

        self._notebook = ttk.Notebook(notebook_frame, style="TNotebook")
        self._notebook.pack(fill="both", expand=True)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Tab 1: Tokens
        tokens_frame = ttk.Frame(self._notebook, style="TFrame")
        self._notebook.add(tokens_frame, text="  🔤  Tokens  ")
        self._token_panel = TokenPanel(tokens_frame)
        self._token_panel.pack(fill="both", expand=True)

        # Tab 2: AST
        ast_frame = ttk.Frame(self._notebook, style="TFrame")
        self._notebook.add(ast_frame, text="  🌲  AST  ")
        self._ast_panel = ASTPanel(ast_frame)
        self._ast_panel.pack(fill="both", expand=True)

        # Tab 3: Diagnostics
        diag_frame = ttk.Frame(self._notebook, style="TFrame")
        self._notebook.add(diag_frame, text="  🔍  Diagnostics  ")
        self._diag_panel = DiagnosticsPanel(diag_frame)
        self._diag_panel.pack(fill="both", expand=True)

        # ---- Right: Grammar sidebar ----
        # Grid rows keep the Pipeline Steps visible. The grammar box is the only
        # part that is allowed to shrink, and it has its own internal scrollbar.
        sidebar = tk.Frame(inner, bg=Colors.BG_CARD, width=238, padx=8, pady=8)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(1, weight=1)

        tk.Label(
            sidebar,
            text="Grammar Rule",
            font=Fonts.UI_LABEL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_ACCENT,
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        grammar_box = tk.Frame(sidebar, bg=Colors.BORDER, padx=1, pady=1)
        grammar_box.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        grammar_box.rowconfigure(0, weight=1)
        grammar_box.columnconfigure(0, weight=1)

        self._grammar_text = tk.Text(
            grammar_box,
            height=5,
            font=Fonts.CODE_SMALL,
            bg=Colors.BG_INPUT,
            fg=Colors.TEXT_SECONDARY,
            relief="flat",
            padx=7,
            pady=5,
            wrap="word",
            state="disabled",
            cursor="arrow",
        )
        grammar_scroll = ttk.Scrollbar(grammar_box, orient="vertical", command=self._grammar_text.yview)
        self._grammar_text.configure(yscrollcommand=grammar_scroll.set)
        self._grammar_text.grid(row=0, column=0, sticky="nsew")
        grammar_scroll.grid(row=0, column=1, sticky="ns")

        pipeline_box = tk.Frame(sidebar, bg=Colors.BG_CARD)
        pipeline_box.grid(row=2, column=0, sticky="ew")

        tk.Frame(pipeline_box, bg=Colors.BORDER, height=1).pack(fill="x", pady=(0, 5))

        tk.Label(
            pipeline_box,
            text="Pipeline Steps",
            font=Fonts.UI_LABEL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_ACCENT,
        ).pack(anchor="w", pady=(0, 3))

        pipeline_steps = [
            ("1", "Lexical", "Tokenize + classify"),
            ("2", "Syntax", "Parser selection"),
            ("3", "AST", "Structured tree"),
            ("4", "Diagnostics", "Errors/warnings"),
        ]
        for num, name, desc in pipeline_steps:
            step_row = tk.Frame(pipeline_box, bg=Colors.BG_CARD)
            step_row.pack(fill="x", pady=(0, 2))

            tk.Label(
                step_row,
                text=num,
                font=("Consolas", 8, "bold"),
                bg=Colors.ACCENT_DIM,
                fg=Colors.TEXT_ACCENT,
                width=2,
                relief="flat",
                padx=2,
            ).pack(side="left", anchor="n", padx=(0, 5))

            tk.Label(
                step_row,
                text=f"{name} — {desc}",
                font=("Segoe UI", 8),
                bg=Colors.BG_CARD,
                fg=Colors.TEXT_PRIMARY,
                wraplength=190,
                justify="left",
            ).pack(side="left", fill="x", expand=True, anchor="w")


    # ------------------------------------------------------------------
    # Compiler Pipeline
    # ------------------------------------------------------------------

    def _run_analysis(self) -> None:
        """Execute the full compiler pipeline and update all panels."""
        query = self._editor.get("1.0", "end-1c").strip()

        if not query:
            self._set_status("No query entered", Colors.WARNING)
            return

        self._set_status("Analyzing…", Colors.TEXT_SECONDARY)
        self._root.update_idletasks()

        collector = DiagnosticsCollector()

        # ---- Phase 1: Lexical Analysis ----
        lex_result = run_lexer(query)
        collector.add_from_lexical_issues(lex_result.lexical_issues)

        token_rows = lex_result.get_display_rows()

        if not lex_result.tokens:
            self._token_panel.clear()
            error_ast = create_error_ast(
                phase="Lexical Analysis",
                message="Lexical error: no valid tokens were generated.",
                details=[d.message for d in collector.get_all()] or ["Input is empty or could not be tokenized."],
            )
            self._ast_panel.populate(error_ast)
            self._diag_panel.populate(collector)
            self._update_stats(
                stmt="—",
                parser="Not run",
                tokens=0,
                nodes=self._count_ast_nodes(error_ast),
                success=False,
            )
            self._set_status("✖  Lexical error — no tokens", Colors.ERROR)
            self._notebook.select(2)
            self._update_grammar("UNKNOWN")
            return

        # Populate token table before parsing so invalid tokens are visible.
        self._token_panel.populate(token_rows)

        # Add missing-semicolon warning
        last_type = lex_result.tokens[-1][0] if lex_result.tokens else ""
        if last_type != "SEMICOLON":
            collector.add_warning("W002", "Statement is missing a trailing semicolon")

        invalid_tokens = self._collect_invalid_tokens(token_rows)
        if lex_result.has_lexical_errors or invalid_tokens:
            if invalid_tokens and not any(d.code == "L001" for d in collector.get_all()):
                collector.add_error(
                    "L001",
                    "Lexical error: unknown token found",
                    detail="Tokenizer produced UNKNOWN token(s).",
                )

            error_ast = create_error_ast(
                phase="Lexical Analysis",
                message="Lexical error: unknown/invalid token found. Parsing stopped safely.",
                invalid_tokens=invalid_tokens,
                details=[d.message for d in collector.get_all()],
            )
            self._ast_panel.populate(error_ast)
            self._diag_panel.populate(collector)
            self._update_stats(
                stmt=lex_result.tokens[0][0] if lex_result.tokens else "UNKNOWN",
                parser="Not run",
                tokens=lex_result.token_count,
                nodes=self._count_ast_nodes(error_ast),
                success=False,
            )
            self._set_status(
                f"✖  Lexical error — {len(invalid_tokens)} invalid token(s)",
                Colors.ERROR,
            )
            # Keep the Tokens tab visible so the highlighted UNKNOWN token is seen immediately.
            self._notebook.select(0)
            self._update_grammar("UNKNOWN")
            return

        # ---- Phase 2: Syntax Parsing ----
        parse_result = run_parser(lex_result.tokens)

        if parse_result.error:
            collector.add_from_exception(parse_result.error)

        # ---- Phase 3: AST + Diagnostics ----
        if parse_result.success and parse_result.ast:
            self._ast_panel.populate(parse_result.ast)
            display_node_count = parse_result.ast_node_count
        else:
            message = "Parsing failed due to invalid syntax."
            if parse_result.error:
                message = str(parse_result.error).split("] ", 1)[-1]
            error_ast = create_error_ast(
                phase="Syntax Parsing",
                message=message,
                details=["BrokenConnection: parser could not complete a valid AST."],
            )
            self._ast_panel.populate(error_ast)
            display_node_count = self._count_ast_nodes(error_ast)

        if collector.is_clean() and parse_result.success:
            self._diag_panel.show_success()
        else:
            self._diag_panel.populate(collector)

        # ---- Stats bar ----
        token_count = lex_result.token_count
        node_count  = display_node_count
        self._update_stats(
            stmt=parse_result.statement_type,
            parser=parse_result.parser_name,
            tokens=token_count,
            nodes=node_count,
            success=parse_result.success,
        )

        # ---- Status label ----
        if parse_result.success and not collector.has_errors():
            color = Colors.SUCCESS if not collector.has_warnings() else Colors.WARNING
            msg = "✔  Success" if not collector.has_warnings() else f"⚠  Success with {collector.warning_count()} warning(s)"
            self._set_status(msg, color)
        else:
            self._set_status(
                f"✖  {collector.error_count()} error(s) — see Diagnostics tab",
                Colors.ERROR,
            )
            # Auto-switch to diagnostics tab on error
            self._notebook.select(2)

        # ---- Grammar sidebar ----
        self._update_grammar(parse_result.statement_type)

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------

    def _collect_invalid_tokens(self, token_rows: list[tuple[int, str, str, str, str]]) -> list[dict[str, Any]]:
        """Return UNKNOWN/invalid tokens in a shape suitable for the error AST."""
        invalid: list[dict[str, Any]] = []
        for index, line_col, lexeme, token_type, category in token_rows:
            if token_type == "UNKNOWN" or category == "Unknown":
                invalid.append({
                    "index": index,
                    "line_col": line_col,
                    "lexeme": lexeme,
                    "token_type": token_type,
                    "category": category,
                })
        return invalid

    def _count_ast_nodes(self, obj: Any, depth: int = 0) -> int:
        """Small local AST-node counter used for visible error placeholder ASTs."""
        if depth > 10:
            return 1
        if isinstance(obj, dict):
            return 1 + sum(self._count_ast_nodes(v, depth + 1) for v in obj.values())
        if isinstance(obj, list):
            return sum(self._count_ast_nodes(item, depth + 1) for item in obj)
        return 1

    def _update_stats(
        self,
        stmt: str,
        parser: str,
        tokens: int,
        nodes: int,
        success: bool,
    ) -> None:
        self._stat_vars["Statement"].set(stmt)
        self._stat_vars["Parser"].set(parser)
        self._stat_vars["Tokens"].set(str(tokens))
        self._stat_vars["AST Nodes"].set(str(nodes))

    def _set_status(self, message: str, color: str = Colors.TEXT_SECONDARY) -> None:
        self._stat_vars["Status"].set(message)
        self._status_label.configure(fg=color)

    def _update_grammar(self, stmt_type: str) -> None:
        rule = get_grammar(stmt_type)
        self._grammar_text.configure(state="normal")
        self._grammar_text.delete("1.0", "end")
        self._grammar_text.insert("1.0", rule)
        self._grammar_text.configure(state="disabled")

    def _load_example(self, key: str) -> None:
        query = EXAMPLE_QUERIES.get(key, "")
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", query)

    def _clear_all(self) -> None:
        self._editor.delete("1.0", "end")
        self._token_panel.clear()
        self._ast_panel.clear()
        self._diag_panel.clear()
        for key in self._stat_vars:
            self._stat_vars[key].set("—" if key != "Status" else "Awaiting input")
        self._status_label.configure(fg=Colors.TEXT_SECONDARY)
        self._grammar_text.configure(state="normal")
        self._grammar_text.delete("1.0", "end")
        self._grammar_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_example_selected(self, event: Any) -> None:
        self._load_example(self._example_var.get())
        self._run_analysis()

    def _on_tab_changed(self, event: Any) -> None:
        pass   # Reserved for future tab-specific actions
