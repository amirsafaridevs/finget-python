"""Exceptions raised by the Finget Python SDK."""

from __future__ import annotations

from typing import Any


class FingetError(Exception):
    """Base error for client-side validation failures."""


class ApiError(FingetError):
    """HTTP or transport failure talking to the Finget API."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        error_code: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.error_code = error_code
        self.body: dict[str, Any] = body or {}
