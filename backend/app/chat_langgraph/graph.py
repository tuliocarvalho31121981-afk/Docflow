# app/chat_langgraph/graph.py
"""
Grafo LangGraph - Simples.

Fluxo:
    carregar_contexto → agente → finalizar

O agente faz todo o trabalho. O grafo só organiza.
"""

from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_DISPONIVEL = True
except ImportError:
    try:
        from langgraph.checkpoint.postgres import AsyncPostgresSaver
        POSTGRES_DISPONIVEL = True
    except ImportError:
        POSTGRES_DISPONIVEL = False

from .states import ConversaState, criar_estado_inicial
from .agent import criar_agente


# ============================================================================
# NÓS DO GRAFO
# ============================================================================

async def carregar_contexto(state: ConversaState, db) -> ConversaState:
    """
    Carrega contexto (histórico de mensagens).
    """
    telefone = state.get("telefone", "")
    print(f"[NODE] carregar_contexto: {telefone[:4]}***")
    
    novo = dict(state)
    
    # Carrega histórico
    try:
        conversa_id = state.get("conversa_id")
        if conversa_id:
            mensagens = await db.select(
                table="mensagens",
                filters={"conversa_id": conversa_id},
                order_by="created_at",
                order_asc=False,
                limit=20
            )
            novo["historico_mensagens"] = list(reversed(mensagens)) if mensagens else []
    except Exception as e:
        print(f"[WARN] Erro ao carregar histórico: {e}")
        novo["historico_mensagens"] = []
    
    return novo


async def executar_agente(state: ConversaState, llm_client, db) -> ConversaState:
    """
    Executa o agente.
    """
    print(f"[NODE] executar_agente: '{state.get('mensagem_atual', '')[:50]}...'")
    
    agente = criar_agente(llm_client, db)
    
    try:
        resultado = await agente.processar(state)
        return resultado
    except Exception as e:
        print(f"[ERROR] Agente falhou: {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "resposta": "Desculpe, ocorreu um erro. Pode repetir?",
            "erro": str(e)
        }


async def finalizar(state: ConversaState, db) -> ConversaState:
    """
    Finaliza o processamento.
    """
    print(f"[NODE] finalizar")
    
    return {
        **state,
        "updated_at": datetime.now().isoformat()
    }


# ============================================================================
# CLASSE DO GRAFO
# ============================================================================

class ChatGraph:
    """
    Grafo de conversa.
    
    Fluxo: carregar_contexto → agente → finalizar
    """
    
    def __init__(self, db, llm_client, checkpointer=None):
        self.db = db
        self.llm_client = llm_client
        self.checkpointer = checkpointer
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Constrói o grafo."""
        
        workflow = StateGraph(ConversaState)
        
        # Nós
        workflow.add_node("carregar_contexto", self._wrap_db(carregar_contexto))
        workflow.add_node("agente", self._wrap_db_llm(executar_agente))
        workflow.add_node("finalizar", self._wrap_db(finalizar))
        
        # Fluxo
        workflow.set_entry_point("carregar_contexto")
        workflow.add_edge("carregar_contexto", "agente")
        workflow.add_edge("agente", "finalizar")
        workflow.add_edge("finalizar", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _wrap_db(self, func):
        """Wrapper que injeta db."""
        async def wrapper(state: ConversaState):
            return await func(state, self.db)
        return wrapper
    
    def _wrap_db_llm(self, func):
        """Wrapper que injeta db e llm_client."""
        async def wrapper(state: ConversaState):
            return await func(state, self.llm_client, self.db)
        return wrapper
    
    # ========================================================================
    # MÉTODO PRINCIPAL
    # ========================================================================
    
    async def processar_mensagem(
        self,
        clinica_id: str,
        telefone: str,
        mensagem: str,
        thread_id: str
    ) -> dict:
        """
        Processa mensagem através do grafo.
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Tenta recuperar estado existente
        try:
            state_snapshot = await self.graph.aget_state(config)
            if state_snapshot and state_snapshot.values:
                # Conversa existente - PRESERVA o estado anterior!
                estado_anterior = dict(state_snapshot.values)
                
                # Atualiza só o que mudou
                estado_anterior["mensagem_atual"] = mensagem
                estado_anterior["conversa_id"] = thread_id
                
                # Adiciona mensagem ao histórico (se existir)
                msgs = estado_anterior.get("mensagens", [])
                msgs.append({"role": "user", "content": mensagem, "timestamp": datetime.now().isoformat()})
                estado_anterior["mensagens"] = msgs
                
                input_state = estado_anterior
                print(f"[GRAPH] Continuando conversa: {thread_id[:8]}...")
                print(f"[GRAPH] Estado preservado: cliente_id={estado_anterior.get('cliente_id')}, rascunho={estado_anterior.get('rascunho_cadastro')}")
            else:
                # Nova conversa
                input_state = criar_estado_inicial(clinica_id, telefone, thread_id)
                input_state["mensagem_atual"] = mensagem
                print(f"[GRAPH] Nova conversa: {thread_id[:8]}...")
        except Exception as e:
            print(f"[WARN] Erro ao recuperar estado: {e}")
            import traceback
            traceback.print_exc()
            input_state = criar_estado_inicial(clinica_id, telefone, thread_id)
            input_state["mensagem_atual"] = mensagem
        
        # Executa
        result = await self.graph.ainvoke(input_state, config)
        
        # Monta resposta
        return {
            "resposta": result.get("resposta", ""),
            "cliente_id": result.get("cliente_id"),
            "paciente_id": result.get("cliente_id"),  # Alias
            "card_id": result.get("card_id"),
            "agendamento_id": result.get("agendamento_id"),
            "consulta_agendada": result.get("consulta_agendada"),
            "acoes_executadas": [a.get("ferramenta", a) if isinstance(a, dict) else a for a in result.get("acoes_executadas", [])],
            "erro": result.get("erro"),
            "rascunho_cadastro": result.get("rascunho_cadastro"),  # Debug
        }


# ============================================================================
# FACTORY
# ============================================================================

def criar_chat_graph(db, llm_client, connection_string: str = None) -> ChatGraph:
    """Cria instância do ChatGraph."""
    
    checkpointer = None
    
    if connection_string and POSTGRES_DISPONIVEL:
        try:
            from psycopg_pool import AsyncConnectionPool
            
            pool = AsyncConnectionPool(conninfo=connection_string)
            checkpointer = AsyncPostgresSaver(pool)
            
            print("[INFO] ChatGraph usando AsyncPostgresSaver")
        except Exception as e:
            print(f"[WARN] Falha AsyncPostgresSaver: {e}")
            import traceback
            traceback.print_exc()
            checkpointer = MemorySaver()
            print("[INFO] ChatGraph usando MemorySaver (fallback)")
    else:
        checkpointer = MemorySaver()
        print("[INFO] ChatGraph usando MemorySaver")
    
    return ChatGraph(db, llm_client, checkpointer)
