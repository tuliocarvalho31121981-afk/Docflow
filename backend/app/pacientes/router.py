"""
Pacientes - Router
Endpoints da API de pacientes.

PADRÃO: Todos os endpoints passam current_user para o service.
O service usa get_authenticated_db(current_user.access_token).
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import PaginatedResponse, SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.pacientes.schemas import (
    PacienteBuscaResponse,
    PacienteCreate,
    PacienteListItem,
    PacienteResponse,
    PacienteResumo,
    PacienteUpdate,
)
from app.pacientes.service import paciente_service

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


# ==========================================
# LISTAGEM E BUSCA
# ==========================================

@router.get(
    "",
    response_model=PaginatedResponse[PacienteListItem],
    summary="Listar Pacientes",
    description="Lista pacientes com paginação e filtros"
)
async def list_pacientes(
    page: int = Query(default=1, ge=1, description="Página"),
    per_page: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(default=None, description="Busca por nome, CPF ou telefone"),
    ativo: Optional[bool] = Query(default=None, description="Filtrar por status ativo/inativo"),
    convenio_id: Optional[UUID] = Query(default=None, description="Filtrar por convênio"),
    sort: str = Query(default="nome", description="Campo para ordenar"),
    order: str = Query(default="asc", pattern="^(asc|desc)$", description="Ordem"),
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Lista pacientes da clínica.
    
    RLS garante que só retorna pacientes da clínica do usuário.
    """
    return await paciente_service.list(
        current_user=current_user,
        page=page,
        per_page=per_page,
        search=search,
        ativo=ativo,
        convenio_id=str(convenio_id) if convenio_id else None,
        sort=sort,
        order=order
    )


@router.get(
    "/autocomplete",
    response_model=list[PacienteResumo],
    summary="Autocomplete de Pacientes",
    description="Busca rápida para autocomplete"
)
async def autocomplete_pacientes(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(default=10, ge=1, le=50, description="Limite de resultados"),
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Autocomplete para busca rápida de pacientes.
    Busca por nome, CPF ou telefone.
    """
    return await paciente_service.autocomplete(
        current_user=current_user,
        termo=q,
        limit=limit
    )


@router.get(
    "/buscar/telefone/{telefone}",
    response_model=PacienteBuscaResponse,
    summary="Buscar por Telefone",
    description="Busca paciente por número de telefone/WhatsApp"
)
async def buscar_por_telefone(
    telefone: str,
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Busca paciente por telefone.
    Útil para identificar paciente no WhatsApp.
    """
    paciente = await paciente_service.buscar_por_telefone(
        telefone=telefone,
        current_user=current_user
    )
    
    return PacienteBuscaResponse(
        encontrado=paciente is not None,
        paciente=paciente
    )


@router.get(
    "/buscar/cpf/{cpf}",
    response_model=PacienteBuscaResponse,
    summary="Buscar por CPF",
    description="Busca paciente por CPF"
)
async def buscar_por_cpf(
    cpf: str,
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Busca paciente por CPF.
    """
    paciente = await paciente_service.buscar_por_cpf(
        cpf=cpf,
        current_user=current_user
    )
    
    return PacienteBuscaResponse(
        encontrado=paciente is not None,
        paciente=paciente
    )


# ==========================================
# CRUD
# ==========================================

@router.get(
    "/{paciente_id}",
    response_model=PacienteResponse,
    summary="Obter Paciente",
    description="Retorna dados completos de um paciente"
)
async def get_paciente(
    paciente_id: UUID,
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Retorna dados completos do paciente.
    RLS garante que só pode acessar pacientes da própria clínica.
    """
    return await paciente_service.get(
        id=str(paciente_id),
        current_user=current_user
    )


@router.post(
    "",
    response_model=PacienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Paciente",
    description="Cadastra novo paciente"
)
async def create_paciente(
    data: PacienteCreate,
    current_user: CurrentUser = Depends(require_permission("pacientes", "C"))
):
    """
    Cadastra novo paciente.
    clinica_id é pego automaticamente do usuário logado.
    """
    return await paciente_service.create(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{paciente_id}",
    response_model=PacienteResponse,
    summary="Atualizar Paciente",
    description="Atualiza dados do paciente"
)
async def update_paciente(
    paciente_id: UUID,
    data: PacienteUpdate,
    current_user: CurrentUser = Depends(require_permission("pacientes", "E"))
):
    """
    Atualiza dados do paciente.
    RLS garante que só pode atualizar pacientes da própria clínica.
    """
    return await paciente_service.update(
        id=str(paciente_id),
        data=data,
        current_user=current_user
    )


@router.delete(
    "/{paciente_id}",
    response_model=SuccessResponse,
    summary="Inativar Paciente",
    description="Inativa paciente (soft delete)"
)
async def delete_paciente(
    paciente_id: UUID,
    current_user: CurrentUser = Depends(require_permission("pacientes", "X"))
):
    """
    Inativa paciente (soft delete).
    RLS garante que só pode inativar pacientes da própria clínica.
    """
    await paciente_service.delete(
        id=str(paciente_id),
        current_user=current_user
    )
    
    return SuccessResponse(message="Paciente inativado com sucesso")
