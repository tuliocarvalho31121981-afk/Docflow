# app/chat_langgraph/schemas.py
"""
Schemas para API - Compatível com frontend existente.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class IntencaoEnum(str, Enum):
    """Intenções possíveis do paciente."""
    AGENDAR = "AGENDAR"
    REMARCAR = "REMARCAR"
    CANCELAR = "CANCELAR"
    CONFIRMAR = "CONFIRMAR"
    VALOR = "VALOR"
    CONVENIO = "CONVENIO"
    FAQ = "FAQ"
    INFORMACAO = "INFORMACAO"
    EXAMES = "EXAMES"
    ANAMNESE = "ANAMNESE"
    CHECK_IN = "CHECK_IN"
    SAUDACAO = "SAUDACAO"
    DESPEDIDA = "DESPEDIDA"
    DESCONHECIDO = "DESCONHECIDO"


class TipoMensagem(str, Enum):
    """Tipos de mensagem."""
    TEXTO = "texto"
    AUDIO = "audio"
    IMAGEM = "imagem"
    DOCUMENTO = "documento"
    VIDEO = "video"


# ============================================================================
# REQUEST
# ============================================================================

class MensagemRequest(BaseModel):
    """Request para envio de mensagem."""
    telefone: str = Field(..., description="Telefone do paciente")
    mensagem: str = Field(..., description="Conteúdo da mensagem")
    tipo: TipoMensagem = Field(default=TipoMensagem.TEXTO)
    midia_url: Optional[str] = None
    simulado: bool = Field(default=False)
    nome_paciente: Optional[str] = None


class WebhookWhatsAppRequest(BaseModel):
    """Request do webhook Evolution API."""
    event: str
    instance: str
    data: Dict[str, Any]


# ============================================================================
# SCHEMAS INTERNOS
# ============================================================================

class DadosExtraidos(BaseModel):
    """Dados extraídos da mensagem."""
    data: Optional[str] = None
    hora: Optional[str] = None
    nome: Optional[str] = None
    medico: Optional[str] = None
    motivo: Optional[str] = None
    cpf: Optional[str] = None
    convenio: Optional[str] = None


class InterpretacaoLLM(BaseModel):
    """Resultado da interpretação do LLM - FORMATO DO FRONTEND."""
    intencao: str = Field(default="DESCONHECIDO")
    confianca: int = Field(default=0, ge=0, le=100)
    dados: DadosExtraidos = Field(default_factory=DadosExtraidos)
    requer_mais_info: bool = Field(default=False)
    pergunta_followup: Optional[str] = None


class AcaoExecutada(BaseModel):
    """Ação executada pelo sistema."""
    tipo: str
    sucesso: bool = True
    detalhes: Dict[str, Any] = Field(default_factory=dict)
    erro: Optional[str] = None


# ============================================================================
# RESPONSE
# ============================================================================

class MensagemResponse(BaseModel):
    """Response de mensagem - compatível com frontend."""
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    resposta: str = Field(..., description="Resposta para o paciente")
    
    # Interpretação (formato frontend)
    interpretacao: InterpretacaoLLM = Field(default_factory=InterpretacaoLLM)
    
    # Ações
    acoes: List[AcaoExecutada] = Field(default_factory=list)
    
    # Governança
    validacao_pendente: bool = Field(default=False)
    validacao_id: Optional[str] = None
    
    # Métricas
    tempo_processamento_ms: int = Field(default=0)
    
    # Campos extras
    estado: Optional[str] = None
    conversa_id: Optional[str] = None
    paciente_id: Optional[str] = None
    cliente_id: Optional[str] = None  # Alias
    card_id: Optional[str] = None
    agendamento_id: Optional[str] = None
    consulta_agendada: Optional[Dict[str, Any]] = None
    sucesso: bool = Field(default=True)
    erro: Optional[str] = None


class MensagemHistorico(BaseModel):
    """Mensagem no histórico."""
    id: str
    tipo: str
    conteudo: str
    timestamp: str
    interpretacao: Optional[Dict[str, Any]] = None


class ConversaResponse(BaseModel):
    """Response de conversa."""
    telefone: str
    paciente_id: Optional[str] = None
    paciente_nome: Optional[str] = None
    estado_atual: str = ""
    total_mensagens: int = 0
    ultima_mensagem: Optional[str] = None
    mensagens: List[MensagemHistorico] = Field(default_factory=list)


class ConversasListResponse(BaseModel):
    """Lista de conversas."""
    conversas: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class LLMConfigResponse(BaseModel):
    """Config do LLM para frontend."""
    provider: str = "groq"
    model: Optional[str] = None
    status: str = "ok"
    erro: Optional[str] = None


# ============================================================================
# FUNÇÕES DE CONVERSÃO
# ============================================================================

def converter_estado_para_response(state: dict) -> dict:
    """
    Converte o estado do LangGraph para o formato esperado pelo frontend.
    """
    # Extrai dados do estado
    intencao = state.get("intencao") or "DESCONHECIDO"
    confianca = state.get("confianca_intencao") or 0
    
    # Converte confiança de 0-1 para 0-100 se necessário
    if isinstance(confianca, float) and confianca <= 1:
        confianca = int(confianca * 100)
    else:
        confianca = int(confianca)
    
    # Extrai dados do paciente/cliente
    dados_paciente = state.get("dados_paciente", {}) or state.get("dados_cliente", {}) or {}
    dados_agendamento = state.get("dados_agendamento", {}) or state.get("consulta_agendada", {}) or {}
    
    # Monta dados extraídos
    dados_extraidos = {
        "data": dados_agendamento.get("data"),
        "hora": dados_agendamento.get("hora"),
        "nome": dados_paciente.get("nome") if isinstance(dados_paciente, dict) else None,
        "medico": dados_agendamento.get("medico_nome") if isinstance(dados_agendamento, dict) else None,
        "motivo": dados_agendamento.get("tipo_consulta") if isinstance(dados_agendamento, dict) else None,
    }
    
    # Determina se precisa de mais info
    estados_coleta = ["coletando_nome", "coletando_cpf", "coletando_nascimento", 
                      "coletando_convenio", "coletando_data", "coletando_horario"]
    requer_mais_info = state.get("estado", "") in estados_coleta
    
    # Monta ações executadas
    acoes_raw = state.get("acoes_executadas", [])
    acoes = []
    for acao in acoes_raw:
        if isinstance(acao, str):
            acoes.append({
                "tipo": acao,
                "sucesso": True,
                "detalhes": {},
                "erro": None
            })
        elif isinstance(acao, dict):
            acoes.append({
                "tipo": acao.get("tipo", acao.get("ferramenta", "desconhecido")),
                "sucesso": acao.get("sucesso", True),
                "detalhes": acao.get("detalhes", acao.get("resultado", {})),
                "erro": acao.get("erro")
            })
    
    return {
        "id": state.get("conversa_id", str(datetime.now().timestamp())),
        "resposta": state.get("resposta", ""),
        "interpretacao": {
            "intencao": intencao,
            "confianca": confianca,
            "dados": dados_extraidos,
            "requer_mais_info": requer_mais_info,
            "pergunta_followup": state.get("resposta") if requer_mais_info else None
        },
        "acoes": acoes,
        "validacao_pendente": state.get("validacao_pendente", False),
        "validacao_id": state.get("validacao_id"),
        "tempo_processamento_ms": state.get("tempo_processamento_ms", 0),
        "estado": state.get("estado"),
        "conversa_id": state.get("conversa_id"),
        "paciente_id": state.get("paciente_id") or state.get("cliente_id"),
        "cliente_id": state.get("cliente_id") or state.get("paciente_id"),
        "card_id": state.get("card_id"),
        "agendamento_id": state.get("agendamento_id"),
        "consulta_agendada": state.get("consulta_agendada"),
        "sucesso": state.get("erro") is None,
        "erro": state.get("erro")
    }


def converter_resultado_para_response(resultado: dict) -> MensagemResponse:
    """
    Converte resultado do grafo para response da API.
    Alias para converter_estado_para_response com tipagem.
    """
    dados = converter_estado_para_response(resultado)
    
    return MensagemResponse(
        id=dados.get("id", ""),
        resposta=dados.get("resposta", ""),
        interpretacao=InterpretacaoLLM(**dados.get("interpretacao", {})),
        acoes=[AcaoExecutada(**a) for a in dados.get("acoes", [])],
        validacao_pendente=dados.get("validacao_pendente", False),
        validacao_id=dados.get("validacao_id"),
        tempo_processamento_ms=dados.get("tempo_processamento_ms", 0),
        estado=dados.get("estado"),
        conversa_id=dados.get("conversa_id"),
        paciente_id=dados.get("paciente_id"),
        cliente_id=dados.get("cliente_id"),
        card_id=dados.get("card_id"),
        agendamento_id=dados.get("agendamento_id"),
        consulta_agendada=dados.get("consulta_agendada"),
        sucesso=dados.get("sucesso", True),
        erro=dados.get("erro")
    )
