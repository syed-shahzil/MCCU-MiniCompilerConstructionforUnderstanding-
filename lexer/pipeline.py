"""
lexer/pipeline.py
-----------------
Public API for the MCCU lexical analysis phase.

This module composes lexer.py (character scanner) and classifier.py
(token classifier) into a single easy-to-call function: run_lexer().

All other modules (parsers, GUI) should call run_lexer() — they should
not import lexer.py or classifier.py directly.

Usage::

    from lexer.pipeline import run_lexer

    result = run_lexer("SELECT name FROM students WHERE age > 20;")

    if result.has_lexical_errors:
        for issue in result.lexical_issues:
            print(issue)
    else:
        for token in result.tokens:
            print(token)
"""

from __future__ import annotations
from dataclasses import dataclass, field

from lexer.lexer import scan as lex_scan, RawToken, LexicalIssue
from lexer.classifier import classify, get_display_category


@dataclass
class LexerResult:
    """
    Complete result of the lexical analysis phase.

    Attributes:
        tokens:         Typed (type, value) tuples — input to parsers.
        raw_tokens:     Unclassified RawToken objects from the scanner.
        lexical_issues: Errors and warnings from the scanner.
        query:          The original query string.
    """
    tokens: list[tuple[str, str | int | float]]
    raw_tokens: list[RawToken]
    lexical_issues: list[LexicalIssue]
    query: str

    @property
    def has_lexical_errors(self) -> bool:
        """True if any non-recovered lexical issues were found."""
        return any(not i.recovered for i in self.lexical_issues)

    @property
    def token_count(self) -> int:
        return len(self.tokens)

    def get_display_rows(self) -> list[tuple[int, str, str, str]]:
        """
        Return token data formatted for GUI table display.

        Returns:
            List of (position, lexeme, token_type, category) tuples.
            position is 1-indexed for user-friendly display.
        """
        rows = []
        for i, (tt, tv) in enumerate(self.tokens, start=1):
            lexeme = str(tv)
            category = get_display_category(tt)
            rows.append((i, lexeme, tt, category))
        return rows

    def __repr__(self) -> str:
        return (
            f"LexerResult(tokens={self.token_count}, "
            f"issues={len(self.lexical_issues)}, "
            f"has_errors={self.has_lexical_errors})"
        )


def run_lexer(query: str) -> LexerResult:
    """
    Run the full lexical analysis pipeline on a SQL query string.

    This function:
      1. Scans the query character-by-character (lexer.py)
      2. Classifies each raw token into a typed tuple (classifier.py)
      3. Returns a structured LexerResult

    Args:
        query: The raw SQL query string entered by the user.

    Returns:
        A LexerResult containing tokens, raw fragments, and any issues.
    """
    raw_tokens, issues = lex_scan(query)
    typed_tokens = classify(raw_tokens)

    return LexerResult(
        tokens=typed_tokens,
        raw_tokens=raw_tokens,
        lexical_issues=issues,
        query=query,
    )
