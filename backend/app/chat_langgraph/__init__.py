# app/chat_langgraph/__init__.py
"""
Chat LangGraph - Módulo de Chat com Agente Inteligente

Arquitetura de AGENTE com Function Calling:
- LLM decide quando chamar cada ferramenta
- Ferramentas simples: verificar_cliente, cadastrar_cliente, agendar_consulta, etc.
- Fluxo: carregar_contexto → agente → finalizar

Uso:
    from app.chat_langgraph import ChatService, router
    from app.chat_langgraph.schemas import MensagemRequest, MensagemResponse

Endpoints:
    POST /chat/mensagem - Processa mensagem do paciente
    POST /chat/webhook/whatsapp - Webhook Evolution API
    GET  /chat/conversas - Lista conversas
    GET  /chat/conversas/{telefone} - Busca conversa
    GET  /chat/grafo - Diagrama Mermaid do grafo
    GET  /chat/status - Health check
"""

__version__ = "2.0.0"
__author__ = "ClinicOS"

# Exports principais
from .service import ChatService, criar_chat_service
from .router import router
from .schemas import (
    MensagemRequest,
    MensagemResponse,
    ConversaResponse,
    ConversasListResponse,
    IntencaoEnum,
    TipoMensagem,
    WebhookWhatsAppRequest,
    InterpretacaoLLM,
    AcaoExecutada,
    DadosExtraidos,
    MensagemHistorico,
    LLMConfigResponse,
    converter_estado_para_response,
    converter_resultado_para_response,
)
from .states import ConversaState, criar_estado_inicial
from .graph import ChatGraph, criar_chat_graph
from .agent import AgenteClinica, criar_agente
from .tools import executar_ferramenta, TOOLS_SCHEMA

# Aliases para compatibilidade com código anterior
ClinicaAgent = AgenteClinica
executar_tool = executar_ferramenta

__all__ = [
    # Service
    "ChatService",
    "criar_chat_service",
    # Router
    "router",
    # Schemas
    "MensagemRequest",
    "MensagemResponse",
    "ConversaResponse",
    "ConversasListResponse",
    "IntencaoEnum",
    "TipoMensagem",
    "WebhookWhatsAppRequest",
    "InterpretacaoLLM",
    "AcaoExecutada",
    "DadosExtraidos",
    "MensagemHistorico",
    "LLMConfigResponse",
    "converter_estado_para_response",
    "converter_resultado_para_response",
    # States
    "ConversaState",
    "criar_estado_inicial",
    # Graph
    "ChatGraph",
    "criar_chat_graph",
    # Agent
    "AgenteClinica",
    "ClinicaAgent",  # Alias
    "criar_agente",
    # Tools
    "executar_ferramenta",
    "executar_tool",  # Alias
    "TOOLS_SCHEMA",
]
