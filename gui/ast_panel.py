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
from typing import Any

from gui.styles import Colors, Fonts
from ast.visualizer import build_tree_nodes, render_text_tree, TreeNode


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
    Supports click-and-drag panning.
    """
    def __init__(self, parent: Any, **kwargs: Any) -> None:
        super().__init__(parent, style="TFrame", **kwargs)
        self._root_node: GraphNode | None = None
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

        # Tip label
        tip = ttk.Label(
            self,
            text="💡 Tip: Click and drag to pan the graph  ·  Double-click to reset view",
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
            if any(k in label_upper for k in ("SELECT", "DELETE", "DROP", "INSERT", "UPDATE")):
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

        level_height = 80
        sibling_gap = 24

        # 1. Measure label text to determine sizes
        def measure(node: GraphNode) -> None:
            char_width = 8.5
            text_len = len(node.label)
            node.width = max(130.0, text_len * char_width + 24.0)
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
                    width=2,
                    arrow=tk.LAST,
                    arrowshape=(9, 11, 4),
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

            # Draw slightly rounded box using polygon smooth curves
            r = 6.0
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
                width=1.5,
                smooth=True,
            )

            # Node label text
            self.canvas.create_text(
                node.x, node.y,
                text=node.label,
                fill=fg,
                font=Fonts.CODE_SMALL,
                justify="center",
            )

            for child in node.children:
                draw_nodes(child)

        draw_nodes(self._root_node)

        # Adjust scroll region to contain the whole tree structure
        max_y = max(n.y + n.height/2 for n in all_nodes)
        self.canvas.configure(scrollregion=(0, 0, max_x + 60, max_y + 60))


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

        # View 1: Canvas Graph View
        self._graph_panel = ASTVisualGraph(self.content_container)
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
        if index == 0:
            return "root"
        if "→" in node.label:
            if any(k in label for k in ("FROM", "TABLE", "NAME")):
                return "table"
            if "AGGREGATE" in label:
                return "aggr"
            return "value"
        return "clause"
