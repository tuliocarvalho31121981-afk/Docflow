"""
CIDs - Schemas Pydantic
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# ESPECIALIDADES
# ============================================================================

class EspecialidadeBase(BaseModel):
    """Base para especialidade."""
    codigo: str = Field(..., description="Código único da especialidade")
    nome: str = Field(..., description="Nome da especialidade")
    descricao: Optional[str] = Field(None, description="Descrição")
    cor: Optional[str] = Field(None, description="Cor hex para UI")
    icone: Optional[str] = Field(None, description="Nome do ícone")


class EspecialidadeResponse(EspecialidadeBase):
    """Resposta de especialidade."""
    id: str
    ativa: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class EspecialidadeCreate(EspecialidadeBase):
    """Criar especialidade."""
    pass


# ============================================================================
# CIDs
# ============================================================================

class CIDBase(BaseModel):
    """Base para CID."""
    codigo: str = Field(..., description="Código CID-10 (ex: I10)")
    descricao: str = Field(..., description="Descrição completa")
    descricao_abreviada: Optional[str] = Field(None, description="Versão curta")


class CIDResponse(CIDBase):
    """Resposta de CID."""
    capitulo: Optional[str] = None
    grupo: Optional[str] = None
    categoria: Optional[str] = None
    ativo: bool = True

    # Campos de contexto (quando busca por especialidade)
    frequencia_uso: Optional[int] = 0
    favorito: Optional[bool] = False

    class Config:
        from_attributes = True


class CIDCreate(CIDBase):
    """Criar CID."""
    capitulo: Optional[str] = None
    grupo: Optional[str] = None
    categoria: Optional[str] = None


class CIDBuscaResponse(BaseModel):
    """Resposta de busca de CIDs."""
    items: List[CIDResponse]
    total: int
    especialidade_id: Optional[str] = None
    especialidade_nome: Optional[str] = None


# ============================================================================
# VINCULO ESPECIALIDADE x CID
# ============================================================================

class CIDEspecialidadeCreate(BaseModel):
    """Vincular CID a especialidade."""
    especialidade_id: str
    cid_codigo: str
    favorito: bool = False


class CIDEspecialidadeResponse(BaseModel):
    """Resposta de vínculo."""
    id: str
    especialidade_id: str
    cid_codigo: str
    frequencia_uso: int = 0
    favorito: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
