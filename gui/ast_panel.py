"""
gui/ast_panel.py
----------------
ASTPanel — displays the Abstract Syntax Tree in two interactive formats:
  1. Graph View: A beautiful, custom-rendered canvas tree showing colored nodes and links.
  2. Tree List: A standard hierarchical ttk.Treeview.

The user can toggle between views using buttons in the panel header.
Graph nodes are color-coded based on node type and can be panned by dragging.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from gui.styles import Colors, Fonts
from compiler_ast.visualizer import build_tree_nodes, render_text_tree, TreeNode


# ===========================================================================
# Visual Graph Component (Canvas-based)
# ===========================================================================

class GraphNode:
    """Represents a node in the visual tree layout."""
    def __init__(self, label: str, tag_type: str = "clause") -> None:
        self.label: str = label
        self.tag_type: str = tag_type
        self.children: list[GraphNode] = []
        self.x: float = 0.0
        self.y: float = 0.0
        self.width: float = 0.0
        self.height: float = 36.0


class ASTVisualGraph(ttk.Frame):
    """
    Renders an AST as an interactive node-link tree diagram on a Canvas.
    Supports click-and-drag panning and zoom in/out controls.
    """
    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(parent, style="TFrame", **kwargs)
        self._root_node: GraphNode | None = None
        self._zoom: float = 1.0
        self._min_zoom: float = 0.65
        self._max_zoom: float = 1.75
        self._zoom_callback: Callable[[float], None] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Canvas
        self.canvas = tk.Canvas(
            self,
            bg=Colors.BG_INPUT,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Drag to pan bindings
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_drag)
        self.canvas.bind("<Double-Button-1>", self._on_reset_view)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)

        # Tip label
        tip = ttk.Label(
            self,
            text="💡 Drag to pan  ·  Use + / − buttons or Ctrl+MouseWheel to zoom  ·  Double-click to reset position",
            style="Muted.TLabel",
            anchor="center",
            padding=(0, 4),
        )
        tip.pack(fill="x", side="bottom")

    def _on_pan_start(self, event: Any) -> None:
        self.canvas.scan_mark(event.x, event.y)

    def _on_pan_drag(self, event: Any) -> None:
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_reset_view(self, event: Any = None) -> None:
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _on_ctrl_mousewheel(self, event: Any) -> str:
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"

    def _scaled_font(self) -> tuple[Any, ...]:
        family, size, *style = Fonts.CODE_SMALL
        return (family, max(7, int(round(size * self._zoom))), *style)

    def set_zoom_callback(self, callback: Callable[[float], None]) -> None:
        """Register a small UI callback used to display the live zoom value."""
        self._zoom_callback = callback
        self._notify_zoom_changed()

    def _notify_zoom_changed(self) -> None:
        if self._zoom_callback is not None:
            self._zoom_callback(self._zoom)

    def set_zoom(self, zoom: float) -> None:
        """Set graph zoom and redraw without changing the AST data."""
        self._zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        self.draw_graph()
        self._notify_zoom_changed()

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom + 0.12)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom - 0.12)

    def reset_zoom(self) -> None:
        self.set_zoom(1.0)
        self._on_reset_view()

    def populate(self, tree_nodes: list[TreeNode]) -> None:
        """Build hierarchical GraphNode structure from flat tree_nodes list."""
        self.canvas.delete("all")
        if not tree_nodes:
            self._root_node = None
            return

        nodes_map: dict[str, GraphNode] = {}
        root_node = None

        for tn in tree_nodes:
            # Determine type based on label content/naming
            tag_type = "clause"
            label_upper = tn.label.upper()
            
            # Root keywords
            if any(k in label_upper for k in ("ERRORNODE", "INVALIDTOKENNODE", "BROKEN")):
                tag_type = "error"
            elif any(k in label_upper for k in ("SELECT", "DELETE", "DROP", "INSERT", "UPDATE")):
                tag_type = "root"
            elif "→" in tn.label:
                if any(k in label_upper for k in ("FROM", "TABLE", "NAME")):
                    tag_type = "table"
                elif "AGGREGATE" in label_upper:
                    tag_type = "aggr"
                else:
                    tag_type = "value"

            gn = GraphNode(tn.label, tag_type)
            nodes_map[tn.node_id] = gn

            if not tn.parent_id:
                root_node = gn
            else:
                parent = nodes_map.get(tn.parent_id)
                if parent:
                    parent.children.append(gn)

        self._root_node = root_node
        self.draw_graph()

    def clear(self) -> None:
        self.canvas.delete("all")
        self._root_node = None

    def draw_graph(self) -> None:
        """Layout and render the nodes and connection arrows."""
        self.canvas.delete("all")
        if not self._root_node:
            return

        z = self._zoom
        level_height = 80 * z
        sibling_gap = 24 * z

        # 1. Measure label text to determine sizes
        def measure(node: GraphNode) -> None:
            char_width = 8.5 * z
            text_len = len(node.label)
            node.height = 36.0 * z
            node.width = max(130.0 * z, text_len * char_width + 24.0 * z)
            for child in node.children:
                measure(child)

        measure(self._root_node)

        # 2. Position nodes recursively (bottom-up centering)
        next_x = 20.0

        def layout(node: GraphNode, level: int = 0) -> None:
            nonlocal next_x
            node.y = level * level_height + 40.0

            if not node.children:
                # Leaf
                node.x = next_x + node.width / 2.0
                next_x += node.width + sibling_gap
            else:
                for child in node.children:
                    layout(child, level + 1)
                first = node.children[0].x
                last = node.children[-1].x
                node.x = (first + last) / 2.0

        layout(self._root_node)

        # 3. Center the entire graph structure in the canvas width
        # Force a widget update to ensure width is fetched
        self.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        if canvas_w < 100:
            canvas_w = 750

        all_nodes: list[GraphNode] = []
        def collect(node: GraphNode) -> None:
            all_nodes.append(node)
            for c in node.children:
                collect(c)
        collect(self._root_node)

        min_x = min(n.x - n.width/2 for n in all_nodes)
        max_x = max(n.x + n.width/2 for n in all_nodes)
        tree_width = max_x - min_x

        shift_x = (canvas_w - tree_width) / 2 - min_x
        if shift_x < 20:
            shift_x = 20 - min_x

        for n in all_nodes:
            n.x += shift_x

        # 4. Draw connectors (arrows) first so they go behind nodes
        def draw_connectors(node: GraphNode) -> None:
            for child in node.children:
                self.canvas.create_line(
                    node.x, node.y + node.height/2,
                    child.x, child.y - child.height/2,
                    fill=Colors.BORDER_LIGHT,
                    width=max(1, int(round(2 * z))),
                    arrow=tk.LAST,
                    arrowshape=(max(6, int(9 * z)), max(7, int(11 * z)), max(3, int(4 * z))),
                )
                draw_connectors(child)

        draw_connectors(self._root_node)

        # 5. Draw node boxes
        def draw_nodes(node: GraphNode) -> None:
            x1 = node.x - node.width/2
            y1 = node.y - node.height/2
            x2 = node.x + node.width/2
            y2 = node.y + node.height/2

            # Theme configurations per type
            bg = Colors.BG_CARD
            border = Colors.BORDER
            fg = Colors.TEXT_PRIMARY

            if node.tag_type == "root":
                bg = Colors.ACCENT
                border = Colors.ACCENT_LIGHT
                fg = "#ffffff"
            elif node.tag_type == "clause":
                bg = Colors.BG_CARD
                border = Colors.ACCENT_DIM
                fg = Colors.TEXT_ACCENT
            elif node.tag_type == "table":
                bg = Colors.BG_SURFACE
                border = Colors.TOK_IDENTIFIER
                fg = Colors.TOK_IDENTIFIER
            elif node.tag_type == "value":
                bg = Colors.BG_DARK
                border = Colors.TOK_CONSTANT
                fg = Colors.TOK_CONSTANT
            elif node.tag_type == "aggr":
                bg = Colors.BG_SURFACE
                border = Colors.TOK_OPERATOR
                fg = Colors.TOK_OPERATOR
            elif node.tag_type == "error":
                bg = Colors.BG_DARK
                border = Colors.ERROR
                fg = Colors.ERROR

            # Draw slightly rounded box using polygon smooth curves
            r = 6.0 * z
            points = [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2 - r,
                x1, y1 + r,
            ]
            self.canvas.create_polygon(
                points,
                fill=bg,
                outline=border,
                width=max(1, int(round(1.5 * z))),
                smooth=True,
            )

            # Node label text
            self.canvas.create_text(
                node.x, node.y,
                text=node.label,
                fill=fg,
                font=self._scaled_font(),
                justify="center",
            )

            for child in node.children:
                draw_nodes(child)

        draw_nodes(self._root_node)

        # Adjust scroll region to contain the whole zoomed tree structure.
        final_max_x = max(n.x + n.width/2 for n in all_nodes)
        max_y = max(n.y + n.height/2 for n in all_nodes)
        self.canvas.configure(scrollregion=(0, 0, final_max_x + 60 * z, max_y + 60 * z))


# ===========================================================================
# ASTPanel Container Component
# ===========================================================================

class ASTPanel(ttk.Frame):
    """
    Container offering switchable List/Graph views for the SQL AST.
    """
    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(parent, style="TFrame", **kwargs)
        self._ast: dict[str, Any] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Header bar with Switcher
        hdr_frame = ttk.Frame(self, style="TFrame")
        hdr_frame.pack(fill="x", padx=2, pady=(0, 4))

        hdr = ttk.Label(
            hdr_frame,
            text="  Abstract Syntax Tree",
            style="Heading.TLabel",
            padding=(0, 6, 0, 6),
        )
        hdr.pack(side="left")

        # Radio button switcher
        self._view_mode = tk.StringVar(value="graph")
        self._zoom_text = tk.StringVar(value="100%")
        
        zoom_controls = ttk.Frame(hdr_frame, style="TFrame")
        zoom_controls.pack(side="right", padx=(0, 8))

        ttk.Button(
            zoom_controls,
            text="−",
            width=3,
            style="Secondary.TButton",
            command=self._zoom_out,
        ).pack(side="left", padx=1)
        ttk.Button(
            zoom_controls,
            textvariable=self._zoom_text,
            width=5,
            style="Secondary.TButton",
            command=self._zoom_reset,
        ).pack(side="left", padx=1)
        ttk.Button(
            zoom_controls,
            text="+",
            width=3,
            style="Secondary.TButton",
            command=self._zoom_in,
        ).pack(side="left", padx=1)

        switcher = ttk.Frame(hdr_frame, style="TFrame")
        switcher.pack(side="right", padx=(0, 10))

        # Graph View toggle
        self.btn_graph = ttk.Radiobutton(
            switcher,
            text="🎨 Graph View",
            variable=self._view_mode,
            value="graph",
            command=self._on_view_changed,
            style="Toolbutton",
        )
        self.btn_graph.pack(side="right", padx=2)

        # Tree List toggle
        self.btn_tree = ttk.Radiobutton(
            switcher,
            text="🌲 Tree List",
            variable=self._view_mode,
            value="tree",
            command=self._on_view_changed,
            style="Toolbutton",
        )
        self.btn_tree.pack(side="right", padx=2)

        # ---- Card Content Container ----
        self.content_container = ttk.Frame(self, style="Card.TFrame")
        self.content_container.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        # Let the AST panel resize with the available notebook area instead of
        # forcing a fixed height that can push the footer outside the screen.
        self.content_container.pack_propagate(True)

        # View 1: Canvas Graph View
        self._graph_panel = ASTVisualGraph(self.content_container)
        self._graph_panel.set_zoom_callback(self._update_zoom_text)
        self._graph_panel.pack(fill="both", expand=True)

        # View 2: Treeview List (start unpacked)
        self._tree_frame = ttk.Frame(self.content_container, style="TFrame")

        self._tree = ttk.Treeview(
            self._tree_frame,
            show="tree",
            selectmode="browse",
            style="Treeview",
        )
        self._tree.column("#0", width=600, minwidth=200)

        vsb = ttk.Scrollbar(self._tree_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(self._tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree_frame.rowconfigure(0, weight=1)
        self._tree_frame.columnconfigure(0, weight=1)

        # Config Tree tags colors
        self._tree.tag_configure("root",    foreground=Colors.TOK_KEYWORD,    font=Fonts.CODE_MEDIUM)
        self._tree.tag_configure("clause",  foreground=Colors.TEXT_ACCENT,    font=Fonts.CODE_MEDIUM)
        self._tree.tag_configure("leaf",    foreground=Colors.TEXT_CODE,      font=Fonts.CODE_SMALL)
        self._tree.tag_configure("value",   foreground=Colors.TOK_CONSTANT,   font=Fonts.CODE_SMALL)
        self._tree.tag_configure("table",   foreground=Colors.TOK_IDENTIFIER, font=Fonts.CODE_MEDIUM)
        self._tree.tag_configure("aggr",    foreground=Colors.TOK_OPERATOR,   font=Fonts.CODE_MEDIUM)
        self._tree.tag_configure("error",   foreground=Colors.ERROR,          font=Fonts.CODE_MEDIUM)

        # Footer
        self._footer_var = tk.StringVar(value="No AST")
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

    def populate(self, ast: dict[str, Any]) -> None:
        """Fill both list and graph views with the parsed AST."""
        self._ast = ast
        self.clear()

        nodes = build_tree_nodes(ast)
        if not nodes:
            return

        # Populate View 1: Graph
        self._graph_panel.populate(nodes)

        # Populate View 2: Treeview
        for i, node in enumerate(nodes):
            tag = self._tag_for(node, i)
            parent = node.parent_id if node.parent_id else ""
            self._tree.insert(
                parent,
                "end",
                iid=node.node_id,
                text=f"  {node.label}",
                open=True,
                tags=(tag,),
            )

        node_count = len(nodes)
        self._footer_var.set(f"  {node_count} AST node{'s' if node_count != 1 else ''}")

    def clear(self) -> None:
        """Reset both visual elements."""
        self._graph_panel.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._footer_var.set("No AST")

    # ------------------------------------------------------------------
    # Event Handlers & Helpers
    # ------------------------------------------------------------------

    def _update_zoom_text(self, zoom: float) -> None:
        self._zoom_text.set(f"{int(round(zoom * 100))}%")

    def _zoom_in(self) -> None:
        if self._view_mode.get() != "graph":
            self._view_mode.set("graph")
            self._on_view_changed()
        self._graph_panel.zoom_in()

    def _zoom_out(self) -> None:
        if self._view_mode.get() != "graph":
            self._view_mode.set("graph")
            self._on_view_changed()
        self._graph_panel.zoom_out()

    def _zoom_reset(self) -> None:
        if self._view_mode.get() != "graph":
            self._view_mode.set("graph")
            self._on_view_changed()
        self._graph_panel.reset_zoom()

    def _on_view_changed(self) -> None:
        mode = self._view_mode.get()
        if mode == "tree":
            self._graph_panel.pack_forget()
            self._tree_frame.pack(fill="both", expand=True)
        else:
            self._tree_frame.pack_forget()
            self._graph_panel.pack(fill="both", expand=True)
            self._graph_panel.draw_graph()

    def _tag_for(self, node: TreeNode, index: int) -> str:
        label = node.label.upper()
        if "ERRORNODE" in label or "INVALIDTOKENNODE" in label or "BROKEN" in label:
            return "error"
        if index == 0:
            return "root"
        if "→" in node.label:
            if any(k in label for k in ("FROM", "TABLE", "NAME")):
                return "table"
            if "AGGREGATE" in label:
                return "aggr"
            return "value"
        return "clause"
