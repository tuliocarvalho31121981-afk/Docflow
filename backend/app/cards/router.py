"""
Cards - Router
Endpoints da API de cards do Kanban.

ESTRUTURA:
- 4 Fases = 4 Colunas
- /cards/kanban/{fase} - Retorna cards de uma fase
- /cards/kanban - Retorna todas as 4 fases
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.security import CurrentUser, require_permission
from app.cards.schemas import (
    CardCreate,
    CardCreateRetorno,
    CardDocumentoCreate,
    CardDocumentoResponse,
    CardHistoricoResponse,
    CardKanban,
    CardMoverFase,
    CardResponse,
    CardUpdate,
    CardVincularAgendamento,
    ChecklistItem,
    ChecklistUpdate,
    CardMensagemResponse,
)
from app.cards.service import card_service

router = APIRouter(prefix="/cards", tags=["Cards"])


# ==========================================
# KANBAN
# ==========================================

@router.get(
    "/kanban",
    response_model=list[CardKanban],
    summary="Kanban Completo (4 Fases)",
)
async def get_kanban_completo(
    data: Optional[date] = Query(default=None, description="Filtrar por data (Fase 2)"),
    medico_id: Optional[UUID] = Query(default=None, description="Filtrar por médico"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna todas as 4 fases do Kanban."""
    return await card_service.get_kanban_completo(
        current_user=current_user,
        data=data,
        medico_id=str(medico_id) if medico_id else None
    )


@router.get(
    "/kanban/{fase}",
    response_model=CardKanban,
    summary="Kanban por Fase",
)
async def get_kanban(
    fase: int = Path(..., ge=0, le=3, description="Fase do kanban (0-3)"),
    data: Optional[date] = Query(default=None, description="Filtrar por data (Fase 2)"),
    medico_id: Optional[UUID] = Query(default=None, description="Filtrar por médico"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna cards de uma fase do Kanban."""
    return await card_service.get_kanban(
        current_user=current_user,
        fase=fase,
        data=data,
        medico_id=str(medico_id) if medico_id else None
    )


# ==========================================
# CRUD
# ==========================================

@router.post(
    "",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Card",
)
async def create_card(
    data: CardCreate,
    current_user: CurrentUser = Depends(require_permission("agenda", "C"))
):
    """Cria novo card (Fase 0)."""
    return await card_service.create(data=data, current_user=current_user)


@router.post(
    "/retorno",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Card de Retorno",
)
async def create_card_retorno(
    data: CardCreateRetorno,
    current_user: CurrentUser = Depends(require_permission("agenda", "C"))
):
    """Cria card de retorno (derivado de outro card)."""
    return await card_service.create_retorno(data=data, current_user=current_user)


@router.get(
    "/{card_id}",
    response_model=CardResponse,
    summary="Obter Card",
)
async def get_card(
    card_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna detalhes de um card."""
    return await card_service.get(id=str(card_id), current_user=current_user)


@router.patch(
    "/{card_id}",
    response_model=CardResponse,
    summary="Atualizar Card",
)
async def update_card(
    card_id: UUID,
    data: CardUpdate,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Atualiza dados do card."""
    return await card_service.update(
        id=str(card_id),
        data=data,
        current_user=current_user
    )


# ==========================================
# MOVIMENTAÇÃO
# ==========================================

@router.post(
    "/{card_id}/mover",
    response_model=CardResponse,
    summary="Mover Card de Fase",
)
async def mover_card(
    card_id: UUID,
    data: CardMoverFase,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Move card para outra fase. Valida se checklist obrigatório está completo."""
    return await card_service.mover_fase(
        id=str(card_id),
        data=data,
        current_user=current_user
    )


@router.post(
    "/{card_id}/vincular-agendamento",
    response_model=CardResponse,
    summary="Vincular Agendamento",
)
async def vincular_agendamento(
    card_id: UUID,
    data: CardVincularAgendamento,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Vincula agendamento ao card e move para Fase 1."""
    return await card_service.vincular_agendamento(
        id=str(card_id),
        data=data,
        current_user=current_user
    )


# ==========================================
# CHECKLIST
# ==========================================

@router.get(
    "/{card_id}/checklist",
    response_model=list[ChecklistItem],
    summary="Obter Checklist",
)
async def get_checklist(
    card_id: UUID,
    fase: Optional[int] = Query(default=None, ge=0, le=3, description="Filtrar por fase"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna checklist do card."""
    return await card_service.get_checklist(
        card_id=str(card_id),
        current_user=current_user,
        fase=fase
    )


@router.patch(
    "/{card_id}/checklist/{item_id}",
    response_model=ChecklistItem,
    summary="Marcar Item Checklist",
)
async def marcar_checklist(
    card_id: UUID,
    item_id: UUID,
    data: ChecklistUpdate,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Marca/desmarca item do checklist."""
    return await card_service.marcar_checklist(
        card_id=str(card_id),
        item_id=str(item_id),
        concluido=data.concluido,
        current_user=current_user
    )


# ==========================================
# HISTÓRICO
# ==========================================

@router.get(
    "/{card_id}/historico",
    response_model=list[CardHistoricoResponse],
    summary="Obter Histórico",
)
async def get_historico(
    card_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna histórico de eventos do card."""
    return await card_service.get_historico(
        card_id=str(card_id),
        current_user=current_user
    )


# ==========================================
# DOCUMENTOS
# ==========================================

@router.get(
    "/{card_id}/documentos",
    response_model=list[CardDocumentoResponse],
    summary="Listar Documentos",
)
async def list_documentos(
    card_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Lista documentos do card."""
    return await card_service.get_documentos(
        card_id=str(card_id),
        current_user=current_user
    )


@router.post(
    "/{card_id}/documentos",
    response_model=CardDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar Documento",
)
async def add_documento(
    card_id: UUID,
    data: CardDocumentoCreate,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Adiciona documento ao card."""
    return await card_service.add_documento(
        card_id=str(card_id),
        data=data,
        current_user=current_user
    )


# ==========================================
# MENSAGENS
# ==========================================

@router.get(
    "/{card_id}/mensagens",
    response_model=list[CardMensagemResponse],
    summary="Listar Mensagens",
)
async def list_mensagens(
    card_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Lista mensagens do card (WhatsApp, email, SMS)."""
    return await card_service.get_mensagens(
        card_id=str(card_id),
        current_user=current_user
    )
