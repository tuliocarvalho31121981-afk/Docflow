"""
Clinicas - Router
Endpoints da API de clínicas e perfis.

PADRÃO: Todos os endpoints passam current_user para o service.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.clinicas.schemas import (
    ClinicaResponse,
    ClinicaUpdate,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
    PerfilCreate,
    PerfilListItem,
    PerfilResponse,
    PerfilUpdate,
)
from app.clinicas.service import clinica_service, perfil_service

router = APIRouter(prefix="/clinica", tags=["Clínica"])


# ==========================================
# CLÍNICA
# ==========================================

@router.get(
    "",
    response_model=ClinicaResponse,
    summary="Obter Clínica Atual",
)
async def get_clinica(
    current_user: CurrentUser = Depends(require_permission("configuracoes", "L"))
):
    """Retorna dados da clínica do usuário logado."""
    return await clinica_service.get(current_user=current_user)


@router.patch(
    "",
    response_model=ClinicaResponse,
    summary="Atualizar Clínica",
)
async def update_clinica(
    data: ClinicaUpdate,
    current_user: CurrentUser = Depends(require_permission("configuracoes", "E"))
):
    """Atualiza dados da clínica."""
    return await clinica_service.update(
        data=data,
        current_user=current_user
    )


# ==========================================
# CONFIGURAÇÕES
# ==========================================

@router.get(
    "/configuracoes",
    response_model=ConfiguracaoResponse,
    summary="Obter Configurações",
)
async def get_configuracoes(
    current_user: CurrentUser = Depends(require_permission("configuracoes", "L"))
):
    """Retorna configurações da clínica."""
    return await clinica_service.get_configuracoes(current_user=current_user)


@router.patch(
    "/configuracoes",
    response_model=ConfiguracaoResponse,
    summary="Atualizar Configurações",
)
async def update_configuracoes(
    data: ConfiguracaoUpdate,
    current_user: CurrentUser = Depends(require_permission("configuracoes", "E"))
):
    """Atualiza configurações da clínica."""
    return await clinica_service.update_configuracoes(
        data=data.model_dump(exclude_none=True),
        current_user=current_user
    )


# ==========================================
# PERFIS
# ==========================================

@router.get(
    "/perfis",
    response_model=list[PerfilListItem],
    summary="Listar Perfis",
)
async def list_perfis(
    incluir_inativos: bool = Query(default=False, description="Incluir perfis inativos"),
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """Lista perfis de acesso da clínica."""
    return await perfil_service.list(
        current_user=current_user,
        incluir_inativos=incluir_inativos
    )


@router.get(
    "/perfis/{perfil_id}",
    response_model=PerfilResponse,
    summary="Obter Perfil",
)
async def get_perfil(
    perfil_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """Retorna detalhes de um perfil."""
    return await perfil_service.get(
        id=str(perfil_id),
        current_user=current_user
    )


@router.post(
    "/perfis",
    response_model=PerfilResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Perfil",
)
async def create_perfil(
    data: PerfilCreate,
    current_user: CurrentUser = Depends(require_permission("usuarios", "C"))
):
    """Cria novo perfil de acesso."""
    return await perfil_service.create(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/perfis/{perfil_id}",
    response_model=PerfilResponse,
    summary="Atualizar Perfil",
)
async def update_perfil(
    perfil_id: UUID,
    data: PerfilUpdate,
    current_user: CurrentUser = Depends(require_permission("usuarios", "E"))
):
    """Atualiza perfil de acesso."""
    return await perfil_service.update(
        id=str(perfil_id),
        data=data,
        current_user=current_user
    )


@router.delete(
    "/perfis/{perfil_id}",
    response_model=SuccessResponse,
    summary="Remover Perfil",
)
async def delete_perfil(
    perfil_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios", "X"))
):
    """Remove perfil (soft delete)."""
    await perfil_service.delete(
        id=str(perfil_id),
        current_user=current_user
    )
    return SuccessResponse(message="Perfil removido com sucesso")
