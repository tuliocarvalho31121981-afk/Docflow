"""
Agenda - Router
Endpoints da API de agendamentos.

PADRÃO: Todos os endpoints passam current_user para o service.
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import PaginatedResponse, SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.core.database import get_authenticated_db
from app.agenda.schemas import (
    AgendamentoCreate,
    AgendamentoListItem,
    AgendamentoResponse,
    AgendamentoStatusUpdate,
    AgendamentoUpdate,
    SlotDisponivel,
    TipoConsultaResponse,
)
from app.agenda.service import agenda_service

router = APIRouter(prefix="/agenda", tags=["Agenda"])


# ==========================================
# TIPOS DE CONSULTA
# ==========================================

@router.get(
    "/tipos-consulta",
    response_model=list[TipoConsultaResponse],
    summary="Listar Tipos de Consulta",
)
async def list_tipos_consulta(
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Lista tipos de consulta disponíveis."""
    db = get_authenticated_db(current_user.access_token)
    tipos = await db.select(
        table="tipos_consulta",
        filters={"ativo": True},
        order_by="nome"
    )
    return tipos


# ==========================================
# SLOTS DISPONÍVEIS
# ==========================================

@router.get(
    "/slots",
    response_model=list[SlotDisponivel],
    summary="Buscar Slots Disponíveis",
)
async def get_slots_disponiveis(
    data_inicio: date = Query(..., description="Data inicial"),
    data_fim: Optional[date] = Query(default=None, description="Data final"),
    medico_id: Optional[UUID] = Query(default=None, description="Filtrar por médico"),
    tipo_consulta_id: Optional[UUID] = Query(default=None, description="Filtrar por tipo"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """
    Retorna slots disponíveis para agendamento.
    """
    return await agenda_service.get_slots_disponiveis(
        current_user=current_user,
        data_inicio=data_inicio,
        data_fim=data_fim,
        medico_id=str(medico_id) if medico_id else None,
        tipo_consulta_id=str(tipo_consulta_id) if tipo_consulta_id else None
    )


# ==========================================
# MÉTRICAS (ANTES de /{agendamento_id}!)
# ==========================================

@router.get(
    "/metricas",
    summary="Métricas da Agenda",
)
async def get_metricas(
    data: date = Query(default=None, description="Data para métricas (default: hoje)"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """
    Retorna métricas da agenda para uma data.
    """
    return await agenda_service.get_metricas(
        current_user=current_user,
        data=data
    )


# ==========================================
# BLOQUEIOS (ANTES de /{agendamento_id}!)
# ==========================================

@router.get(
    "/bloqueios",
    summary="Listar Bloqueios",
)
async def list_bloqueios(
    data_inicio: date = Query(default=None, description="Data inicial (default: hoje)"),
    data_fim: Optional[date] = Query(default=None, description="Data final"),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """
    Lista bloqueios de agenda.
    """
    return await agenda_service.list_bloqueios(
        current_user=current_user,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


# ==========================================
# AGENDAMENTOS - LISTAGEM
# ==========================================

@router.get(
    "/agendamentos",
    response_model=PaginatedResponse[AgendamentoListItem],
    summary="Listar Agendamentos",
)
async def list_agendamentos(
    data: Optional[date] = Query(default=None, description="Data específica"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial"),
    data_fim: Optional[date] = Query(default=None, description="Data final"),
    medico_id: Optional[UUID] = Query(default=None, description="Filtrar por médico"),
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    status: Optional[str] = Query(default=None, description="Filtrar por status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """
    Lista agendamentos com filtros.
    RLS garante que só retorna agendamentos da clínica do usuário.
    """
    return await agenda_service.list(
        current_user=current_user,
        data=data,
        data_inicio=data_inicio,
        data_fim=data_fim,
        medico_id=str(medico_id) if medico_id else None,
        paciente_id=str(paciente_id) if paciente_id else None,
        status=status,
        page=page,
        per_page=per_page
    )


# ==========================================
# AGENDAMENTOS - CRUD (rotas com {id} por último!)
# ==========================================

@router.get(
    "/{agendamento_id}",
    response_model=AgendamentoResponse,
    summary="Obter Agendamento",
)
async def get_agendamento(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "L"))
):
    """Retorna dados completos de um agendamento."""
    return await agenda_service.get(
        id=str(agendamento_id),
        current_user=current_user
    )


@router.post(
    "/agendamentos",
    response_model=AgendamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Agendamento",
)
async def create_agendamento(
    data: AgendamentoCreate,
    current_user: CurrentUser = Depends(require_permission("agenda", "C"))
):
    """
    Cria novo agendamento.
    clinica_id é pego automaticamente do usuário logado.
    """
    return await agenda_service.create(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{agendamento_id}",
    response_model=AgendamentoResponse,
    summary="Atualizar Agendamento",
)
async def update_agendamento(
    agendamento_id: UUID,
    data: AgendamentoUpdate,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """
    Atualiza dados do agendamento.
    RLS garante que só pode atualizar agendamentos da própria clínica.
    """
    return await agenda_service.update(
        id=str(agendamento_id),
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{agendamento_id}/status",
    response_model=AgendamentoResponse,
    summary="Atualizar Status",
)
async def update_agendamento_status(
    agendamento_id: UUID,
    data: AgendamentoStatusUpdate,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """
    Atualiza status do agendamento.

    **Transições permitidas:**
    - agendado → confirmado, cancelado, remarcado
    - confirmado → aguardando, faltou, cancelado, remarcado
    - aguardando → em_atendimento, faltou, cancelado
    - em_atendimento → atendido
    """
    return await agenda_service.update_status(
        id=str(agendamento_id),
        data=data,
        current_user=current_user
    )


# ==========================================
# AÇÕES RÁPIDAS
# ==========================================

@router.post(
    "/{agendamento_id}/confirmar",
    response_model=AgendamentoResponse,
    summary="Confirmar Agendamento",
)
async def confirmar_agendamento(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Confirma agendamento (atalho para status=confirmado)."""
    return await agenda_service.confirmar(
        id=str(agendamento_id),
        current_user=current_user
    )


@router.post(
    "/{agendamento_id}/cancelar",
    response_model=AgendamentoResponse,
    summary="Cancelar Agendamento",
)
async def cancelar_agendamento(
    agendamento_id: UUID,
    motivo: Optional[str] = Query(default=None, description="Motivo do cancelamento"),
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Cancela agendamento."""
    return await agenda_service.cancelar(
        id=str(agendamento_id),
        current_user=current_user,
        motivo=motivo
    )


@router.post(
    "/{agendamento_id}/chegada",
    response_model=AgendamentoResponse,
    summary="Registrar Chegada",
)
async def registrar_chegada(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Registra chegada do paciente (check-in)."""
    return await agenda_service.registrar_chegada(
        id=str(agendamento_id),
        current_user=current_user
    )


@router.post(
    "/{agendamento_id}/iniciar",
    response_model=AgendamentoResponse,
    summary="Iniciar Atendimento",
)
async def iniciar_atendimento(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Inicia atendimento (chamou o paciente)."""
    return await agenda_service.iniciar_atendimento(
        id=str(agendamento_id),
        current_user=current_user
    )


@router.post(
    "/{agendamento_id}/finalizar",
    response_model=AgendamentoResponse,
    summary="Finalizar Atendimento",
)
async def finalizar_atendimento(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Finaliza atendimento."""
    return await agenda_service.finalizar_atendimento(
        id=str(agendamento_id),
        current_user=current_user
    )


@router.post(
    "/{agendamento_id}/falta",
    response_model=AgendamentoResponse,
    summary="Marcar Falta",
)
async def marcar_falta(
    agendamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("agenda", "E"))
):
    """Marca falta do paciente."""
    return await agenda_service.marcar_falta(
        id=str(agendamento_id),
        current_user=current_user
    )
