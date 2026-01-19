"""
Agenda - Schemas
DTOs para agendamentos, horários e slots.
"""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.schemas import BaseSchema, TimestampMixin


# ==========================================
# TIPOS DE CONSULTA
# ==========================================

class TipoConsultaResponse(BaseSchema):
    """Tipo de consulta disponível."""

    id: UUID
    nome: str
    descricao: Optional[str] = None
    cor: str = "#3B82F6"
    duracao_minutos: int = 30
    valor: Optional[float] = None
    requer_preparo: bool = False
    instrucoes_preparo: Optional[str] = None
    permite_retorno: bool = True
    dias_retorno: int = 30
    disponivel_online: bool = False
    ativo: bool = True


# ==========================================
# SLOTS DISPONÍVEIS
# ==========================================

class SlotDisponivel(BaseSchema):
    """Slot de horário disponível para agendamento."""

    data: date
    hora_inicio: time
    hora_fim: time
    medico_id: UUID
    medico_nome: str
    disponivel: bool = True


class SlotsDisponivelRequest(BaseSchema):
    """Request para buscar slots disponíveis."""

    medico_id: Optional[UUID] = Field(default=None, description="Filtrar por médico")
    data_inicio: date = Field(..., description="Data inicial")
    data_fim: Optional[date] = Field(default=None, description="Data final (default: data_inicio)")
    tipo_consulta_id: Optional[UUID] = Field(default=None, description="Filtrar por tipo")


# ==========================================
# AGENDAMENTOS
# ==========================================

class AgendamentoCreate(BaseSchema):
    """Schema para criar agendamento."""

    paciente_id: UUID = Field(..., description="ID do paciente")
    medico_id: UUID = Field(..., description="ID do médico")
    tipo_consulta_id: UUID = Field(..., description="Tipo de consulta")
    data: date = Field(..., description="Data do agendamento")
    hora_inicio: time = Field(..., description="Hora de início")
    
    # Opcionais
    observacoes: Optional[str] = Field(default=None, max_length=1000)
    retorno_de: Optional[UUID] = Field(default=None, description="ID do agendamento original (se for retorno)")
    
    # Convênio (se aplicável)
    convenio_id: Optional[UUID] = Field(default=None)
    numero_guia: Optional[str] = Field(default=None, max_length=50)
    valor: Optional[float] = Field(default=None)


class AgendamentoUpdate(BaseSchema):
    """Schema para atualizar agendamento."""

    medico_id: Optional[UUID] = None
    tipo_consulta_id: Optional[UUID] = None
    data: Optional[date] = None
    hora_inicio: Optional[time] = None
    observacoes: Optional[str] = Field(default=None, max_length=1000)
    convenio_id: Optional[UUID] = None
    numero_guia: Optional[str] = Field(default=None, max_length=50)
    valor: Optional[float] = None


class AgendamentoStatusUpdate(BaseSchema):
    """Schema para atualizar status do agendamento."""

    status: str = Field(
        ...,
        pattern="^(agendado|confirmado|aguardando|em_atendimento|atendido|faltou|cancelado|remarcado)$"
    )
    motivo_cancelamento: Optional[str] = Field(default=None, max_length=500)


class AgendamentoResponse(BaseSchema, TimestampMixin):
    """Schema de resposta do agendamento."""

    id: UUID
    clinica_id: UUID
    
    # Paciente
    paciente_id: UUID
    paciente_nome: Optional[str] = None
    paciente_telefone: Optional[str] = None
    
    # Médico
    medico_id: UUID
    medico_nome: Optional[str] = None
    
    # Tipo de consulta
    tipo_consulta_id: Optional[UUID] = None
    tipo_consulta_nome: Optional[str] = None
    tipo_consulta_cor: str = "#3B82F6"
    duracao_minutos: int = 30
    
    # Horário
    data: date
    hora_inicio: time
    hora_fim: Optional[time] = None
    
    # Status
    status: str = "agendado"
    
    # Flags
    primeira_vez: bool = False
    retorno_de: Optional[UUID] = None
    
    # Confirmação
    confirmado: bool = False
    confirmado_em: Optional[datetime] = None
    confirmado_via: Optional[str] = None
    
    # Check-in
    checkin_em: Optional[datetime] = None
    
    # Convênio
    convenio_id: Optional[UUID] = None
    convenio_nome: Optional[str] = None
    numero_guia: Optional[str] = None
    
    # Valor
    valor: Optional[float] = None
    
    # Observações
    observacoes: Optional[str] = None
    motivo_cancelamento: Optional[str] = None
    
    # Card vinculado
    card_id: Optional[UUID] = None


class AgendamentoListItem(BaseSchema):
    """Schema resumido para listagem de agenda."""

    id: UUID
    paciente_id: UUID
    paciente_nome: Optional[str] = None
    paciente_telefone: Optional[str] = None
    medico_id: UUID
    medico_nome: Optional[str] = None
    tipo_consulta_nome: Optional[str] = None
    tipo_consulta_cor: str = "#3B82F6"
    data: date
    hora_inicio: time
    hora_fim: Optional[time] = None
    duracao_minutos: int = 30
    status: str
    primeira_vez: bool = False
    retorno_de: Optional[UUID] = None
    convenio_nome: Optional[str] = None


# ==========================================
# AGENDA DO DIA
# ==========================================

class AgendaDiaResponse(BaseSchema):
    """Agenda completa de um dia."""

    data: date
    total_agendamentos: int
    total_confirmados: int
    total_aguardando: int
    total_atendidos: int
    total_faltas: int
    agendamentos: list[AgendamentoListItem]


# ==========================================
# MÉTRICAS
# ==========================================

class MetricasAgendaResponse(BaseSchema):
    """Métricas da agenda."""

    data: date
    total_agendados: int
    total_confirmados: int
    total_aguardando_confirmacao: int
    total_atendidos: int
    total_faltas: int
    total_cancelados: int
    taxa_confirmacao: float
    taxa_comparecimento: float
    horarios_disponiveis: int
    horarios_ocupados: int
    taxa_ocupacao: float
