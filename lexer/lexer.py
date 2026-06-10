"""
lexer/lexer.py
--------------
Character-level SQL scanner.

Refactored from m1/SQL_Tokenizer_Project/tokenizer.py with the following
improvements:
  - Returns (raw_tokens, errors) instead of printing and returning None
  - Error recovery: unknown characters are emitted as UNKNOWN raw tokens
    so the GUI can display them and diagnostics can block success
  - Handles \\n, \\t as whitespace
  - Numeric literals parsed correctly (digits and dot)
  - Position tracking (character index) for each raw token

The output of this module is a list of raw string tokens.
Classification into typed (type, value) tuples is done by classifier.py.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class RawToken:
    """A raw, unclassified string fragment from the source query."""
    value: str
    position: int   # character index where this token starts


@dataclass
class LexicalIssue:
    """Represents a lexical error or warning found during scanning."""
    code: str
    message: str
    position: int
    recovered: bool = False   # True if scanner continued past the issue


class Lexer:
    """
    Character-level SQL scanner.

    Scans a raw SQL query string and produces a flat list of RawToken
    objects, along with any lexical issues encountered.

    Usage::

        lexer = Lexer("SELECT name FROM students;")
        tokens, issues = lexer.scan()
    """

    # Characters that are treated as whitespace (separators between tokens)
    _WHITESPACE: frozenset[str] = frozenset({" ", "\t", "\n", "\r"})

    # Single-character delimiters and punctuation that always form their own token
    _SINGLE_CHAR_TOKENS: frozenset[str] = frozenset({
        ";", ",", "(", ")", "[", "]", ".",
    })

    # Characters that are illegal and trigger error recovery
    _ILLEGAL_CHARS: frozenset[str] = frozenset({"@", "#", "`", "~", "^", "&"})

    # Operator characters that may combine into two-character operators
    _OPERATOR_CHARS: frozenset[str] = frozenset({"=", "<", ">", "!", "+", "-", "/", "*", "%"})

    def __init__(self, query: str) -> None:
        self._query: str = query
        self._pos: int = 0
        self._tokens: list[RawToken] = []
        self._issues: list[LexicalIssue] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> tuple[list[RawToken], list[LexicalIssue]]:
        """
        Scan the entire query and return (tokens, issues).

        Returns:
            tokens: List of RawToken objects in source order.
            issues: List of LexicalIssue objects (errors and warnings).
        """
        self._tokens = []
        self._issues = []
        self._pos = 0

        # Empty query check
        if not self._query or not self._query.strip():
            self._issues.append(LexicalIssue(
                code="L003",
                message="Query is empty",
                position=0,
            ))
            return self._tokens, self._issues

        # Unclosed string pre-check
        if self._query.count("'") % 2 != 0:
            self._issues.append(LexicalIssue(
                code="L002",
                message="Unclosed string literal — missing closing quote",
                position=self._query.rfind("'"),
            ))
            # Still attempt to scan what we can

        while self._pos < len(self._query):
            char = self._query[self._pos]

            if char in self._WHITESPACE:
                self._pos += 1

            elif char == "'":
                self._scan_string_literal()

            elif char in self._ILLEGAL_CHARS:
                self._handle_unknown_char(char, illegal=True)

            elif self._pos + 1 < len(self._query) and self._is_two_char_operator():
                op = self._query[self._pos: self._pos + 2]
                self._emit(op)
                self._pos += 2

            elif char in self._OPERATOR_CHARS:
                self._emit(char)
                self._pos += 1

            elif char in self._SINGLE_CHAR_TOKENS:
                self._emit(char)
                self._pos += 1

            elif char.isdigit():
                self._scan_number()

            elif char.isalpha() or char == "_":
                self._scan_word()

            else:
                # Unexpected character — keep it visible as an UNKNOWN token
                # instead of silently skipping it. Parsing is stopped later
                # by the GUI/diagnostics layer, but tokenization continues
                # so the user can see exactly what failed.
                self._handle_unknown_char(char, illegal=False)

        return self._tokens, self._issues

    # ------------------------------------------------------------------
    # Private scanning helpers
    # ------------------------------------------------------------------

    def _emit(self, value: str) -> None:
        """Append a raw token at the current position."""
        self._tokens.append(RawToken(value=value, position=self._pos))

    def _scan_string_literal(self) -> None:
        """Scan a single-quoted string literal and emit it."""
        start = self._pos
        buf = "'"
        self._pos += 1  # skip opening quote

        while self._pos < len(self._query):
            ch = self._query[self._pos]
            buf += ch
            self._pos += 1
            if ch == "'":
                break   # closing quote found

        self._tokens.append(RawToken(value=buf, position=start))

    def _scan_number(self) -> None:
        """Scan an integer or floating-point literal."""
        start = self._pos
        buf = ""
        dot_seen = False

        while self._pos < len(self._query):
            ch = self._query[self._pos]
            if ch.isdigit():
                buf += ch
                self._pos += 1
            elif ch == "." and not dot_seen:
                dot_seen = True
                buf += ch
                self._pos += 1
            else:
                break

        self._tokens.append(RawToken(value=buf, position=start))

    def _scan_word(self) -> None:
        """Scan an alphanumeric word (keyword or identifier)."""
        start = self._pos
        buf = ""

        while self._pos < len(self._query):
            ch = self._query[self._pos]
            if ch.isalnum() or ch == "_":
                buf += ch
                self._pos += 1
            else:
                break

        self._tokens.append(RawToken(value=buf, position=start))

    def _is_two_char_operator(self) -> bool:
        """Return True if the current position starts a two-character operator."""
        two = self._query[self._pos: self._pos + 2]
        return two in {">=", "<=", "!=", "<>"}

    def _handle_unknown_char(self, char: str, *, illegal: bool = False) -> None:
        """Record an invalid character and emit it as a visible UNKNOWN token."""
        kind = "Illegal" if illegal else "Unknown"
        self._tokens.append(RawToken(value=char, position=self._pos))
        self._issues.append(LexicalIssue(
            code="L001",
            message=f"Lexical error: {kind.lower()} token '{char}' found at position {self._pos}",
            position=self._pos,
            recovered=False,
        ))
        self._pos += 1


def scan(query: str) -> tuple[list[RawToken], list[LexicalIssue]]:
    """
    Module-level convenience function.

    Args:
        query: Raw SQL query string.

    Returns:
        (tokens, issues) as produced by Lexer.scan().
    """
    return Lexer(query).scan()
