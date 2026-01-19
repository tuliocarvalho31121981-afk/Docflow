"""
Modelos de Documentos - Router
Endpoints da API para templates de documentos médicos.

PERMISSÕES:
- prontuario: C=criar, L=ler, E=editar, X=deletar
- Modelos podem ter uso exclusivo (privados de um usuário)
"""
from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import PaginatedResponse, SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.modelos_documentos.schemas import (
    ModeloDocumentoCreate,
    ModeloDocumentoUpdate,
    ModeloDocumentoResponse,
    ModeloDocumentoListItem,
    CategoriaDocumento,
)
from app.modelos_documentos.service import modelos_documentos_service

router = APIRouter(prefix="/modelos-documentos", tags=["Modelos de Documentos"])


# ============================================================================
# LISTAGEM
# ============================================================================

@router.get(
    "",
    response_model=PaginatedResponse[ModeloDocumentoListItem],
    summary="Listar Modelos",
)
async def list_modelos(
    categoria: Optional[str] = Query(
        default=None,
        description="Filtrar por categoria (Atestados, Exames, Orientações Médicas, Receitas, Outros)"
    ),
    apenas_ativos: bool = Query(default=True, description="Apenas modelos ativos"),
    incluir_privados: bool = Query(default=True, description="Incluir modelos privados"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """
    Lista modelos de documentos com filtros.

    Categorias disponíveis:
    - Atestados
    - Exames
    - Orientações Médicas
    - Receitas
    - Outros
    """
    return await modelos_documentos_service.list_modelos(
        current_user=current_user,
        categoria=categoria,
        apenas_ativos=apenas_ativos,
        incluir_privados=incluir_privados,
        page=page,
        per_page=per_page
    )


@router.get(
    "/por-categoria",
    response_model=dict,
    summary="Listar por Categoria",
)
async def list_por_categoria(
    apenas_ativos: bool = Query(default=True, description="Apenas modelos ativos"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """
    Lista modelos agrupados por categoria.

    Retorna um dicionário onde cada chave é uma categoria
    e o valor é a lista de modelos daquela categoria.

    Exemplo de retorno:
    ```json
    {
        "Atestados": [
            {"id": "...", "titulo": "Aptidão física", ...},
            {"id": "...", "titulo": "Dispensa do trabalho", ...}
        ],
        "Exames": [
            {"id": "...", "titulo": "Hemograma", ...}
        ]
    }
    ```
    """
    return await modelos_documentos_service.list_por_categoria(
        current_user=current_user,
        apenas_ativos=apenas_ativos
    )


@router.get(
    "/contagem",
    response_model=List[dict],
    summary="Contagem por Categoria",
)
async def contar_por_categoria(
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """
    Conta modelos por categoria.

    Retorna lista com categoria e total.
    """
    return await modelos_documentos_service.contar_por_categoria(
        current_user=current_user
    )


# ============================================================================
# CRUD
# ============================================================================

@router.get(
    "/{modelo_id}",
    response_model=ModeloDocumentoResponse,
    summary="Obter Modelo",
)
async def get_modelo(
    modelo_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca modelo de documento por ID."""
    return await modelos_documentos_service.get_modelo(
        id=str(modelo_id),
        current_user=current_user
    )


@router.post(
    "",
    response_model=ModeloDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Modelo",
)
async def create_modelo(
    data: ModeloDocumentoCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Cria novo modelo de documento.

    O modelo pode ser:
    - **Público** (uso_exclusivo_usuario_id = null): visível para todos da clínica
    - **Privado** (uso_exclusivo_usuario_id = UUID): visível apenas para o usuário
    """
    return await modelos_documentos_service.create_modelo(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{modelo_id}",
    response_model=ModeloDocumentoResponse,
    summary="Atualizar Modelo",
)
async def update_modelo(
    modelo_id: UUID,
    data: ModeloDocumentoUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza modelo de documento."""
    return await modelos_documentos_service.update_modelo(
        id=str(modelo_id),
        data=data,
        current_user=current_user
    )


@router.delete(
    "/{modelo_id}",
    response_model=SuccessResponse,
    summary="Remover Modelo",
)
async def delete_modelo(
    modelo_id: UUID,
    permanente: bool = Query(default=False, description="Remoção permanente (sem soft delete)"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "X"))
):
    """
    Remove modelo de documento.

    Por padrão faz soft delete (desativa).
    Use `permanente=true` para remover permanentemente.
    """
    await modelos_documentos_service.delete_modelo(
        id=str(modelo_id),
        current_user=current_user,
        soft_delete=not permanente
    )

    return SuccessResponse(
        message="Modelo removido com sucesso" if permanente else "Modelo desativado com sucesso"
    )


# ============================================================================
# AÇÕES
# ============================================================================

@router.post(
    "/{modelo_id}/duplicar",
    response_model=ModeloDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicar Modelo",
)
async def duplicar_modelo(
    modelo_id: UUID,
    novo_titulo: Optional[str] = Query(default=None, description="Título para a cópia"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Duplica um modelo existente.

    Útil para criar variações de um template.
    Se `novo_titulo` não for informado, usa "Título original (cópia)".
    """
    return await modelos_documentos_service.duplicar_modelo(
        id=str(modelo_id),
        novo_titulo=novo_titulo,
        current_user=current_user
    )


@router.post(
    "/{modelo_id}/reativar",
    response_model=ModeloDocumentoResponse,
    summary="Reativar Modelo",
)
async def reativar_modelo(
    modelo_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Reativa modelo desativado."""
    return await modelos_documentos_service.update_modelo(
        id=str(modelo_id),
        data=ModeloDocumentoUpdate(ativo=True),
        current_user=current_user
    )
