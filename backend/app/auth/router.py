"""
Auth - Router
Endpoints de autenticação (login, logout, refresh token).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
    UserInfo,
)
from app.auth.service import auth_service
from app.core.security import CurrentUser, require_permission

router = APIRouter(prefix="/auth", tags=["Autenticação"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse, summary="Login")
async def login(request: LoginRequest):
    """
    Realiza login do usuário via Supabase Auth.
    Retorna tokens para autenticação nas demais rotas.
    """
    return await auth_service.login(request)


@router.post("/refresh", response_model=RefreshResponse, summary="Refresh Token")
async def refresh_token(request: RefreshRequest):
    """Renova o token usando refresh_token do Supabase."""
    return await auth_service.refresh(request.refresh_token)


@router.get("/me", response_model=UserInfo, summary="Usuário Atual")
async def get_me(
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """
    Retorna informações do usuário logado.

    Usa o mesmo padrão de autenticação dos demais endpoints.
    """
    # Busca dados completos usando o token do current_user
    user_info = await auth_service.get_current_user(current_user.access_token)
    return user_info


@router.post("/logout", response_model=LogoutResponse, summary="Logout")
async def logout(
    current_user: CurrentUser = Depends(require_permission("usuarios", "L"))
):
    """
    Realiza logout do usuário.

    O frontend deve descartar os tokens. O backend não mantém sessão,
    então basta o frontend remover o token local.

    Usa autenticação para registrar o logout (opcional, mas mantém
    padrão uniforme).
    """
    return LogoutResponse()
