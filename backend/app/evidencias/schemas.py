"""
Evidencias - Schemas
DTOs para evidências documentais.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import BaseSchema, TimestampMixin


# ==========================================
# ENUMS
# ==========================================

class EvidenciaCategoria(str, Enum):
    """Categorias de evidências."""
    DOCUMENTO = "documento"
    ASSINATURA = "assinatura"
    AUTORIZACAO = "autorizacao"
    CONSENTIMENTO = "consentimento"
    COMPROVANTE = "comprovante"
    LAUDO = "laudo"
    EXAME = "exame"
    RECEITA = "receita"
    ATESTADO = "atestado"


class EvidenciaTipo(str, Enum):
    """Tipos específicos de evidências."""
    # Documentos
    RG = "rg"
    CPF = "cpf"
    CNH = "cnh"
    COMPROVANTE_RESIDENCIA = "comprovante_residencia"
    CARTAO_CONVENIO = "cartao_convenio"
    
    # Assinaturas
    TERMO_CONSENTIMENTO = "termo_consentimento"
    TERMO_RESPONSABILIDADE = "termo_responsabilidade"
    AUTORIZACAO_PROCEDIMENTO = "autorizacao_procedimento"
    
    # Médicos
    PEDIDO_EXAME = "pedido_exame"
    RESULTADO_EXAME = "resultado_exame"
    LAUDO_MEDICO = "laudo_medico"
    RECEITA_MEDICA = "receita_medica"
    ATESTADO_MEDICO = "atestado_medico"
    
    # Financeiros
    COMPROVANTE_PAGAMENTO = "comprovante_pagamento"
    NOTA_FISCAL = "nota_fiscal"
    GUIA_CONVENIO = "guia_convenio"


# ==========================================
# CREATE
# ==========================================

class EvidenciaCreate(BaseModel):
    """Dados para criar evidência."""
    
    # Vínculo com entidade
    entidade: str = Field(..., description="Tipo da entidade (paciente, agendamento, card, etc)")
    entidade_id: UUID = Field(..., description="ID da entidade")
    
    # Tipo e categoria
    tipo: str = Field(..., max_length=50, description="Tipo da evidência")
    categoria: EvidenciaCategoria = Field(..., description="Categoria")
    
    # Arquivo
    storage_path: str = Field(..., description="Caminho no storage")
    nome_arquivo: str = Field(..., max_length=255, description="Nome original do arquivo")
    mime_type: Optional[str] = Field(default=None, max_length=100)
    tamanho_bytes: Optional[int] = Field(default=None)
    
    # Metadados
    descricao: Optional[str] = Field(default=None, max_length=500)
    data_documento: Optional[date] = Field(default=None, description="Data do documento")
    data_validade: Optional[date] = Field(default=None, description="Data de validade")
    
    # Assinatura digital
    assinatura_digital: bool = Field(default=False)
    assinatura_ip: Optional[str] = Field(default=None)
    assinatura_user_agent: Optional[str] = Field(default=None)


# ==========================================
# UPDATE
# ==========================================

class EvidenciaUpdate(BaseModel):
    """Dados para atualizar evidência."""
    
    descricao: Optional[str] = Field(default=None, max_length=500)
    data_documento: Optional[date] = None
    data_validade: Optional[date] = None


# ==========================================
# RESPONSE
# ==========================================

class EvidenciaResponse(BaseSchema, TimestampMixin):
    """Resposta completa da evidência."""
    
    id: UUID
    clinica_id: UUID
    
    # Vínculo
    entidade: str
    entidade_id: UUID
    
    # Tipo
    tipo: str
    categoria: str
    
    # Arquivo
    storage_path: str
    nome_arquivo: str
    mime_type: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    
    # Metadados
    descricao: Optional[str] = None
    data_documento: Optional[date] = None
    data_validade: Optional[date] = None
    
    # Integridade
    hash_arquivo: Optional[str] = None
    verificado: bool = False
    verificado_em: Optional[datetime] = None
    verificado_por: Optional[UUID] = None
    
    # Assinatura digital
    assinatura_digital: bool = False
    assinatura_ip: Optional[str] = None
    assinatura_em: Optional[datetime] = None
    
    # Upload
    uploaded_by_user: Optional[UUID] = None
    uploaded_by_paciente: bool = False
    
    # Status
    ativo: bool = True
    invalidado_em: Optional[datetime] = None
    invalidado_por: Optional[UUID] = None
    motivo_invalidacao: Optional[str] = None


class EvidenciaListItem(BaseSchema):
    """Item da lista de evidências."""
    
    id: UUID
    entidade: str
    entidade_id: UUID
    tipo: str
    categoria: str
    nome_arquivo: str
    data_documento: Optional[date] = None
    data_validade: Optional[date] = None
    verificado: bool = False
    assinatura_digital: bool = False
    ativo: bool = True
    created_at: datetime


# ==========================================
# RESUMO E VERIFICAÇÃO
# ==========================================

class EvidenciasResumo(BaseSchema):
    """Resumo das evidências de uma entidade."""
    
    entidade: str
    entidade_id: UUID
    total: int
    por_categoria: dict[str, int]
    por_tipo: dict[str, int]
    pendentes: list[str]  # Tipos de evidências pendentes
    vencidas: list[str]   # Tipos de evidências vencidas


class VerificacaoEvidencias(BaseSchema):
    """Resultado da verificação de evidências."""
    
    pode_executar: bool
    evidencias_faltando: list[str]
    mensagem: str
