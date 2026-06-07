"""
error_handling/diagnostics.py
------------------------------
DiagnosticsCollector — gathers lexical errors, syntax errors, warnings,
and informational messages from the entire compiler pipeline into a single
structured list for display in the GUI diagnostics panel.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

DiagnosticLevel = Literal["ERROR", "WARNING", "INFO"]


@dataclass
class Diagnostic:
    """A single compiler diagnostic message."""

    level: DiagnosticLevel        # "ERROR", "WARNING", or "INFO"
    code: str                     # e.g. "L001", "S004", "W002"
    message: str                  # Human-readable description
    position: int | None = None   # Token / character position (0-indexed)
    recovered: bool = False       # True if compiler continued past this issue
    detail: str = ""              # Optional extra detail for educational display

    @property
    def phase(self) -> str:
        """Return the pipeline phase based on code prefix."""
        if self.code.startswith("L"):
            return "Lexical"
        if self.code.startswith("S"):
            return "Syntax"
        if self.code.startswith("W"):
            return "Warning"
        if self.code.startswith("I"):
            return "Info"
        return "Unknown"

    @property
    def icon(self) -> str:
        """Return a Unicode icon representing the diagnostic level."""
        icons = {"ERROR": "✖", "WARNING": "⚠", "INFO": "ℹ"}
        return icons.get(self.level, "•")

    def __str__(self) -> str:
        pos_str = f" (pos {self.position})" if self.position is not None else ""
        rec_str = " [recovered]" if self.recovered else ""
        return f"{self.icon} [{self.code}] {self.message}{pos_str}{rec_str}"


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class DiagnosticsCollector:
    """
    Accumulates diagnostic messages from all pipeline phases.

    Usage::

        dc = DiagnosticsCollector()
        dc.add_error("S004", "Expected FROM keyword", position=3)
        dc.add_warning("W002", "Missing trailing semicolon")
        dc.add_info("I001", "Recovery applied", detail="Skipped '@'")

        for diag in dc.get_all():
            print(diag)
    """

    def __init__(self) -> None:
        self._diagnostics: list[Diagnostic] = []

    # ------------------------------------------------------------------
    # Adding diagnostics
    # ------------------------------------------------------------------

    def add_error(
        self,
        code: str,
        message: str,
        position: int | None = None,
        recovered: bool = False,
        detail: str = "",
    ) -> None:
        """Add an ERROR-level diagnostic."""
        self._diagnostics.append(Diagnostic(
            level="ERROR",
            code=code,
            message=message,
            position=position,
            recovered=recovered,
            detail=detail,
        ))

    def add_warning(
        self,
        code: str,
        message: str,
        position: int | None = None,
        detail: str = "",
    ) -> None:
        """Add a WARNING-level diagnostic."""
        self._diagnostics.append(Diagnostic(
            level="WARNING",
            code=code,
            message=message,
            position=position,
            detail=detail,
        ))

    def add_info(
        self,
        code: str,
        message: str,
        position: int | None = None,
        detail: str = "",
    ) -> None:
        """Add an INFO-level diagnostic."""
        self._diagnostics.append(Diagnostic(
            level="INFO",
            code=code,
            message=message,
            position=position,
            detail=detail,
        ))

    def add_from_exception(self, exc: Exception) -> None:
        """
        Automatically extract and add a diagnostic from an MCCU exception.

        Args:
            exc: Any MCCUError subclass instance.
        """
        from error_handling.exceptions import MCCUError
        if isinstance(exc, MCCUError):
            self.add_error(
                code=exc.code or "S001",
                message=str(exc).split("] ", 1)[-1].split(" at position")[0],
                position=exc.position,
            )
        else:
            self.add_error(code="S000", message=str(exc))

    def add_from_lexical_issues(self, issues: list) -> None:
        """
        Add diagnostics from a list of LexicalIssue objects (from lexer.py).

        Args:
            issues: List of LexicalIssue dataclass instances.
        """
        for issue in issues:
            if issue.recovered:
                self.add_info(
                    code="I002",
                    message=issue.message,
                    position=issue.position,
                    detail="Error recovery applied — tokenization continued",
                )
            else:
                self.add_error(
                    code=issue.code,
                    message=issue.message,
                    position=issue.position,
                )

    # ------------------------------------------------------------------
    # Querying diagnostics
    # ------------------------------------------------------------------

    def get_all(self) -> list[Diagnostic]:
        """Return all diagnostics in insertion order."""
        return list(self._diagnostics)

    def get_errors(self) -> list[Diagnostic]:
        """Return only ERROR-level diagnostics."""
        return [d for d in self._diagnostics if d.level == "ERROR"]

    def get_warnings(self) -> list[Diagnostic]:
        """Return only WARNING-level diagnostics."""
        return [d for d in self._diagnostics if d.level == "WARNING"]

    def get_info(self) -> list[Diagnostic]:
        """Return only INFO-level diagnostics."""
        return [d for d in self._diagnostics if d.level == "INFO"]

    def has_errors(self) -> bool:
        """Return True if any ERROR-level diagnostics have been recorded."""
        return any(d.level == "ERROR" for d in self._diagnostics)

    def has_warnings(self) -> bool:
        """Return True if any WARNING-level diagnostics have been recorded."""
        return any(d.level == "WARNING" for d in self._diagnostics)

    def is_clean(self) -> bool:
        """Return True if no errors or warnings were recorded."""
        return not self.has_errors() and not self.has_warnings()

    def error_count(self) -> int:
        return sum(1 for d in self._diagnostics if d.level == "ERROR")

    def warning_count(self) -> int:
        return sum(1 for d in self._diagnostics if d.level == "WARNING")

    def clear(self) -> None:
        """Remove all recorded diagnostics."""
        self._diagnostics.clear()

    def __len__(self) -> int:
        return len(self._diagnostics)

    def __repr__(self) -> str:
        return (
            f"DiagnosticsCollector("
            f"errors={self.error_count()}, "
            f"warnings={self.warning_count()}, "
            f"info={len(self.get_info())})"
        )
