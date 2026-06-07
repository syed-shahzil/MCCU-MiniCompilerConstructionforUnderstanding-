"""
parser/cursor.py
----------------
TokenCursor — a navigable cursor over a flat list of typed token tuples.

Directly ported from m2/parser_utils.py with import paths updated to use
the new project structure. All parser modules share this single cursor
implementation — no more duplicated navigation logic.

The cursor wraps a list of (token_type, token_value) tuples and provides
primitive read/advance/expect operations. All read operations are
non-destructive; only advance() moves the internal pointer.
"""

from __future__ import annotations
from typing import Any, NamedTuple

from error_handling.exceptions import UnexpectedEndOfInputError, UnexpectedTokenError


class Token(NamedTuple):
    """Immutable representation of a single classified token."""
    type: str
    value: str | int | float

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r})"


# Sentinel returned when the cursor is exhausted
EOF_TOKEN = Token(type="EOF", value="")


class TokenCursor:
    """
    A navigable cursor over a flat list of Token objects.

    Args:
        tokens: List of (token_type, token_value) tuples from the lexer.
    """

    def __init__(self, tokens: list[tuple[str, Any]]) -> None:
        self._tokens: list[Token] = [Token(type=t, value=v) for t, v in tokens]
        self._pos: int = 0

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    @property
    def position(self) -> int:
        """Current zero-based index into the token list."""
        return self._pos

    def is_at_end(self) -> bool:
        """Return True when all tokens have been consumed."""
        return self._pos >= len(self._tokens)

    def remaining(self) -> int:
        """Number of tokens not yet consumed."""
        return max(0, len(self._tokens) - self._pos)

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------

    def peek(self) -> Token:
        """Return the current token without advancing the cursor."""
        if self.is_at_end():
            return EOF_TOKEN
        return self._tokens[self._pos]

    def peek_type(self) -> str:
        """Return the type of the current token."""
        return self.peek().type

    def peek_value(self) -> Any:
        """Return the value of the current token."""
        return self.peek().value

    def advance(self) -> Token:
        """
        Return the current token and move the cursor one step forward.

        Raises:
            UnexpectedEndOfInputError: When called past the end of the stream.
        """
        if self.is_at_end():
            raise UnexpectedEndOfInputError(
                expected="more tokens",
                position=self._pos,
            )
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    # ------------------------------------------------------------------
    # Conditional helpers
    # ------------------------------------------------------------------

    def match(self, *token_types: str) -> bool:
        """Return True if the current token's type is among *token_types*."""
        return self.peek_type() in token_types

    def consume_if(self, *token_types: str) -> Token | None:
        """Advance and return the token only if its type matches."""
        if self.match(*token_types):
            return self.advance()
        return None

    def expect(self, token_type: str, context: str = "") -> Token:
        """
        Assert that the current token has *token_type*, then consume it.

        Args:
            token_type: Required token type string.
            context:    Human-friendly description (used in error messages).

        Raises:
            UnexpectedEndOfInputError: Stream exhausted.
            UnexpectedTokenError:      Wrong type encountered.
        """
        if self.is_at_end():
            description = context if context else token_type
            raise UnexpectedEndOfInputError(
                expected=description,
                position=self._pos,
            )
        current = self.peek()
        if current.type != token_type:
            description = context if context else token_type
            raise UnexpectedTokenError(
                expected=description,
                got=str(current.value),
                position=self._pos,
            )
        return self.advance()

    def expect_identifier(self, context: str = "identifier") -> Token:
        """Convenience: expect an IDENTIFIER token."""
        return self.expect("IDENTIFIER", context=context)

    def expect_value(self, context: str = "value") -> Token:
        """
        Expect a literal value token (NUMBER, FLOAT, or STRING).

        Raises:
            UnexpectedTokenError: If current token is not a literal value.
        """
        from config.token_types import WHERE_VALUE_TYPES
        if self.peek_type() not in WHERE_VALUE_TYPES:
            raise UnexpectedTokenError(
                expected=context,
                got=str(self.peek_value()),
                position=self._pos,
            )
        return self.advance()

    def expect_operator(self, context: str = "comparison operator") -> Token:
        """
        Expect a comparison operator token (EQ, NEQ, LT, GT, LTE, GTE).

        Raises:
            MissingOperatorError: If current token is not an operator.
        """
        from config.token_types import COMPARISON_OPERATOR_TYPES
        from error_handling.exceptions import MissingOperatorError
        if self.peek_type() not in COMPARISON_OPERATOR_TYPES:
            raise MissingOperatorError(position=self._pos)
        return self.advance()

    # ------------------------------------------------------------------
    # Lookahead
    # ------------------------------------------------------------------

    def lookahead(self, offset: int = 1) -> Token:
        """
        Return the token *offset* positions ahead without moving the cursor.

        Returns EOF_TOKEN if out of range.
        """
        target = self._pos + offset
        if target >= len(self._tokens):
            return EOF_TOKEN
        return self._tokens[target]

    # ------------------------------------------------------------------
    # Skip helpers
    # ------------------------------------------------------------------

    def skip_semicolons(self) -> None:
        """Consume any trailing SEMICOLON tokens silently."""
        while self.match("SEMICOLON"):
            self.advance()

    def ensure_exhausted(self) -> None:
        """
        Assert no tokens remain after a complete parse.

        Raises:
            ExtraTokensError: If unconsumed tokens remain.
        """
        self.skip_semicolons()
        if not self.is_at_end():
            from error_handling.exceptions import ExtraTokensError
            raise ExtraTokensError(
                token=str(self.peek_value()),
                position=self._pos,
            )
