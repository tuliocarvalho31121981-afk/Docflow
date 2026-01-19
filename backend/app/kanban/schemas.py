# -*- coding: utf-8 -*-
"""
Kanban - Schemas
DTOs para o módulo de Kanban.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, List, Any

from pydantic import BaseModel, Field


# ============================================
# CHECKLIST
# ============================================

class ChecklistItem(BaseModel):
    """Item individual do checklist."""
    label: str
    obrigatorio: bool = False
    auto: bool = False
    concluido: bool = False
    concluido_em: Optional[datetime] = None
    concluido_por: Optional[str] = None
    automatico: bool = False
    origem: Optional[str] = None


class ChecklistItemUpdate(BaseModel):
    """Payload para atualizar item do checklist."""
    concluido: bool = True
    automatico: bool = False
    origem: Optional[str] = None


# ============================================
# HISTÓRICO
# ============================================

class HistoricoFase(BaseModel):
    """Registro de mudança de fase."""
    fase_anterior: int
    fase_nova: int
    transicao_em: datetime
    automatico: bool = False
    motivo: Optional[str] = None
    usuario_id: Optional[str] = None


# ============================================
# CARD
# ============================================

class CardBase(BaseModel):
    """Dados base do card."""
    agendamento_id: str
    fase: int = Field(0, ge=0, le=4)
    subfase: Optional[str] = None
    status: str = "ativo"


class CardCreate(BaseModel):
    """Payload para criar card."""
    agendamento_id: str


class CardResponse(BaseModel):
    """Resposta de card."""
    id: str
    clinica_id: str
    agendamento_id: str
    paciente_id: str
    medico_id: str
    fase: int
    fase_nome: Optional[str] = None
    subfase: Optional[str] = None
    checklist: Dict[str, Any] = {}
    status: str
    historico_fases: List[HistoricoFase] = []
    created_at: datetime
    updated_at: datetime
    
    # Dados expandidos (opcionais)
    paciente: Optional[Dict[str, Any]] = None
    medico: Optional[Dict[str, Any]] = None
    agendamento: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================
# MOVIMENTAÇÃO
# ============================================

class MoverCardRequest(BaseModel):
    """Payload para mover card."""
    fase: int = Field(..., ge=0, le=4, description="Fase destino (0-4)")
    subfase: Optional[str] = Field(None, description="Subfase dentro da fase")
    automatico: bool = Field(False, description="Se foi movido automaticamente")
    motivo: Optional[str] = Field(None, description="Motivo da movimentação")


# ============================================
# KANBAN VIEW
# ============================================

class FaseInfo(BaseModel):
    """Informações de uma fase do Kanban."""
    nome: str
    subfases: List[str] = []
    cards: List[CardResponse] = []


class KanbanResponse(BaseModel):
    """Resposta da visualização do Kanban."""
    fases: Dict[int, FaseInfo]
    totais: Dict[str, int]


# ============================================
# FILTROS
# ============================================

class KanbanFilters(BaseModel):
    """Filtros para listagem do Kanban."""
    fase: Optional[int] = None
    subfase: Optional[str] = None
    data: Optional[str] = None
    medico_id: Optional[str] = None
    paciente_id: Optional[str] = None
    status: Optional[str] = "ativo"
