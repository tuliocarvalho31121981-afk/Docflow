"""
Core - Módulo central com configurações, exceções e utilitários.
"""

from app.core.config import settings
from app.core.database import get_authenticated_db, SupabaseClient
from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import CurrentUser, get_current_user, require_permission

__all__ = [
    "settings",
    "get_authenticated_db",
    "SupabaseClient",
    "AppException",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "UnauthorizedError",
    "ValidationError",
    "CurrentUser",
    "get_current_user",
    "require_permission",
]
