"""
Auth - Schemas
DTOs para autenticação.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr


class PerfilInfo(BaseModel):
    """Informações do perfil do usuário."""
    
    id: str
    nome: str
    permissoes: dict = {}


class UserResponse(BaseModel):
    """Dados do usuário retornados no login."""
    
    id: str
    nome: str
    email: str
    tipo: Optional[str] = None
    clinica_id: str
    clinica_nome: str
    perfil: PerfilInfo


class LoginRequest(BaseModel):
    """Request de login."""
    
    email: EmailStr
    senha: str


class LoginResponse(BaseModel):
    """Response de login."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse  # ✅ Tipado ao invés de dict


class RefreshRequest(BaseModel):
    """Request de refresh token."""
    
    refresh_token: str


class RefreshResponse(BaseModel):
    """Response de refresh token."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """Informações do usuário logado."""
    
    id: str
    nome: str
    email: str
    tipo: Optional[str] = None
    clinica_id: str
    clinica_nome: str
    perfil: PerfilInfo  # ✅ Tipado ao invés de dict


class LogoutResponse(BaseModel):
    """Response de logout."""
    
    message: str = "Logout realizado com sucesso"
