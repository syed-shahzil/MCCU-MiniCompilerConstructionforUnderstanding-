"""
app.py
------
Single executable entry point for the MCCU application.

Run with:
    python app.py

This launches the full Tkinter GUI that drives the MCCU compiler pipeline:
  Lexical Analysis → Syntax Parsing → AST Generation → Diagnostics
"""

import sys
import os

# Ensure the project root is on sys.path so all package imports resolve
# regardless of where the script is launched from.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tkinter as tk

from gui.main_window import MainWindow


def main() -> None:
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
