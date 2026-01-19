"""
Core - Schemas
Schemas base e utilitários para DTOs.
"""
from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Schema base com configurações padrão."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )


class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp."""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Response paginada genérica."""
    
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class SuccessResponse(BaseModel):
    """Response de sucesso simples."""
    
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Response de erro."""
    
    error: dict
