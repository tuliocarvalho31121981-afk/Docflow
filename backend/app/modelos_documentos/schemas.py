"""
Modelos de Documentos - Schemas
DTOs para templates de receitas, atestados, exames e orientações.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import Field

from app.core.schemas import BaseSchema, TimestampMixin


# ============================================================================
# TIPOS
# ============================================================================

CategoriaDocumento = Literal[
    "Atestados",
    "Exames",
    "Orientações Médicas",
    "Receitas",
    "Outros"
]


# ============================================================================
# CREATE / UPDATE
# ============================================================================

class ModeloDocumentoCreate(BaseSchema):
    """Criar novo modelo de documento."""
    categoria: CategoriaDocumento = Field(..., description="Categoria do documento")
    titulo: str = Field(..., min_length=1, max_length=200, description="Título do modelo")
    conteudo: str = Field(..., min_length=1, description="Conteúdo/template do documento")
    uso_exclusivo_usuario_id: Optional[UUID] = Field(
        default=None,
        description="Se preenchido, modelo é privado deste usuário"
    )


class ModeloDocumentoUpdate(BaseSchema):
    """Atualizar modelo de documento."""
    categoria: Optional[CategoriaDocumento] = None
    titulo: Optional[str] = Field(default=None, min_length=1, max_length=200)
    conteudo: Optional[str] = Field(default=None, min_length=1)
    uso_exclusivo_usuario_id: Optional[UUID] = None
    ativo: Optional[bool] = None


# ============================================================================
# RESPONSE
# ============================================================================

class ModeloDocumentoResponse(BaseSchema, TimestampMixin):
    """Resposta de modelo de documento."""
    id: UUID
    clinica_id: UUID
    categoria: str
    titulo: str
    conteudo: str
    uso_exclusivo_usuario_id: Optional[UUID] = None
    ativo: bool = True
    created_by: Optional[UUID] = None


class ModeloDocumentoListItem(BaseSchema):
    """Item de listagem de modelos."""
    id: UUID
    categoria: str
    titulo: str
    ativo: bool = True
    uso_exclusivo_usuario_id: Optional[UUID] = None


# ============================================================================
# FILTROS
# ============================================================================

class ModeloDocumentoFiltros(BaseSchema):
    """Filtros para busca de modelos."""
    categoria: Optional[CategoriaDocumento] = None
    apenas_ativos: bool = True
    incluir_privados: bool = True
