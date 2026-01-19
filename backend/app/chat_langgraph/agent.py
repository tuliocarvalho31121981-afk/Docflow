# app/chat_langgraph/agent.py
"""
Agente da Clínica - Simples como um estagiário.

O agente:
1. Recebe mensagem
2. Chama ferramentas quando precisa
3. Responde naturalmente

Não tem mágica. Não tem complexidade desnecessária.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from .tools import TOOLS_SCHEMA, executar_ferramenta


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """Você é Ana, assistente virtual da clínica de cardiologia do Dr. Carlos.

# COMO VOCÊ FUNCIONA

Você é como uma recepcionista simpática. Conversa naturalmente, coleta informações, agenda consultas.

# REGRA OBRIGATÓRIA

SEMPRE que receber uma mensagem, a PRIMEIRA coisa é chamar `verificar_cliente`.
Não responda nada antes de verificar. Isso te dá o contexto completo.

# FLUXOS

## Cliente NOVO (verificar_cliente retornou existe=false):

1. Cumprimente e pergunte o nome
2. Pergunte CPF
3. Pergunte data de nascimento  
4. Pergunte convênio (ou se é particular)
5. Quando tiver tudo, chame `cadastrar_cliente` com todos os dados
6. Pergunte se quer agendar consulta

Use `atualizar_rascunho` para guardar cada dado que coletar.
Só chame `cadastrar_cliente` quando tiver TODOS os dados.

## Cliente JÁ CADASTRADO sem consulta:

1. Cumprimente pelo nome ("Oi João!")
2. Pergunte como pode ajudar
3. Se quer agendar: `ver_horarios` → cliente escolhe → `agendar_consulta`
4. Se quer saber valores/convênios: `ver_info_clinica`

## Cliente COM CONSULTA agendada:

1. Cumprimente e mencione a consulta ("Vi que você tem consulta dia X")
2. Pergunte o que precisa: confirmar, remarcar, cancelar?
3. Use `gerenciar_consulta` conforme o pedido

# ESTILO

- Seja simpática mas objetiva
- Use 1-2 emojis por mensagem, não mais
- Respostas curtas (2-4 linhas)
- Não repita informações que já deu

# CONTEXTO ATUAL

{contexto}

# DADOS COLETADOS (rascunho do cadastro)

{rascunho}
"""


# ============================================================================
# CLASSE DO AGENTE
# ============================================================================

class AgenteClinica:
    """
    Agente de atendimento da clínica.
    
    Usa LLM com function calling para decidir ações.
    """
    
    def __init__(self, llm_client, db):
        self.llm_client = llm_client
        self.db = db
        self.max_iteracoes = 5
    
    async def processar(self, state: dict) -> dict:
        """Processa mensagem e retorna estado atualizado."""
        
        # Monta contexto e rascunho para o prompt
        contexto = self._montar_contexto(state)
        rascunho = json.dumps(state.get("rascunho_cadastro", {}), indent=2, ensure_ascii=False)
        
        system = SYSTEM_PROMPT.format(contexto=contexto, rascunho=rascunho)
        messages = self._montar_mensagens(state)
        
        # Loop do agente
        acoes = []
        state_atual = dict(state)
        
        for i in range(self.max_iteracoes):
            print(f"[AGENTE] Iteração {i+1}")
            
            # Chama LLM
            resposta = await self._chamar_llm(system, messages)
            
            # Se não tem tool calls, é a resposta final
            tool_calls = resposta.get("tool_calls", [])
            if not tool_calls:
                return {
                    **state_atual,
                    "resposta": resposta.get("content", ""),
                    "acoes_executadas": acoes,
                    "updated_at": datetime.now().isoformat()
                }
            
            # Executa cada ferramenta
            for tc in tool_calls:
                nome = tc.get("function", {}).get("name", "")
                args_str = tc.get("function", {}).get("arguments", "{}")
                
                try:
                    args = json.loads(args_str)
                except:
                    args = {}
                
                print(f"[AGENTE] Chamando: {nome}({args})")
                
                resultado = await executar_ferramenta(nome, args, self.db, state_atual)
                print(f"[AGENTE] Resultado: {resultado}")
                
                # Atualiza state
                state_atual = self._atualizar_state(state_atual, nome, resultado)
                
                acoes.append({
                    "ferramenta": nome,
                    "args": args,
                    "resultado": resultado
                })
                
                # Adiciona na conversa para o LLM ver
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tc]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps(resultado, ensure_ascii=False)
                })
        
        # Limite de iterações
        return {
            **state_atual,
            "resposta": "Desculpe, tive um problema. Pode repetir?",
            "acoes_executadas": acoes,
            "erro": "Limite de iterações",
            "updated_at": datetime.now().isoformat()
        }
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def _montar_contexto(self, state: dict) -> str:
        """Monta string de contexto."""
        partes = []
        
        if state.get("cliente_id"):
            dados = state.get("dados_cliente", {})
            nome = dados.get("nome", "Cliente")
            partes.append(f"Cliente: {nome}")
            
            if not dados.get("cadastro_completo"):
                partes.append("Cadastro INCOMPLETO")
            
            if state.get("consulta_agendada"):
                c = state["consulta_agendada"]
                partes.append(f"Consulta: {c.get('data_formatada', c.get('data'))}")
                if c.get("confirmada"):
                    partes.append("(Confirmada)")
        else:
            partes.append("Cliente não identificado")
        
        return "\n".join(partes) if partes else "Início da conversa"
    
    def _montar_mensagens(self, state: dict) -> List[Dict]:
        """Monta histórico de mensagens."""
        messages = []
        
        # Histórico
        for msg in state.get("historico_mensagens", [])[-10:]:
            role = "user" if msg.get("direcao") == "recebida" else "assistant"
            messages.append({"role": role, "content": msg.get("conteudo", "")})
        
        # Mensagem atual
        if state.get("mensagem_atual"):
            messages.append({"role": "user", "content": state["mensagem_atual"]})
        
        return messages
    
    async def _chamar_llm(self, system: str, messages: List[Dict]) -> dict:
        """Chama o LLM."""
        import httpx
        
        api_key = self.llm_client.api_key
        model = self.llm_client.model
        base_url = self.llm_client.base_url
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if "openrouter" in base_url.lower():
            headers["HTTP-Referer"] = "https://clinicos.app"
            headers["X-Title"] = "ClinicOS"
        
        body = {
            "model": model,
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", [])
        }
    
    def _atualizar_state(self, state: dict, ferramenta: str, resultado: dict) -> dict:
        """Atualiza state com resultado da ferramenta."""
        novo = dict(state)
        
        if ferramenta == "verificar_cliente":
            if resultado.get("existe"):
                cliente = resultado.get("cliente", {})
                novo["cliente_id"] = cliente.get("id")
                novo["cliente_existe"] = True
                novo["dados_cliente"] = cliente
                
                if resultado.get("consulta_agendada"):
                    novo["consulta_agendada"] = resultado["consulta_agendada"]
            else:
                novo["cliente_existe"] = False
        
        elif ferramenta == "cadastrar_cliente":
            if resultado.get("sucesso"):
                novo["cliente_id"] = resultado.get("cliente_id")
                novo["cliente_existe"] = True
                novo["card_id"] = resultado.get("card_id")
                novo["dados_cliente"] = {
                    "nome": resultado.get("nome"),
                    "cadastro_completo": True
                }
                novo["rascunho_cadastro"] = {}  # Limpa rascunho
        
        elif ferramenta == "agendar_consulta":
            if resultado.get("sucesso"):
                novo["agendamento_id"] = resultado.get("agendamento_id")
                novo["consulta_agendada"] = {
                    "id": resultado.get("agendamento_id"),
                    "data": resultado.get("data"),
                    "hora": resultado.get("hora"),
                    "data_formatada": resultado.get("data_formatada")
                }
        
        elif ferramenta == "atualizar_rascunho":
            if resultado.get("rascunho"):
                novo["rascunho_cadastro"] = resultado["rascunho"]
        
        elif ferramenta == "gerenciar_consulta":
            if resultado.get("sucesso"):
                acao = resultado.get("acao")
                if acao == "cancelada":
                    novo["consulta_agendada"] = None
                elif acao == "remarcada":
                    novo["consulta_agendada"] = {
                        **novo.get("consulta_agendada", {}),
                        "data_formatada": resultado.get("nova_data_formatada")
                    }
                elif acao == "confirmada":
                    if novo.get("consulta_agendada"):
                        novo["consulta_agendada"]["confirmada"] = True
        
        return novo


# ============================================================================
# FACTORY
# ============================================================================

def criar_agente(llm_client, db) -> AgenteClinica:
    """Cria instância do agente."""
    return AgenteClinica(llm_client, db)
