"""
CIDs - Router (Endpoints da API)
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.security import CurrentUser, get_current_user
from app.cids.schemas import (
    EspecialidadeResponse,
    CIDResponse,
    CIDBuscaResponse,
)
from app.cids.service import cids_service

router = APIRouter(prefix="/cids", tags=["CIDs"])


# ============================================================================
# ESPECIALIDADES
# ============================================================================


@router.get(
    "/especialidades",
    response_model=List[EspecialidadeResponse],
    summary="Listar Especialidades",
)
async def list_especialidades(
    apenas_ativas: bool = Query(default=True, description="Apenas ativas"),
):
    """
    Lista todas as especialidades médicas disponíveis.

    Usado para:
    - Configurar especialidade do médico
    - Filtrar CIDs por especialidade
    """
    return await cids_service.list_especialidades(apenas_ativas=apenas_ativas)


@router.get(
    "/especialidades/{especialidade_id}",
    response_model=EspecialidadeResponse,
    summary="Obter Especialidade",
)
async def get_especialidade(especialidade_id: UUID):
    """Busca especialidade por ID."""
    esp = await cids_service.get_especialidade(str(especialidade_id))
    if not esp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Especialidade não encontrada",
        )
    return esp


@router.get(
    "/especialidades/codigo/{codigo}",
    response_model=EspecialidadeResponse,
    summary="Obter Especialidade por Código",
)
async def get_especialidade_by_codigo(codigo: str):
    """Busca especialidade por código (ex: 'cardiologia')."""
    esp = await cids_service.get_especialidade_by_codigo(codigo)
    if not esp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Especialidade não encontrada",
        )
    return esp


# ============================================================================
# CIDs
# ============================================================================


@router.get(
    "",
    response_model=CIDBuscaResponse,
    summary="Buscar CIDs",
)
async def buscar_cids(
    search: Optional[str] = Query(
        default=None,
        description="Busca por código ou descrição",
        min_length=1,
    ),
    especialidade_id: Optional[UUID] = Query(
        default=None,
        description="Filtrar por especialidade",
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Limite de resultados"),
):
    """
    Busca CIDs com filtros.

    **Se especialidade_id for informado:**
    - Retorna apenas CIDs vinculados à especialidade
    - Ordena por favoritos e frequência de uso
    - Ideal para autocomplete no prontuário

    **Se especialidade_id não for informado:**
    - Busca em todos os CIDs
    - Ordena por código
    """
    return await cids_service.buscar_cids(
        search=search,
        especialidade_id=str(especialidade_id) if especialidade_id else None,
        limit=limit,
    )


@router.get(
    "/{codigo}",
    response_model=CIDResponse,
    summary="Obter CID por Código",
)
async def get_cid(codigo: str):
    """Busca CID por código (ex: I10)."""
    cid = await cids_service.get_cid(codigo)
    if not cid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CID não encontrado",
        )
    return cid


@router.get(
    "/favoritos/{especialidade_id}",
    response_model=List[CIDResponse],
    summary="CIDs Favoritos",
)
async def get_cids_favoritos(
    especialidade_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Retorna CIDs marcados como favoritos para a especialidade.

    Útil para mostrar atalhos rápidos no prontuário.
    """
    return await cids_service.get_cids_favoritos(
        especialidade_id=str(especialidade_id),
        limit=limit,
    )


@router.post(
    "/uso/{especialidade_id}/{cid_codigo}",
    summary="Registrar Uso do CID",
)
async def registrar_uso_cid(
    especialidade_id: UUID,
    cid_codigo: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Registra uso de um CID pelo médico.

    Incrementa contador de frequência para melhorar ordenação por relevância.
    Chamado automaticamente quando médico seleciona um CID no SOAP.
    """
    await cids_service.incrementar_uso_cid(
        especialidade_id=str(especialidade_id),
        cid_codigo=cid_codigo,
    )
    return {"status": "ok", "message": "Uso registrado"}


@router.post(
    "/favorito/{especialidade_id}/{cid_codigo}",
    summary="Toggle Favorito",
)
async def toggle_favorito(
    especialidade_id: UUID,
    cid_codigo: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Alterna status de favorito do CID para a especialidade.

    - Se não era favorito, torna favorito
    - Se já era favorito, remove dos favoritos
    """
    novo_status = await cids_service.toggle_favorito(
        especialidade_id=str(especialidade_id),
        cid_codigo=cid_codigo,
    )
    return {"favorito": novo_status}
