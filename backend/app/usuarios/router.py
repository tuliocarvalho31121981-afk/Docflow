# app/usuarios/router.py
"""
Usuarios - Router
Endpoints da API de usuários.

Endpoints:
- GET    /usuarios          - Lista usuários da clínica
- GET    /usuarios/me       - Dados do usuário logado
- GET    /usuarios/{id}     - Detalhes do usuário
- POST   /usuarios          - Criar usuário
- PATCH  /usuarios/{id}     - Atualizar usuário
- PATCH  /usuarios/me       - Atualizar próprio usuário
- DELETE /usuarios/{id}     - Desativar usuário
- POST   /usuarios/{id}/reativar - Reativar usuário
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.usuarios.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    ListaUsuariosResponse,
)
from app.usuarios.service import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


# ==========================================
# USUÁRIO LOGADO (ME)
# ==========================================

@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Meus Dados",
)
async def get_me(
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """Retorna dados do usuário logado."""
    return await usuario_service.get_me(current_user=current_user)


@router.patch(
    "/me",
    response_model=UsuarioResponse,
    summary="Atualizar Meus Dados",
)
async def update_me(
    data: UsuarioUpdate,
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """
    Atualiza dados do próprio usuário.
    
    Campos permitidos: nome, telefone, avatar_url.
    Para alterar outros campos, use o endpoint de admin.
    """
    return await usuario_service.update_me(
        data=data,
        current_user=current_user
    )


# ==========================================
# CRUD USUÁRIOS (ADMIN)
# ==========================================

@router.get(
    "",
    response_model=ListaUsuariosResponse,
    summary="Listar Usuários",
)
async def list_usuarios(
    incluir_inativos: bool = Query(default=False, description="Incluir usuários inativos"),
    tipo: Optional[str] = Query(default=None, description="Filtrar por tipo (admin, medico, etc)"),
    busca: Optional[str] = Query(default=None, description="Buscar por nome ou email"),
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """Lista todos os usuários da clínica."""
    return await usuario_service.list(
        current_user=current_user,
        incluir_inativos=incluir_inativos,
        tipo=tipo,
        busca=busca
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obter Usuário",
)
async def get_usuario(
    usuario_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """Retorna detalhes de um usuário."""
    return await usuario_service.get(
        id=str(usuario_id),
        current_user=current_user
    )


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Usuário",
)
async def create_usuario(
    data: UsuarioCreate,
    current_user: CurrentUser = Depends(require_permission("usuarios", "C"))
):
    """
    Cria novo usuário.
    
    - Cria no Supabase Auth (email + senha)
    - Cria registro na tabela usuarios
    - Vincula ao perfil de acesso
    """
    return await usuario_service.create(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualizar Usuário",
)
async def update_usuario(
    usuario_id: UUID,
    data: UsuarioUpdate,
    current_user: CurrentUser = Depends(require_permission("usuarios", "E"))
):
    """Atualiza dados de um usuário."""
    return await usuario_service.update(
        id=str(usuario_id),
        data=data,
        current_user=current_user
    )


@router.delete(
    "/{usuario_id}",
    response_model=SuccessResponse,
    summary="Desativar Usuário",
)
async def delete_usuario(
    usuario_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios", "X"))
):
    """
    Desativa um usuário (soft delete).
    
    - NÃO remove do Supabase Auth
    - Usuário não consegue mais logar
    - Pode ser reativado depois
    """
    await usuario_service.delete(
        id=str(usuario_id),
        current_user=current_user
    )
    return SuccessResponse(message="Usuário desativado com sucesso")


@router.post(
    "/{usuario_id}/reativar",
    response_model=UsuarioResponse,
    summary="Reativar Usuário",
)
async def reativar_usuario(
    usuario_id: UUID,
    current_user: CurrentUser = Depends(require_permission("usuarios", "E"))
):
    """Reativa um usuário que foi desativado."""
    return await usuario_service.reativar(
        id=str(usuario_id),
        current_user=current_user
    )
