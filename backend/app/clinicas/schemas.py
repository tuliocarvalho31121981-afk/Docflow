"""
Clinicas - Schemas
DTOs para clínicas, perfis e configurações.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.schemas import BaseSchema


# ==========================================
# CLINICA
# ==========================================

class ClinicaBase(BaseModel):
    """Campos comuns de clínica."""
    nome: str = Field(..., min_length=2, max_length=255)
    nome_fantasia: Optional[str] = Field(default=None, max_length=255)
    cnpj: Optional[str] = Field(default=None, pattern=r"^\d{14}$")
    telefone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    
    # Endereço
    logradouro: Optional[str] = Field(default=None, max_length=255)
    numero: Optional[str] = Field(default=None, max_length=20)
    complemento: Optional[str] = Field(default=None, max_length=100)
    bairro: Optional[str] = Field(default=None, max_length=100)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, pattern=r"^[A-Z]{2}$")
    cep: Optional[str] = Field(default=None, pattern=r"^\d{8}$")
    
    # Configurações
    fuso_horario: str = Field(default="America/Sao_Paulo", max_length=50)


class ClinicaCreate(ClinicaBase):
    """Dados para criar clínica."""
    pass


class ClinicaUpdate(BaseModel):
    """Dados para atualizar clínica."""
    nome: Optional[str] = Field(default=None, min_length=2, max_length=255)
    nome_fantasia: Optional[str] = Field(default=None, max_length=255)
    telefone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    logo_url: Optional[str] = None


class ClinicaResponse(BaseSchema):
    """Resposta com dados da clínica."""
    id: UUID
    nome: str
    nome_fantasia: Optional[str]
    cnpj: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    logradouro: Optional[str]
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    cep: Optional[str]
    fuso_horario: str
    logo_url: Optional[str]
    ativo: bool
    created_at: datetime
    updated_at: datetime


class ClinicaListItem(BaseSchema):
    """Item da lista de clínicas."""
    id: UUID
    nome: str
    nome_fantasia: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    ativo: bool


# ==========================================
# PERFIL
# ==========================================

class PerfilBase(BaseModel):
    """Campos comuns de perfil."""
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = None
    permissoes: dict = Field(default_factory=dict)


class PerfilCreate(PerfilBase):
    """Dados para criar perfil."""
    pass


class PerfilUpdate(BaseModel):
    """Dados para atualizar perfil."""
    nome: Optional[str] = Field(default=None, min_length=2, max_length=100)
    descricao: Optional[str] = None
    permissoes: Optional[dict] = None


class PerfilResponse(BaseSchema):
    """Resposta com dados do perfil."""
    id: UUID
    clinica_id: UUID
    nome: str
    descricao: Optional[str]
    permissoes: dict
    is_sistema: bool
    ativo: bool
    created_at: datetime


class PerfilListItem(BaseSchema):
    """Item da lista de perfis."""
    id: UUID
    nome: str
    descricao: Optional[str]
    is_sistema: bool
    ativo: bool


# ==========================================
# CONFIGURAÇÕES
# ==========================================

class ConfiguracaoUpdate(BaseModel):
    """Atualização de configurações da clínica."""
    
    # Agenda
    agenda_antecedencia_minima: Optional[int] = Field(default=None, ge=0, le=720)  # horas
    agenda_antecedencia_maxima: Optional[int] = Field(default=None, ge=1, le=365)  # dias
    agenda_permitir_encaixe: Optional[bool] = None
    agenda_intervalo_padrao: Optional[int] = None
    
    # Agendamento Online
    agendamento_online_ativo: Optional[bool] = None
    agendamento_online_antecedencia: Optional[int] = None
    
    # WhatsApp
    whatsapp_confirmacao_ativo: Optional[bool] = None
    whatsapp_confirmacao_horas: Optional[int] = None
    whatsapp_lembrete_ativo: Optional[bool] = None
    whatsapp_lembrete_horas: Optional[int] = None
    whatsapp_nps_ativo: Optional[bool] = None
    whatsapp_nps_horas: Optional[int] = None
    
    # Financeiro
    financeiro_alerta_saldo_minimo: Optional[Decimal] = None
    financeiro_alerta_contas_vencer: Optional[int] = None
    financeiro_fechamento_dia: Optional[int] = None
    
    # IA
    ia_transcricao_auto: Optional[bool] = None
    ia_soap_auto: Optional[bool] = None
    ia_modelo_preferido: Optional[str] = None
    
    # Notificações
    notificacoes_email_ativo: Optional[bool] = None
    notificacoes_push_ativo: Optional[bool] = None
    
    # Segurança
    seguranca_2fa_obrigatorio: Optional[bool] = None
    seguranca_sessao_timeout: Optional[int] = None


class ConfiguracaoResponse(BaseSchema):
    """Configurações da clínica."""
    
    clinica_id: UUID
    
    # Agenda
    agenda_antecedencia_minima: int
    agenda_antecedencia_maxima: int
    agenda_permitir_encaixe: bool
    agenda_intervalo_padrao: int
    
    # Agendamento Online
    agendamento_online_ativo: bool
    agendamento_online_antecedencia: int
    
    # WhatsApp
    whatsapp_confirmacao_ativo: bool
    whatsapp_confirmacao_horas: int
    whatsapp_lembrete_ativo: bool
    whatsapp_lembrete_horas: int
    whatsapp_nps_ativo: bool
    whatsapp_nps_horas: int
    
    # Financeiro
    financeiro_alerta_saldo_minimo: Decimal
    financeiro_alerta_contas_vencer: int
    financeiro_fechamento_dia: int
    
    # IA
    ia_transcricao_auto: bool
    ia_soap_auto: bool
    ia_modelo_preferido: str
    
    # Notificações
    notificacoes_email_ativo: bool
    notificacoes_push_ativo: bool
    
    # Segurança
    seguranca_2fa_obrigatorio: bool
    seguranca_sessao_timeout: int
