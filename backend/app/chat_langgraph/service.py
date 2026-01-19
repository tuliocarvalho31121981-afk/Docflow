# app/chat_langgraph/service.py
"""
Serviço principal de Chat LangGraph - ADAPTADO PARA CLINICOS
Usa SupabaseClient wrapper e retorna formato compatível com frontend
"""

from typing import Optional
from datetime import datetime
import httpx
import uuid

from .graph import criar_chat_graph, ChatGraph
from .states import ConversaState
from .schemas import converter_estado_para_response


class ChatService:
    """
    Serviço de chat usando LangGraph.
    Gerencia conversas, persistência e integração com Kestra.
    """
    
    def __init__(
        self,
        db,
        llm_client,
        kestra_url: str = None,
        kestra_token: str = None,
        pg_connection_string: str = None
    ):
        """
        Inicializa o serviço de chat.
        
        Args:
            db: SupabaseClient wrapper
            llm_client: Cliente LLM (Groq)
            kestra_url: URL base do Kestra (para webhooks)
            kestra_token: Token de autenticação Kestra
            pg_connection_string: Conexão PostgreSQL para checkpointer
        """
        self.db = db
        self.llm_client = llm_client
        self.kestra_url = kestra_url
        self.kestra_token = kestra_token
        
        # Cria o grafo
        self.graph = criar_chat_graph(
            db=db,
            llm_client=llm_client,
            connection_string=pg_connection_string
        )
    
    # ========================================
    # MÉTODO PRINCIPAL
    # ========================================
    
    async def processar_mensagem(
        self,
        clinica_id: str,
        telefone: str,
        mensagem: str,
        tipo_mensagem: str = "texto",
        midia_url: str = None
    ) -> dict:
        """
        Processa uma mensagem recebida do paciente.
        
        Returns:
            dict compatível com ChatResponse do frontend
        """
        
        # Tempo de início
        inicio = datetime.now()
        
        # Normaliza telefone
        telefone = self._normalizar_telefone(telefone)
        
        # Busca ou cria conversa
        conversa = await self._get_ou_criar_conversa(clinica_id, telefone)
        conversa_id = conversa.get("id", str(uuid.uuid4()))
        
        # Registra mensagem recebida
        await self._registrar_mensagem(
            conversa_id=conversa_id,
            direcao="recebida",
            conteudo=mensagem,
            tipo=tipo_mensagem,
            midia_url=midia_url
        )
        
        # Processa com o grafo
        try:
            resultado = await self.graph.processar_mensagem(
                clinica_id=clinica_id,
                telefone=telefone,
                mensagem=mensagem,
                thread_id=conversa_id
            )
        except Exception as e:
            print(f"[ERROR] Falha no grafo: {e}")
            resultado = {
                "resposta": "Desculpe, ocorreu um erro. Tente novamente.",
                "estado": "erro",
                "intencao": "DESCONHECIDO",
                "confianca_intencao": 0,
                "acoes_executadas": [],
                "erro": str(e)
            }
        
        # Registra resposta
        await self._registrar_mensagem(
            conversa_id=conversa_id,
            direcao="enviada",
            conteudo=resultado.get("resposta", ""),
            tipo="texto"
        )
        
        # Dispara webhooks Kestra se necessário
        await self._disparar_webhooks(resultado, clinica_id)
        
        # Atualiza conversa
        await self._atualizar_conversa(conversa_id, resultado)
        
        # Calcula tempo de processamento
        tempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        
        # Adiciona dados extras ao resultado
        resultado["conversa_id"] = conversa_id
        resultado["tempo_processamento_ms"] = tempo_ms
        
        # CONVERTE PARA FORMATO DO FRONTEND
        return converter_estado_para_response(resultado)
    
    # ========================================
    # MÉTODOS DE CONVERSA (usando SupabaseClient)
    # ========================================
    
    async def _get_ou_criar_conversa(self, clinica_id: str, telefone: str) -> dict:
        """Busca conversa ativa ou cria nova"""
        
        try:
            # Busca conversa ativa usando SupabaseClient wrapper
            conversas = await self.db.select(
                table="conversas",
                filters={
                    "clinica_id": clinica_id,
                    "telefone": telefone,
                    "ativa": True
                },
                order_by="created_at",
                order_asc=False,
                limit=1
            )
            
            if conversas:
                return conversas[0]
        except Exception as e:
            print(f"[WARN] Erro ao buscar conversa: {e}")
        
        # Cria nova conversa
        nova_conversa = {
            "id": str(uuid.uuid4()),
            "clinica_id": clinica_id,
            "telefone": telefone,
            "ativa": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            result = await self.db.insert("conversas", nova_conversa)
            return result if result else nova_conversa
        except Exception as e:
            print(f"[WARN] Erro ao criar conversa: {e}")
            return nova_conversa
    
    async def _atualizar_conversa(self, conversa_id: str, resultado: dict):
        """Atualiza dados da conversa"""
        
        update_data = {
            "updated_at": datetime.now().isoformat(),
            "paciente_id": resultado.get("paciente_id"),
            "ultima_intencao": resultado.get("intencao"),
            "ultimo_estado": resultado.get("estado")
        }
        
        try:
            await self.db.update(
                table="conversas",
                data=update_data,
                filters={"id": conversa_id}
            )
        except Exception as e:
            print(f"[WARN] Erro ao atualizar conversa: {e}")
    
    async def _registrar_mensagem(
        self,
        conversa_id: str,
        direcao: str,
        conteudo: str,
        tipo: str = "texto",
        midia_url: str = None
    ):
        """Registra mensagem no histórico"""
        
        mensagem = {
            "id": str(uuid.uuid4()),
            "conversa_id": conversa_id,
            "direcao": direcao,
            "tipo": tipo,
            "conteudo": conteudo,
            "midia_url": midia_url,
            "created_at": datetime.now().isoformat()
        }
        
        try:
            await self.db.insert("mensagens", mensagem)
        except Exception as e:
            print(f"[WARN] Erro ao registrar mensagem: {e}")
    
    # ========================================
    # INTEGRAÇÃO KESTRA
    # ========================================
    
    async def _disparar_webhooks(self, resultado: dict, clinica_id: str):
        """Dispara webhooks do Kestra baseado nas ações executadas."""
        
        if not self.kestra_url:
            print("[INFO] Kestra não configurado - pulando webhooks")
            return
        
        acoes = resultado.get("acoes_executadas", [])
        
        webhooks = {
            "card_criado": "confirmacao-consulta",
            "agendamento_criado": "confirmacao-consulta",
            "paciente_criado": "boas-vindas"
        }
        
        for acao in acoes:
            acao_tipo = acao if isinstance(acao, str) else acao.get("tipo", "")
            if acao_tipo in webhooks:
                await self._chamar_kestra(
                    workflow=webhooks[acao_tipo],
                    dados={
                        "clinica_id": clinica_id,
                        "paciente_id": resultado.get("paciente_id"),
                        "card_id": resultado.get("card_id"),
                        "agendamento_id": resultado.get("agendamento_id"),
                        "telefone": resultado.get("telefone"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    async def _chamar_kestra(self, workflow: str, dados: dict):
        """Faz chamada HTTP para webhook do Kestra"""
        
        url = f"{self.kestra_url}/api/v1/executions/webhook/clinica/{workflow}"
        
        headers = {"Content-Type": "application/json"}
        if self.kestra_token:
            headers["Authorization"] = f"Bearer {self.kestra_token}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=dados,
                    headers=headers,
                    timeout=5.0
                )
                print(f"[INFO] Kestra webhook {workflow}: {response.status_code}")
        except httpx.TimeoutException:
            print(f"[WARN] Timeout ao chamar Kestra: {workflow}")
        except Exception as e:
            print(f"[ERROR] Erro ao chamar Kestra: {e}")
    
    # ========================================
    # UTILITÁRIOS
    # ========================================
    
    def _normalizar_telefone(self, telefone: str) -> str:
        """Remove formatação do telefone"""
        import re
        return re.sub(r'[^\d]', '', telefone)
    
    # ========================================
    # MÉTODOS DE CONSULTA
    # ========================================
    
    async def listar_conversas(
        self,
        clinica_id: str,
        apenas_ativas: bool = True,
        limite: int = 50
    ) -> list:
        """Lista conversas da clínica"""
        
        try:
            filters = {"clinica_id": clinica_id}
            if apenas_ativas:
                filters["ativa"] = True
            
            return await self.db.select(
                table="conversas",
                filters=filters,
                order_by="updated_at",
                order_asc=False,
                limit=limite
            )
        except Exception as e:
            print(f"[ERROR] Erro ao listar conversas: {e}")
            return []
    
    async def get_historico(
        self,
        conversa_id: str,
        limite: int = 100
    ) -> list:
        """Retorna histórico de mensagens"""
        
        try:
            return await self.db.select(
                table="mensagens",
                filters={"conversa_id": conversa_id},
                order_by="created_at",
                order_asc=True,
                limit=limite
            )
        except Exception as e:
            print(f"[ERROR] Erro ao buscar histórico: {e}")
            return []
    
    async def get_conversa(
        self,
        telefone: str,
        clinica_id: str
    ) -> Optional[dict]:
        """Busca conversa específica pelo telefone"""
        
        telefone = self._normalizar_telefone(telefone)
        
        try:
            conversas = await self.db.select(
                table="conversas",
                filters={
                    "clinica_id": clinica_id,
                    "telefone": telefone
                },
                order_by="updated_at",
                order_asc=False,
                limit=1
            )
            
            if conversas:
                conversa = conversas[0]
                conversa["mensagens"] = await self.get_historico(conversa["id"])
                return conversa
            
            return None
        except Exception as e:
            print(f"[ERROR] Erro ao buscar conversa: {e}")
            return None
    
    def get_grafo_mermaid(self) -> str:
        """Retorna representação Mermaid do grafo"""
        try:
            return self.graph.get_mermaid()
        except Exception as e:
            print(f"[ERROR] Erro ao gerar diagrama: {e}")
            return "graph TD\n  A[Erro ao gerar diagrama]"


# ============================================
# FACTORY FUNCTION
# ============================================

def criar_chat_service(
    db,
    llm_client,
    settings = None
) -> ChatService:
    """Cria instância do ChatService com configurações."""
    
    kestra_url = None
    kestra_token = None
    pg_connection = None
    
    if settings:
        kestra_url = getattr(settings, 'kestra_url', None) or getattr(settings, 'KESTRA_URL', None)
        kestra_token = getattr(settings, 'kestra_token', None) or getattr(settings, 'KESTRA_TOKEN', None)
        pg_connection = getattr(settings, 'supabase_db_url', None) or getattr(settings, 'SUPABASE_DB_URL', None)
    
    return ChatService(
        db=db,
        llm_client=llm_client,
        kestra_url=kestra_url,
        kestra_token=kestra_token,
        pg_connection_string=pg_connection
    )
