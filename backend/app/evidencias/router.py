"""
Evidencias - Router
Endpoints da API de evidências documentais.

PADRÃO: Todos os endpoints passam current_user para o service.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import PaginatedResponse, SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.evidencias.schemas import (
    EvidenciaCreate,
    EvidenciaListItem,
    EvidenciaResponse,
    EvidenciasResumo,
    EvidenciaUpdate,
    VerificacaoEvidencias,
)
from app.evidencias.service import evidencia_service

router = APIRouter(prefix="/evidencias", tags=["Evidências"])


# ==========================================
# LISTAGEM
# ==========================================

@router.get(
    "",
    response_model=PaginatedResponse[EvidenciaListItem],
    summary="Listar Evidências",
)
async def list_evidencias(
    entidade: Optional[str] = Query(default=None, description="Tipo da entidade (paciente, agendamento, etc)"),
    entidade_id: Optional[UUID] = Query(default=None, description="ID da entidade"),
    tipo: Optional[str] = Query(default=None, description="Tipo da evidência"),
    categoria: Optional[str] = Query(default=None, description="Categoria"),
    ativo: Optional[bool] = Query(default=True, description="Somente ativos"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("evidencias", "L"))
):
    """Lista evidências com filtros."""
    return await evidencia_service.list(
        current_user=current_user,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id else None,
        tipo=tipo,
        categoria=categoria,
        ativo=ativo,
        page=page,
        per_page=per_page
    )


@router.get(
    "/resumo/{entidade}/{entidade_id}",
    response_model=EvidenciasResumo,
    summary="Resumo de Evidências",
)
async def get_resumo(
    entidade: str,
    entidade_id: UUID,
    current_user: CurrentUser = Depends(require_permission("evidencias", "L"))
):
    """Retorna resumo das evidências de uma entidade."""
    return await evidencia_service.get_resumo(
        entidade=entidade,
        entidade_id=str(entidade_id),
        current_user=current_user
    )


# ==========================================
# VERIFICAÇÃO
# ==========================================

@router.get(
    "/verificar/{entidade}/{entidade_id}/{acao}",
    response_model=VerificacaoEvidencias,
    summary="Verificar Evidências",
)
async def verificar_evidencias(
    entidade: str,
    entidade_id: UUID,
    acao: str,
    valor: Optional[float] = Query(default=None, description="Valor (para verificações baseadas em valor)"),
    perfil: Optional[str] = Query(default=None, description="Perfil do usuário"),
    current_user: CurrentUser = Depends(require_permission("evidencias", "L"))
):
    """
    Verifica se uma entidade tem as evidências necessárias para executar uma ação.
    
    Retorna se pode executar e lista de evidências faltando.
    """
    return await evidencia_service.verificar(
        entidade=entidade,
        entidade_id=str(entidade_id),
        acao=acao,
        current_user=current_user,
        valor=valor,
        perfil=perfil
    )


# ==========================================
# CRUD
# ==========================================

@router.get(
    "/{evidencia_id}",
    response_model=EvidenciaResponse,
    summary="Obter Evidência",
)
async def get_evidencia(
    evidencia_id: UUID,
    current_user: CurrentUser = Depends(require_permission("evidencias", "L"))
):
    """Retorna detalhes de uma evidência."""
    return await evidencia_service.get(
        id=str(evidencia_id),
        current_user=current_user
    )


@router.post(
    "",
    response_model=EvidenciaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Evidência",
)
async def create_evidencia(
    data: EvidenciaCreate,
    current_user: CurrentUser = Depends(require_permission("evidencias", "C"))
):
    """
    Cria nova evidência documental.
    
    A evidência é vinculada a uma entidade (paciente, agendamento, etc).
    """
    return await evidencia_service.create(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{evidencia_id}",
    response_model=EvidenciaResponse,
    summary="Atualizar Evidência",
)
async def update_evidencia(
    evidencia_id: UUID,
    data: EvidenciaUpdate,
    current_user: CurrentUser = Depends(require_permission("evidencias", "E"))
):
    """Atualiza dados da evidência."""
    return await evidencia_service.update(
        id=str(evidencia_id),
        data=data,
        current_user=current_user
    )


@router.delete(
    "/{evidencia_id}",
    response_model=SuccessResponse,
    summary="Invalidar Evidência",
)
async def invalidar_evidencia(
    evidencia_id: UUID,
    motivo: Optional[str] = Query(default=None, description="Motivo da invalidação"),
    current_user: CurrentUser = Depends(require_permission("evidencias", "X"))
):
    """
    Invalida evidência (soft delete).
    
    Evidências invalidadas ficam no histórico mas não são consideradas em verificações.
    """
    await evidencia_service.invalidar(
        id=str(evidencia_id),
        current_user=current_user,
        motivo=motivo
    )
    return SuccessResponse(message="Evidência invalidada com sucesso")
