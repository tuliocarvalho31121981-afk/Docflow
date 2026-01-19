"""
Pacientes - Schemas
DTOs para entrada e saída de dados de pacientes.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.core.schemas import BaseSchema, TimestampMixin
from app.core.utils import format_cpf, format_telefone, validate_cpf


# ==========================================
# CREATE
# ==========================================

class PacienteCreate(BaseSchema):
    """Schema para criar paciente."""

    # Obrigatórios
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    telefone: str = Field(..., min_length=10, max_length=20, description="Telefone principal")

    # Opcionais mas importantes
    nome_social: Optional[str] = Field(default=None, max_length=255, description="Nome social")
    cpf: Optional[str] = Field(default=None, max_length=14, description="CPF")
    rg: Optional[str] = Field(default=None, max_length=20, description="RG")
    data_nascimento: Optional[date] = Field(default=None, description="Data de nascimento")
    sexo: Optional[str] = Field(default=None, pattern="^[MFO]$", description="M/F/O")
    estado_civil: Optional[str] = Field(default=None, max_length=20, description="Estado civil")
    profissao: Optional[str] = Field(default=None, max_length=100, description="Profissão")
    email: Optional[str] = Field(default=None, max_length=255, description="Email")
    celular: Optional[str] = Field(default=None, max_length=20, description="Celular")
    whatsapp: Optional[str] = Field(default=None, max_length=20, description="WhatsApp")

    # Endereço
    cep: Optional[str] = Field(default=None, max_length=10)
    logradouro: Optional[str] = Field(default=None, max_length=255)
    numero: Optional[str] = Field(default=None, max_length=20)
    complemento: Optional[str] = Field(default=None, max_length=100)
    bairro: Optional[str] = Field(default=None, max_length=100)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, max_length=2)

    # Responsável/Contato de emergência
    responsavel_nome: Optional[str] = Field(default=None, max_length=255)
    responsavel_cpf: Optional[str] = Field(default=None, max_length=14)
    responsavel_telefone: Optional[str] = Field(default=None, max_length=20)
    responsavel_parentesco: Optional[str] = Field(default=None, max_length=50)

    # Convênio
    convenio_id: Optional[UUID] = Field(default=None, description="ID do convênio")
    convenio_numero: Optional[str] = Field(default=None, max_length=50)
    convenio_validade: Optional[date] = Field(default=None)

    # Médico preferencial
    medico_preferencial_id: Optional[UUID] = Field(default=None)

    # Observações e saúde
    observacoes: Optional[str] = Field(default=None, description="Observações gerais")
    alergias: Optional[str] = Field(default=None, description="Alergias")
    medicamentos_uso: Optional[str] = Field(default=None, description="Medicamentos em uso")

    # Marketing
    como_conheceu: Optional[str] = Field(default=None, max_length=100)
    indicado_por: Optional[UUID] = Field(default=None)

    @field_validator("cpf", "responsavel_cpf")
    @classmethod
    def validate_cpf_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cpf = format_cpf(v)
        if not validate_cpf(cpf):
            raise ValueError("CPF inválido")
        return cpf

    @field_validator("telefone", "celular", "whatsapp", "responsavel_telefone")
    @classmethod
    def validate_telefone_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        telefone = format_telefone(v)
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")
        return telefone


# ==========================================
# UPDATE
# ==========================================

class PacienteUpdate(BaseSchema):
    """Schema para atualizar paciente (todos opcionais)."""

    nome: Optional[str] = Field(default=None, min_length=3, max_length=255)
    nome_social: Optional[str] = Field(default=None, max_length=255)
    telefone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    cpf: Optional[str] = Field(default=None, max_length=14)
    rg: Optional[str] = Field(default=None, max_length=20)
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = Field(default=None, pattern="^[MFO]$")
    estado_civil: Optional[str] = Field(default=None, max_length=20)
    profissao: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    celular: Optional[str] = Field(default=None, max_length=20)
    whatsapp: Optional[str] = Field(default=None, max_length=20)

    cep: Optional[str] = Field(default=None, max_length=10)
    logradouro: Optional[str] = Field(default=None, max_length=255)
    numero: Optional[str] = Field(default=None, max_length=20)
    complemento: Optional[str] = Field(default=None, max_length=100)
    bairro: Optional[str] = Field(default=None, max_length=100)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, max_length=2)

    responsavel_nome: Optional[str] = Field(default=None, max_length=255)
    responsavel_cpf: Optional[str] = Field(default=None, max_length=14)
    responsavel_telefone: Optional[str] = Field(default=None, max_length=20)
    responsavel_parentesco: Optional[str] = Field(default=None, max_length=50)

    convenio_id: Optional[UUID] = None
    convenio_numero: Optional[str] = Field(default=None, max_length=50)
    convenio_validade: Optional[date] = None

    medico_preferencial_id: Optional[UUID] = None

    observacoes: Optional[str] = None
    alergias: Optional[str] = None
    medicamentos_uso: Optional[str] = None
    
    ativo: Optional[bool] = None

    como_conheceu: Optional[str] = Field(default=None, max_length=100)
    indicado_por: Optional[UUID] = None
    foto_url: Optional[str] = None

    @field_validator("cpf", "responsavel_cpf")
    @classmethod
    def validate_cpf_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cpf = format_cpf(v)
        if not validate_cpf(cpf):
            raise ValueError("CPF inválido")
        return cpf

    @field_validator("telefone", "celular", "whatsapp", "responsavel_telefone")
    @classmethod
    def validate_telefone_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        telefone = format_telefone(v)
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")
        return telefone


# ==========================================
# RESPONSE
# ==========================================

class PacienteResponse(BaseSchema, TimestampMixin):
    """Schema de resposta completa do paciente."""

    id: UUID
    clinica_id: UUID

    # Dados básicos
    nome: str
    nome_social: Optional[str] = None
    telefone: str
    celular: Optional[str] = None
    whatsapp: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None
    email: Optional[str] = None
    idade: Optional[int] = None

    # Endereço
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None

    # Responsável/Contato de emergência
    responsavel_nome: Optional[str] = None
    responsavel_cpf: Optional[str] = None
    responsavel_telefone: Optional[str] = None
    responsavel_parentesco: Optional[str] = None

    # Convênio
    convenio_id: Optional[UUID] = None
    convenio_numero: Optional[str] = None
    convenio_validade: Optional[date] = None
    convenio_nome: Optional[str] = None  # Join com tabela convenios

    # Médico preferencial
    medico_preferencial_id: Optional[UUID] = None

    # Observações e saúde
    observacoes: Optional[str] = None
    alergias: Optional[str] = None
    medicamentos_uso: Optional[str] = None

    # Foto
    foto_url: Optional[str] = None

    # Marketing
    como_conheceu: Optional[str] = None
    indicado_por: Optional[UUID] = None

    # Status
    ativo: bool = True


class PacienteListItem(BaseSchema):
    """Schema resumido para listagem."""

    id: UUID
    nome: str
    telefone: str
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    convenio_nome: Optional[str] = None
    ativo: bool = True


# ==========================================
# BUSCA
# ==========================================

class PacienteBuscaResponse(BaseSchema):
    """Schema para busca de paciente (por CPF ou telefone)."""

    encontrado: bool
    paciente: Optional[PacienteResponse] = None


class PacienteResumo(BaseSchema):
    """Resumo mínimo do paciente (para autocomplete)."""

    id: UUID
    nome: str
    telefone: str
    cpf: Optional[str] = None
