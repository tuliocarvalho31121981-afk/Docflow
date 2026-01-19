"""
Prontuário - Schemas
DTOs para consultas, SOAP, receitas, atestados, exames e encaminhamentos.
"""

from datetime import date, datetime, time
from typing import Optional, List, Any
from uuid import UUID

from pydantic import Field

from app.core.schemas import BaseSchema, TimestampMixin


# ============================================================================
# TIPOS AUXILIARES
# ============================================================================

class SinaisVitais(BaseSchema):
    """Sinais vitais do paciente."""
    pa_sistolica: Optional[int] = Field(default=None, description="Pressão sistólica (mmHg)")
    pa_diastolica: Optional[int] = Field(default=None, description="Pressão diastólica (mmHg)")
    fc: Optional[int] = Field(default=None, description="Frequência cardíaca (bpm)")
    fr: Optional[int] = Field(default=None, description="Frequência respiratória (irpm)")
    temperatura: Optional[float] = Field(default=None, description="Temperatura (°C)")
    saturacao: Optional[int] = Field(default=None, description="Saturação O2 (%)")
    peso: Optional[float] = Field(default=None, description="Peso (kg)")
    altura: Optional[float] = Field(default=None, description="Altura (cm)")
    imc: Optional[float] = Field(default=None, description="IMC calculado")
    glicemia: Optional[int] = Field(default=None, description="Glicemia capilar (mg/dL)")


class CID(BaseSchema):
    """Código CID."""
    codigo: str = Field(..., description="Código CID-10")
    descricao: str = Field(..., description="Descrição do diagnóstico")
    tipo: str = Field(default="principal", description="principal ou secundario")


class SOAPData(BaseSchema):
    """Estrutura SOAP do prontuário."""
    subjetivo: Optional[str] = Field(default=None, description="Queixa do paciente")
    objetivo: Optional[str] = Field(default=None, description="Exame físico")
    avaliacao: Optional[str] = Field(default=None, description="Hipótese diagnóstica")
    plano: Optional[str] = Field(default=None, description="Conduta")


class ItemReceita(BaseSchema):
    """Item de uma receita médica."""
    medicamento: str = Field(..., description="Nome do medicamento")
    concentracao: Optional[str] = Field(default=None, description="Ex: 50mg")
    forma: Optional[str] = Field(default=None, description="comprimido, cápsula, etc")
    quantidade: Optional[int] = Field(default=None, description="Quantidade de unidades")
    posologia: str = Field(..., description="Ex: 1 comprimido pela manhã")
    duracao: Optional[str] = Field(default=None, description="Ex: 30 dias, uso contínuo")
    observacao: Optional[str] = Field(default=None)


# ============================================================================
# CONSULTAS
# ============================================================================

class ConsultaCreate(BaseSchema):
    """Criar nova consulta."""
    agendamento_id: Optional[UUID] = Field(default=None, description="ID do agendamento")
    paciente_id: UUID = Field(..., description="ID do paciente")
    medico_id: UUID = Field(..., description="ID do médico")
    data: date = Field(..., description="Data da consulta")
    hora_inicio: Optional[time] = Field(default=None, description="Hora de início")


class ConsultaUpdate(BaseSchema):
    """Atualizar consulta."""
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    queixa_principal: Optional[str] = None
    historia_doenca_atual: Optional[str] = None
    antecedentes_pessoais: Optional[str] = None
    antecedentes_familiares: Optional[str] = None
    habitos_vida: Optional[str] = None
    exame_fisico: Optional[str] = None
    sinais_vitais: Optional[SinaisVitais] = None
    hipotese_diagnostica: Optional[str] = None
    cid: Optional[str] = None
    conduta: Optional[str] = None
    soap: Optional[SOAPData] = None
    audio_url: Optional[str] = None
    transcricao: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(em_andamento|finalizada|cancelada)$")


class ConsultaIniciar(BaseSchema):
    """Iniciar consulta (médico chamou paciente)."""
    agendamento_id: UUID = Field(..., description="ID do agendamento")


class ConsultaFinalizar(BaseSchema):
    """Finalizar consulta."""
    resumo: Optional[str] = Field(default=None, description="Resumo da consulta")


class ConsultaResponse(BaseSchema, TimestampMixin):
    """Resposta de consulta."""
    id: UUID
    clinica_id: UUID
    agendamento_id: Optional[UUID] = None
    paciente_id: UUID
    medico_id: UUID

    data: date
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None

    queixa_principal: Optional[str] = None
    historia_doenca_atual: Optional[str] = None
    antecedentes_pessoais: Optional[str] = None
    antecedentes_familiares: Optional[str] = None
    habitos_vida: Optional[str] = None
    exame_fisico: Optional[str] = None
    sinais_vitais: Optional[dict] = None
    hipotese_diagnostica: Optional[str] = None
    cid: Optional[str] = None
    conduta: Optional[str] = None
    soap: Optional[dict] = None

    audio_url: Optional[str] = None
    transcricao: Optional[str] = None
    transcricao_processada: bool = False

    status: str = "em_andamento"
    assinada_em: Optional[datetime] = None

    # Dados expandidos (joins)
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


class ConsultaListItem(BaseSchema):
    """Item de listagem de consultas."""
    id: UUID
    paciente_id: UUID
    medico_id: UUID
    data: date
    hora_inicio: Optional[time] = None
    status: str
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


# ============================================================================
# TRANSCRIÇÕES
# ============================================================================

class TranscricaoCreate(BaseSchema):
    """Criar transcrição."""
    consulta_id: UUID
    audio_storage_path: Optional[str] = None
    audio_duracao_segundos: Optional[int] = None


class TranscricaoUpdate(BaseSchema):
    """Atualizar transcrição."""
    transcricao_bruta: Optional[str] = None
    transcricao_revisada: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(processando|concluida|erro)$")
    erro_mensagem: Optional[str] = None


class TranscricaoResponse(BaseSchema):
    """Resposta de transcrição."""
    id: UUID
    consulta_id: UUID

    audio_storage_path: Optional[str] = None
    audio_duracao_segundos: Optional[int] = None

    transcricao_bruta: Optional[str] = None
    transcricao_revisada: Optional[str] = None

    status: str = "processando"
    erro_mensagem: Optional[str] = None
    modelo_whisper: Optional[str] = None
    idioma: str = "pt"

    iniciada_em: Optional[datetime] = None
    concluida_em: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ============================================================================
# PRONTUÁRIO SOAP
# ============================================================================

class ProntuarioSOAPCreate(BaseSchema):
    """Criar prontuário SOAP."""
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    avaliacao: Optional[str] = None
    plano: Optional[str] = None

    exame_fisico: Optional[dict] = Field(default_factory=dict)
    cids: Optional[List[CID]] = Field(default_factory=list)

    gerado_por_ia: bool = False


class ProntuarioSOAPUpdate(BaseSchema):
    """Atualizar prontuário SOAP."""
    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    avaliacao: Optional[str] = None
    plano: Optional[str] = None
    exame_fisico: Optional[dict] = None
    cids: Optional[List[dict]] = None
    revisado_por_medico: Optional[bool] = None


class ProntuarioSOAPResponse(BaseSchema, TimestampMixin):
    """Resposta de prontuário SOAP."""
    id: UUID
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    avaliacao: Optional[str] = None
    plano: Optional[str] = None

    exame_fisico: dict = Field(default_factory=dict)
    cids: List[dict] = Field(default_factory=list)

    gerado_por_ia: bool = False
    revisado_por_medico: bool = False
    revisado_em: Optional[datetime] = None

    assinado: bool = False
    assinatura_certificado: Optional[str] = None
    assinado_em: Optional[datetime] = None


# ============================================================================
# RECEITAS
# ============================================================================

class ReceitaCreate(BaseSchema):
    """Criar receita."""
    consulta_id: Optional[UUID] = None
    paciente_id: UUID
    medico_id: UUID

    tipo: str = Field(default="simples", pattern="^(simples|especial|antimicrobiano)$")
    itens: List[ItemReceita] = Field(..., min_length=1)
    observacoes: Optional[str] = None


class ReceitaUpdate(BaseSchema):
    """Atualizar receita."""
    tipo: Optional[str] = Field(default=None, pattern="^(simples|especial|antimicrobiano)$")
    itens: Optional[List[ItemReceita]] = None
    observacoes: Optional[str] = None
    validade: Optional[date] = None
    status: Optional[str] = Field(default=None, pattern="^(rascunho|emitida|cancelada)$")


class ReceitaResponse(BaseSchema, TimestampMixin):
    """Resposta de receita."""
    id: UUID
    clinica_id: UUID
    consulta_id: Optional[UUID] = None
    paciente_id: UUID
    medico_id: UUID

    tipo: str = "simples"
    data_emissao: Optional[date] = None
    validade: Optional[date] = None

    itens: List[dict] = Field(default_factory=list)
    observacoes: Optional[str] = None

    pdf_url: Optional[str] = None
    assinatura_digital: bool = False
    status: str = "emitida"

    # Dados expandidos
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


# ============================================================================
# ATESTADOS
# ============================================================================

class AtestadoCreate(BaseSchema):
    """Criar atestado."""
    consulta_id: Optional[UUID] = None
    paciente_id: UUID
    medico_id: UUID

    tipo: str = Field(..., pattern="^(comparecimento|afastamento|aptidao|acompanhante|medico)$")
    texto: str = Field(..., description="Texto do atestado")

    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    dias_afastamento: Optional[int] = None
    cid: Optional[str] = Field(default=None, description="CID (se autorizado)")


class AtestadoUpdate(BaseSchema):
    """Atualizar atestado."""
    tipo: Optional[str] = Field(default=None, pattern="^(comparecimento|afastamento|aptidao|acompanhante|medico)$")
    texto: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    dias_afastamento: Optional[int] = None
    cid: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(rascunho|emitido|cancelado)$")


class AtestadoResponse(BaseSchema, TimestampMixin):
    """Resposta de atestado."""
    id: UUID
    clinica_id: UUID
    consulta_id: Optional[UUID] = None
    paciente_id: UUID
    medico_id: UUID

    tipo: str
    data_emissao: Optional[date] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    dias_afastamento: Optional[int] = None
    cid: Optional[str] = None
    texto: Optional[str] = None

    pdf_url: Optional[str] = None
    assinatura_digital: bool = False
    status: str = "emitido"

    # Dados expandidos
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


# ============================================================================
# EXAMES SOLICITADOS
# ============================================================================

class ExameSolicitadoCreate(BaseSchema):
    """Criar solicitação de exame."""
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    nome: str = Field(..., description="Nome do exame")
    codigo_tuss: Optional[str] = Field(default=None, description="Código TUSS")
    tipo: Optional[str] = Field(default=None, description="laboratorial, imagem, cardiologico")
    indicacao_clinica: Optional[str] = None
    cid_codigo: Optional[str] = None

    urgente: bool = False
    para_retorno: bool = False
    prazo_dias: Optional[int] = None


class ExameSolicitadoUpdate(BaseSchema):
    """Atualizar exame solicitado."""
    status: Optional[str] = Field(
        default=None,
        pattern="^(solicitado|guia_emitida|agendado|realizado|resultado_anexado|cancelado)$"
    )
    documento_id: Optional[UUID] = None
    resultado_em: Optional[datetime] = None
    guia_storage_path: Optional[str] = None
    guia_numero: Optional[str] = None


class ExameSolicitadoResponse(BaseSchema, TimestampMixin):
    """Resposta de exame solicitado."""
    id: UUID
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    nome: str
    codigo_tuss: Optional[str] = None
    tipo: Optional[str] = None
    indicacao_clinica: Optional[str] = None
    cid_codigo: Optional[str] = None

    urgente: bool = False
    para_retorno: bool = False
    prazo_dias: Optional[int] = None

    status: str = "solicitado"
    documento_id: Optional[UUID] = None
    resultado_em: Optional[datetime] = None
    guia_storage_path: Optional[str] = None
    guia_numero: Optional[str] = None

    # Dados expandidos
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


class ExameSolicitadoBatch(BaseSchema):
    """Criar múltiplos exames de uma vez."""
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID
    exames: List[str] = Field(..., description="Lista de nomes de exames")
    para_retorno: bool = False


# ============================================================================
# ENCAMINHAMENTOS
# ============================================================================

class EncaminhamentoCreate(BaseSchema):
    """Criar encaminhamento."""
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    especialidade: str = Field(..., description="Especialidade destino")
    profissional_nome: Optional[str] = Field(default=None, description="Nome do profissional")
    motivo: str = Field(..., description="Motivo do encaminhamento")
    cid_codigo: Optional[str] = None
    urgente: bool = False


class EncaminhamentoUpdate(BaseSchema):
    """Atualizar encaminhamento."""
    especialidade: Optional[str] = None
    profissional_nome: Optional[str] = None
    motivo: Optional[str] = None
    cid_codigo: Optional[str] = None
    urgente: Optional[bool] = None
    status: Optional[str] = Field(default=None, pattern="^(rascunho|emitido|cancelado)$")
    enviado_paciente: Optional[bool] = None


class EncaminhamentoResponse(BaseSchema):
    """Resposta de encaminhamento."""
    id: UUID
    consulta_id: UUID
    paciente_id: UUID
    medico_id: UUID

    especialidade: str
    profissional_nome: Optional[str] = None
    motivo: str
    cid_codigo: Optional[str] = None
    urgente: bool = False

    pdf_storage_path: Optional[str] = None
    status: str = "emitido"
    enviado_paciente: bool = False
    enviado_em: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # Dados expandidos
    paciente_nome: Optional[str] = None
    medico_nome: Optional[str] = None


# ============================================================================
# BRIEFING PRÉ-CONSULTA
# ============================================================================

class BriefingPaciente(BaseSchema):
    """Briefing do paciente para o médico antes da consulta."""
    paciente_id: UUID
    nome: str
    idade: Optional[int] = None
    sexo: Optional[str] = None

    # Dados clínicos
    alergias: List[str] = Field(default_factory=list)
    medicamentos_uso: List[str] = Field(default_factory=list)
    antecedentes: Optional[str] = None

    # Última consulta
    ultima_consulta: Optional[dict] = None

    # Exames pendentes
    exames_pendentes: List[dict] = Field(default_factory=list)

    # Alertas
    alertas: List[str] = Field(default_factory=list)


# ============================================================================
# HISTÓRICO
# ============================================================================

class HistoricoConsulta(BaseSchema):
    """Item do histórico de consultas."""
    consulta_id: UUID
    data: date
    medico_nome: Optional[str] = None
    resumo: Optional[str] = None
    cids: List[dict] = Field(default_factory=list)
    teve_receita: bool = False
    teve_exames: bool = False
