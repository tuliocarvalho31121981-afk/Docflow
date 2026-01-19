# app/chat_langgraph/states.py
"""
Estados da Conversa - Simples e direto.

O estado guarda:
- Identificadores (clínica, telefone, conversa)
- Dados do cliente (se existe)
- Dados da consulta (se tem)
- Rascunho do cadastro (formulário em memória)
- Mensagens
- Resposta
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from datetime import datetime
import operator


# ============================================================================
# TIPOS
# ============================================================================

class DadosCliente(TypedDict, total=False):
    """Dados do cliente."""
    id: str
    nome: str
    nome_curto: str
    cpf: str
    data_nascimento: str
    convenio: str
    carteirinha: str
    cadastro_completo: bool


class DadosConsulta(TypedDict, total=False):
    """Dados da consulta agendada."""
    id: str
    data: str
    hora: str
    data_formatada: str
    medico: str
    tipo: str
    confirmada: bool


class RascunhoCadastro(TypedDict, total=False):
    """Rascunho do cadastro (formulário em memória)."""
    nome: str
    cpf: str
    data_nascimento: str
    convenio: str
    carteirinha: str


# ============================================================================
# ESTADO PRINCIPAL
# ============================================================================

class ConversaState(TypedDict, total=False):
    """Estado da conversa."""
    
    # Identificadores
    clinica_id: str
    telefone: str
    conversa_id: str
    
    # Cliente
    cliente_id: Optional[str]
    cliente_existe: bool
    dados_cliente: DadosCliente
    
    # Consulta
    consulta_agendada: Optional[DadosConsulta]
    agendamento_id: Optional[str]
    
    # Card
    card_id: Optional[str]
    
    # Rascunho do cadastro (formulário em memória)
    rascunho_cadastro: RascunhoCadastro
    
    # Mensagens
    mensagem_atual: str
    mensagens: Annotated[List[Dict], operator.add]
    historico_mensagens: List[Dict]
    
    # Resposta
    resposta: str
    acoes_executadas: List[Dict]
    
    # Controle
    erro: Optional[str]
    updated_at: str


# ============================================================================
# FACTORY
# ============================================================================

def criar_estado_inicial(clinica_id: str, telefone: str, conversa_id: str = None) -> ConversaState:
    """Cria estado inicial para nova conversa."""
    
    return ConversaState(
        # Identificadores
        clinica_id=clinica_id,
        telefone=telefone,
        conversa_id=conversa_id or "",
        
        # Cliente
        cliente_id=None,
        cliente_existe=False,
        dados_cliente={},
        
        # Consulta
        consulta_agendada=None,
        agendamento_id=None,
        
        # Card
        card_id=None,
        
        # Rascunho
        rascunho_cadastro={},
        
        # Mensagens
        mensagem_atual="",
        mensagens=[],
        historico_mensagens=[],
        
        # Resposta
        resposta="",
        acoes_executadas=[],
        
        # Controle
        erro=None,
        updated_at=datetime.now().isoformat()
    )
