# -*- coding: utf-8 -*-
"""
Kanban - Router
Endpoints para gerenciamento do Kanban.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser, require_permission
from app.kanban.service import kanban_service
from app.kanban.schemas import (
    CardResponse,
    CardCreate,
    ChecklistItemUpdate,
    MoverCardRequest,
    KanbanResponse
)


router = APIRouter(prefix="/kanban", tags=["Kanban"])


# ============================================
# VISUALIZAÇÃO DO KANBAN
# ============================================

@router.get(
    "",
    response_model=KanbanResponse,
    summary="Lista cards do Kanban"
)
async def listar_kanban(
    fase: Optional[int] = Query(None, description="Filtrar por fase (0-4)"),
    data: Optional[str] = Query(None, description="Filtrar por data (YYYY-MM-DD)"),
    medico_id: Optional[str] = Query(None, description="Filtrar por médico"),
    current_user: CurrentUser = Depends(require_permission("kanban", "L"))
):
    """
    Lista todos os cards do Kanban agrupados por fase.
    
    Fases:
    - 0: Agendado
    - 1: Pré-Consulta
    - 2: Dia da Consulta
    - 3: Pós-Consulta
    - 4: Finalizado (não exibido por padrão)
    """
    return await kanban_service.listar_cards_kanban(
        current_user=current_user,
        fase=fase,
        data=data,
        medico_id=medico_id
    )


# ============================================
# CARDS
# ============================================

@router.get(
    "/cards/{card_id}",
    response_model=CardResponse,
    summary="Busca card por ID"
)
async def get_card(
    card_id: str,
    current_user: CurrentUser = Depends(require_permission("kanban", "L"))
):
    """Retorna detalhes de um card específico."""
    return await kanban_service.get_card(
        card_id=card_id,
        current_user=current_user
    )


@router.get(
    "/cards/by-agendamento/{agendamento_id}",
    response_model=CardResponse,
    summary="Busca card por agendamento"
)
async def get_card_by_agendamento(
    agendamento_id: str,
    current_user: CurrentUser = Depends(require_permission("kanban", "L"))
):
    """Retorna card associado a um agendamento."""
    return await kanban_service.get_card_by_agendamento(
        agendamento_id=agendamento_id,
        current_user=current_user
    )


@router.post(
    "/cards",
    response_model=CardResponse,
    summary="Cria novo card"
)
async def criar_card(
    data: CardCreate,
    current_user: CurrentUser = Depends(require_permission("kanban", "C"))
):
    """
    Cria novo card para um agendamento.
    
    Normalmente chamado automaticamente quando um agendamento é criado.
    """
    return await kanban_service.criar_card(
        agendamento_id=data.agendamento_id,
        current_user=current_user
    )


# ============================================
# CHECKLIST
# ============================================

@router.post(
    "/cards/{card_id}/checklist/{item_key}",
    response_model=CardResponse,
    summary="Atualiza item do checklist"
)
async def atualizar_checklist_item(
    card_id: str,
    item_key: str,
    data: ChecklistItemUpdate,
    current_user: CurrentUser = Depends(require_permission("kanban", "E"))
):
    """
    Marca/desmarca um item do checklist.
    
    Se todos os itens obrigatórios da fase forem concluídos,
    o card move automaticamente para a próxima fase.
    """
    return await kanban_service.atualizar_checklist_item(
        card_id=card_id,
        item_key=item_key,
        concluido=data.concluido,
        current_user=current_user,
        automatico=data.automatico,
        origem=data.origem
    )


# ============================================
# MOVIMENTAÇÃO
# ============================================

@router.post(
    "/cards/{card_id}/mover",
    response_model=CardResponse,
    summary="Move card para outra fase"
)
async def mover_card(
    card_id: str,
    data: MoverCardRequest,
    current_user: CurrentUser = Depends(require_permission("kanban", "E"))
):
    """
    Move card manualmente para outra fase.
    
    Normalmente a movimentação é automática via checklist,
    mas este endpoint permite forçar uma transição.
    """
    return await kanban_service.mover_card(
        card_id=card_id,
        fase=data.fase,
        current_user=current_user,
        subfase=data.subfase,
        automatico=data.automatico,
        motivo=data.motivo
    )


@router.patch(
    "/cards/{card_id}/subfase",
    response_model=CardResponse,
    summary="Atualiza subfase do card"
)
async def atualizar_subfase(
    card_id: str,
    subfase: str = Query(..., description="Nova subfase"),
    current_user: CurrentUser = Depends(require_permission("kanban", "E"))
):
    """
    Atualiza a subfase do card sem mudar a fase principal.
    
    Subfases por fase:
    - Fase 0: aguardando_confirmacao, confirmado
    - Fase 1: pendente, em_andamento, pronto
    - Fase 2: aguardando_checkin, em_espera, em_atendimento, finalizado
    - Fase 3: aguardando_soap, soap_pendente, concluido
    """
    return await kanban_service.atualizar_subfase(
        card_id=card_id,
        subfase=subfase,
        current_user=current_user
    )


# ============================================
# ENDPOINTS INTERNOS (para workflows)
# ============================================

@router.post(
    "/internal/cards/{card_id}/checklist/{item_key}",
    response_model=CardResponse,
    include_in_schema=False
)
async def internal_atualizar_checklist(
    card_id: str,
    item_key: str,
    data: ChecklistItemUpdate,
    current_user: CurrentUser = Depends(require_permission("kanban", "E"))
):
    """Endpoint interno para workflows atualizarem checklist."""
    return await kanban_service.atualizar_checklist_item(
        card_id=card_id,
        item_key=item_key,
        concluido=data.concluido,
        current_user=current_user,
        automatico=True,
        origem=data.origem
    )
