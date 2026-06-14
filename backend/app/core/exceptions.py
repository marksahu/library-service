"""
app/core/exceptions.py

Domain exception hierarchy.  Services raise these; the HTTP layer
translates them to the appropriate status codes in main.py.
This keeps every service module free of FastAPI imports.
"""
from __future__ import annotations


class LibraryError(Exception):
    """Base class for all application-level errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(LibraryError):
    """Raised when a requested resource does not exist."""


class ConflictError(LibraryError):
    """Raised when an operation violates a uniqueness or state constraint."""


class BusinessRuleError(LibraryError):
    """Raised when an operation violates a domain business rule."""


class DatabaseError(LibraryError):
    """Raised when an unexpected database-level error occurs."""
