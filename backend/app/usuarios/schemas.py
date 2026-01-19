# app/usuarios/schemas.py
"""
Schemas para o módulo de Usuários
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class TipoUsuario(str, Enum):
    """Tipos de usuário no sistema"""
    ADMIN = "admin"
    MEDICO = "medico"
    RECEPCIONISTA = "recepcionista"
    FINANCEIRO = "financeiro"
    ENFERMEIRO = "enfermeiro"
    TECNICO = "tecnico"
    OUTRO = "outro"


# === Dados profissionais (médicos) ===

class DadosProfissionais(BaseModel):
    """Dados profissionais para médicos e outros profissionais de saúde"""
    crm: Optional[str] = Field(None, description="Número do CRM")
    crm_uf: Optional[str] = Field(None, max_length=2, description="UF do CRM")
    especialidade: Optional[str] = Field(None, description="Especialidade médica")
    registro_conselho: Optional[str] = Field(None, description="Registro em outro conselho")
    conselho_tipo: Optional[str] = Field(None, description="Tipo do conselho (COREN, CRO, etc)")


# === Requests ===

class UsuarioCreate(BaseModel):
    """Request para criar usuário"""
    nome: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    senha: str = Field(..., min_length=6, description="Senha para acesso")
    telefone: Optional[str] = Field(None, max_length=20)
    cpf: Optional[str] = Field(None, max_length=14)
    perfil_id: str = Field(..., description="ID do perfil de acesso")
    tipo: TipoUsuario = Field(TipoUsuario.OUTRO, description="Tipo do usuário")
    
    # Dados profissionais (opcional)
    crm: Optional[str] = None
    crm_uf: Optional[str] = None
    especialidade: Optional[str] = None
    registro_conselho: Optional[str] = None
    conselho_tipo: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Dr. João Silva",
                "email": "joao@clinica.com",
                "senha": "senha123",
                "telefone": "21999998888",
                "perfil_id": "uuid-do-perfil",
                "tipo": "medico",
                "crm": "12345",
                "crm_uf": "RJ",
                "especialidade": "Cardiologia"
            }
        }


class UsuarioUpdate(BaseModel):
    """Request para atualizar usuário"""
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    telefone: Optional[str] = Field(None, max_length=20)
    cpf: Optional[str] = Field(None, max_length=14)
    perfil_id: Optional[str] = None
    tipo: Optional[TipoUsuario] = None
    
    # Dados profissionais
    crm: Optional[str] = None
    crm_uf: Optional[str] = None
    especialidade: Optional[str] = None
    registro_conselho: Optional[str] = None
    conselho_tipo: Optional[str] = None
    
    # Avatar e assinatura
    avatar_url: Optional[str] = None
    assinatura_digital_url: Optional[str] = None


class UsuarioUpdateSenha(BaseModel):
    """Request para alterar senha"""
    senha_atual: str = Field(..., min_length=6)
    senha_nova: str = Field(..., min_length=6)


# === Responses ===

class PerfilResumo(BaseModel):
    """Resumo do perfil para exibição"""
    id: str
    nome: str


class UsuarioResponse(BaseModel):
    """Response com dados do usuário"""
    id: str
    nome: str
    email: str
    telefone: Optional[str] = None
    cpf: Optional[str] = None
    tipo: Optional[str] = None
    perfil: Optional[PerfilResumo] = None
    
    # Dados profissionais
    crm: Optional[str] = None
    crm_uf: Optional[str] = None
    especialidade: Optional[str] = None
    registro_conselho: Optional[str] = None
    conselho_tipo: Optional[str] = None
    
    # URLs
    avatar_url: Optional[str] = None
    assinatura_digital_url: Optional[str] = None
    
    # Status
    ativo: bool = True
    primeiro_acesso: bool = True
    ultimo_acesso: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class UsuarioListItem(BaseModel):
    """Item da lista de usuários (resumido)"""
    id: str
    nome: str
    email: str
    tipo: Optional[str] = None
    perfil_nome: Optional[str] = None
    ativo: bool = True
    ultimo_acesso: Optional[datetime] = None


class ListaUsuariosResponse(BaseModel):
    """Response com lista de usuários"""
    usuarios: list[UsuarioListItem]
    total: int
    ativos: int
    inativos: int
