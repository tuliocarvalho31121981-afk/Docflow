"""
Cards - Schemas
DTOs para cards do Kanban.

ESTRUTURA SIMPLIFICADA:
- 4 Fases = 4 Colunas do Kanban
- Checklist por fase
- Tipo: primeira_consulta ou retorno
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import BaseSchema


# ==========================================
# ENUMS
# ==========================================

class CardFase(int, Enum):
    """Fases do Kanban (são as colunas)."""
    PRE_AGENDAMENTO = 0
    PRE_CONSULTA = 1
    DIA_CONSULTA = 2
    POS_CONSULTA = 3


class CardStatus(str, Enum):
    """Status do card."""
    ATIVO = "ativo"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    PERDIDO = "perdido"
    NO_SHOW = "no_show"


class CardTipo(str, Enum):
    """Tipo do card."""
    PRIMEIRA_CONSULTA = "primeira_consulta"
    RETORNO = "retorno"


class CardPrioridade(str, Enum):
    """Prioridade do card."""
    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class IntencaoInicial(str, Enum):
    """Intenção inicial do contato (Fase 0)."""
    MARCAR = "marcar"
    SABER_VALOR = "saber_valor"
    SABER_CONVENIO = "saber_convenio"
    FAQ = "faq"


class MotivoSaida(str, Enum):
    """Motivo de saída/perda."""
    SEM_PLANO = "sem_plano"
    CARO = "caro"
    HORARIO = "horario"
    CANCELOU = "cancelou"
    DESISTIU = "desistiu"
    NO_SHOW = "no_show"
    OUTRO = "outro"


# ==========================================
# CHECKLIST
# ==========================================

class ChecklistItem(BaseSchema):
    """Item do checklist do card."""
    id: UUID
    card_id: UUID
    fase: int
    item_key: str
    descricao: str
    obrigatorio: bool = True
    concluido: bool = False
    concluido_em: Optional[datetime] = None
    concluido_por: Optional[str] = None
    ordem: int = 0


class ChecklistUpdate(BaseModel):
    """Atualização de item do checklist."""
    concluido: bool


class ChecklistResumo(BaseModel):
    """Resumo do checklist para exibição no card."""
    total: int = 0
    concluidos: int = 0
    obrigatorios_pendentes: int = 0
    
    @property
    def percentual(self) -> int:
        if self.total == 0:
            return 100
        return int((self.concluidos / self.total) * 100)
    
    @property
    def pode_avancar(self) -> bool:
        return self.obrigatorios_pendentes == 0


# ==========================================
# CARD - CREATE
# ==========================================

class CardCreate(BaseModel):
    """Criar card a partir de contato (Fase 0)."""
    paciente_id: Optional[UUID] = None
    paciente_nome: str
    paciente_telefone: str
    tipo_card: CardTipo = CardTipo.PRIMEIRA_CONSULTA
    origem: str = "whatsapp"
    intencao_inicial: Optional[IntencaoInicial] = None


class CardCreateRetorno(BaseModel):
    """Criar card de retorno (derivado de outro card)."""
    card_origem_id: UUID
    paciente_id: UUID
    prazo_dias: int = 30
    exames_solicitados: Optional[list[str]] = None


# ==========================================
# CARD - UPDATE
# ==========================================

class CardUpdate(BaseModel):
    """Atualizar dados do card."""
    prioridade: Optional[CardPrioridade] = None
    cor_alerta: Optional[str] = None
    observacoes: Optional[str] = None
    intencao_inicial: Optional[IntencaoInicial] = None
    motivo_saida: Optional[MotivoSaida] = None


class CardMoverFase(BaseModel):
    """Mover card para outra fase."""
    nova_fase: CardFase
    motivo: Optional[str] = None


class CardVincularAgendamento(BaseModel):
    """Vincular agendamento ao card (Fase 0 → 1)."""
    agendamento_id: UUID
    medico_id: UUID
    data_agendamento: date
    hora_agendamento: str


# ==========================================
# CARD - RESPONSE
# ==========================================

class CardResponse(BaseSchema):
    """Resposta completa do card."""
    id: UUID
    clinica_id: UUID
    
    # Paciente
    paciente_id: Optional[UUID] = None
    paciente_nome: Optional[str] = None
    paciente_telefone: Optional[str] = None
    
    # Tipo e Status
    tipo_card: str = "primeira_consulta"
    fase: int = 0
    status: str = "ativo"
    prioridade: str = "normal"
    cor_alerta: Optional[str] = None
    observacoes: Optional[str] = None
    
    # Agendamento (preenchido após agendar)
    agendamento_id: Optional[UUID] = None
    medico_id: Optional[UUID] = None
    data_agendamento: Optional[date] = None
    hora_agendamento: Optional[time] = None
    tipo_consulta: Optional[str] = None
    
    # Fase 0 - Pré-agendamento
    origem: Optional[str] = None
    intencao_inicial: Optional[str] = None
    motivo_saida: Optional[str] = None
    em_reativacao: bool = False
    tentativa_reativacao: int = 0
    ultima_interacao: Optional[datetime] = None
    
    # Convênio
    convenio_validado: bool = False
    convenio_status: Optional[str] = None
    
    # No-show
    no_show: bool = False
    no_show_em: Optional[datetime] = None
    
    # Card derivado (retorno)
    is_derivado: bool = False
    card_origem_id: Optional[UUID] = None
    card_derivado_id: Optional[UUID] = None
    
    # Timestamps
    fase0_em: Optional[datetime] = None
    fase1_em: Optional[datetime] = None
    fase2_em: Optional[datetime] = None
    fase3_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Checklist (resumo)
    checklist: Optional[ChecklistResumo] = None

    class Config:
        from_attributes = True


class CardListItem(BaseSchema):
    """Item do Kanban (card resumido)."""
    id: UUID
    
    # Paciente
    paciente_nome: Optional[str] = None
    paciente_telefone: Optional[str] = None
    
    # Status
    tipo_card: str = "primeira_consulta"
    fase: int = 0
    status: str = "ativo"
    prioridade: str = "normal"
    cor_alerta: Optional[str] = None
    
    # Agendamento
    data_agendamento: Optional[date] = None
    hora_agendamento: Optional[time] = None
    medico_id: Optional[UUID] = None
    
    # Fase 0
    intencao_inicial: Optional[str] = None
    em_reativacao: bool = False
    tentativa_reativacao: int = 0
    ultima_interacao: Optional[datetime] = None
    
    # Checklist
    checklist_total: int = 0
    checklist_concluidos: int = 0
    checklist_pode_avancar: bool = False

    class Config:
        from_attributes = True


class CardKanban(BaseSchema):
    """Estrutura do Kanban."""
    fase: int
    fase_nome: str
    cards: list[CardListItem]
    total: int
    
    # Métricas da fase
    em_reativacao: int = 0  # Só Fase 0
    aguardando_confirmacao: int = 0  # Só Fase 1


# ==========================================
# HISTÓRICO
# ==========================================

class CardHistoricoResponse(BaseSchema):
    """Evento do histórico do card."""
    id: UUID
    card_id: UUID
    tipo: str
    descricao: str
    dados_anteriores: Optional[dict] = None
    dados_novos: Optional[dict] = None
    user_id: Optional[UUID] = None
    user_nome: Optional[str] = None
    automatico: bool = False
    created_at: datetime


# ==========================================
# DOCUMENTOS
# ==========================================

class CardDocumentoCreate(BaseModel):
    """Upload de documento no card."""
    tipo: str = Field(..., pattern=r"^(exame|laudo|receita|atestado|guia|carteirinha|outro)$")
    nome: str = Field(..., max_length=255)
    descricao: Optional[str] = None
    storage_path: str
    mime_type: Optional[str] = None
    tamanho_bytes: Optional[int] = None


class CardDocumentoResponse(BaseSchema):
    """Documento do card."""
    id: UUID
    card_id: UUID
    tipo: str
    nome: str
    descricao: Optional[str] = None
    storage_path: str
    mime_type: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    created_at: datetime


# ==========================================
# MENSAGENS
# ==========================================

class CardMensagemResponse(BaseSchema):
    """Mensagem do card."""
    id: UUID
    card_id: UUID
    direcao: str  # entrada, saida
    canal: str  # whatsapp, email, sms
    conteudo: str
    status: str
    created_at: datetime


# ==========================================
# CONSTANTES
# ==========================================

FASES = {
    0: {"nome": "Pré-Agendamento", "icone": "📋"},
    1: {"nome": "Pré-Consulta", "icone": "📅"},
    2: {"nome": "Dia da Consulta", "icone": "🏥"},
    3: {"nome": "Pós-Consulta", "icone": "✅"},
}
