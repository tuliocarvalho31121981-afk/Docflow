"""
Core - Security
Autenticação e autorização via JWT/Supabase.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError

security = HTTPBearer(auto_error=False)

# Cache do cliente
_anon_client = None


def get_anon_client():
    """Retorna cliente Supabase com chave anônima."""
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(settings.supabase_url, settings.supabase_key)
    return _anon_client


class CurrentUser(BaseModel):
    """Usuário atual autenticado."""

    id: str
    auth_user_id: str
    email: str
    nome: str
    tipo: Optional[str] = None
    clinica_id: str
    perfil_id: Optional[str] = None
    permissoes: dict = {}
    access_token: str

    def has_permission(self, module: str, action: str) -> bool:
        """Verifica se usuário tem permissão."""
        # Admin tem todas permissões
        if self.tipo == "admin":
            return True

        module_perms = self.permissoes.get(module, "")
        return action in module_perms


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency para obter usuário atual via token JWT.
    Valida token com Supabase Auth e busca dados do usuário.
    """
    if not credentials:
        raise UnauthorizedError("Token não fornecido")

    token = credentials.credentials

    # Usa auth_service que já tem a validação implementada corretamente
    from app.auth.service import auth_service

    try:
        user_info = await auth_service.get_current_user(token)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            raise UnauthorizedError(e.detail)
        raise

    # Busca auth_user_id para construir CurrentUser
    from app.core.database import get_service_client
    service_client = get_service_client()

    user_result = service_client.table("usuarios").select(
        "id, auth_user_id, nome, email, tipo, clinica_id, perfil_id, ativo"
    ).eq("id", user_info.id).single().execute()

    if not user_result.data:
        raise UnauthorizedError("Usuário não cadastrado no sistema")

    user_data = user_result.data

    # Busca permissões do perfil
    permissoes = user_info.perfil.permissoes if user_info.perfil else {}

    return CurrentUser(
        id=str(user_data["id"]),
        auth_user_id=str(user_data["auth_user_id"]),
        email=user_data["email"],
        nome=user_data["nome"],
        tipo=user_data.get("tipo"),
        clinica_id=str(user_data["clinica_id"]),
        perfil_id=str(user_data["perfil_id"]) if user_data.get("perfil_id") else None,
        permissoes=permissoes,
        access_token=token
    )


def require_permission(module: str, action: str):
    """
    Dependency factory para verificar permissão específica.

    Actions:
        L = Listar/Ler
        C = Criar
        E = Editar
        X = Excluir

    Usage:
        @router.get("/items")
        async def list_items(current_user = Depends(require_permission("items", "L"))):
            ...
    """
    async def check_permission(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not current_user.has_permission(module, action):
            raise ForbiddenError(f"Sem permissão para {action} em {module}")
        return current_user

    return check_permission
