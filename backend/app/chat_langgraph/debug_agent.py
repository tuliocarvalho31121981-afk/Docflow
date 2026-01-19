#!/usr/bin/env python3
# debug_agent.py
"""
Debug do Agente - Testa se as ferramentas são chamadas corretamente.

Uso:
    python debug_agent.py

Simula conversas e mostra quais ferramentas são chamadas.
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass


# ============================================================================
# MOCK DO BANCO DE DADOS
# ============================================================================

class MockDB:
    """Banco de dados fake para testes."""
    
    def __init__(self):
        self.pacientes = {}
        self.agendamentos = {}
        self.cards = {}
    
    async def select_one(self, table: str, filters: dict) -> dict | None:
        if table == "pacientes":
            telefone = filters.get("telefone")
            return self.pacientes.get(telefone)
        return None
    
    async def select(self, table: str, filters: dict = None, order_by: str = None, 
                     order_asc: bool = True, limit: int = None) -> list:
        if table == "agendamentos":
            paciente_id = filters.get("paciente_id")
            return [a for a in self.agendamentos.values() if a.get("paciente_id") == paciente_id]
        if table == "cards":
            paciente_id = filters.get("paciente_id")
            return [c for c in self.cards.values() if c.get("paciente_id") == paciente_id]
        if table == "mensagens":
            return []
        return []
    
    async def insert(self, table: str, data: dict):
        if table == "pacientes":
            self.pacientes[data.get("telefone")] = data
        elif table == "agendamentos":
            self.agendamentos[data.get("id")] = data
        elif table == "cards":
            self.cards[data.get("id")] = data
    
    async def update(self, table: str, data: dict, filters: dict):
        if table == "pacientes":
            for tel, pac in self.pacientes.items():
                if pac.get("id") == filters.get("id"):
                    self.pacientes[tel].update(data)
        elif table == "agendamentos":
            ag_id = filters.get("id")
            if ag_id in self.agendamentos:
                self.agendamentos[ag_id].update(data)
        elif table == "cards":
            card_id = filters.get("id")
            if card_id in self.cards:
                self.cards[card_id].update(data)


# ============================================================================
# MOCK DO LLM CLIENT
# ============================================================================

class MockLLMClient:
    """LLM fake que simula respostas baseado em regras."""
    
    def __init__(self):
        self.api_key = "fake-key"
        self.model = "mock-model"
        self.base_url = "http://localhost"
        self.call_count = 0
        self.tool_calls_history = []
    
    def set_next_response(self, content: str = None, tool_calls: list = None):
        """Define próxima resposta do LLM."""
        self._next_response = {
            "content": content,
            "tool_calls": tool_calls or []
        }
    
    def get_response(self) -> dict:
        """Retorna resposta configurada."""
        self.call_count += 1
        if hasattr(self, '_next_response'):
            resp = self._next_response
            self._next_response = {"content": "Ok!", "tool_calls": []}
            return resp
        return {"content": "Resposta padrão", "tool_calls": []}


# ============================================================================
# AGENTE DE DEBUG (versão simplificada para teste)
# ============================================================================

class AgenteDebug:
    """Agente com debug detalhado."""
    
    def __init__(self, db: MockDB):
        self.db = db
        self.ferramentas_chamadas = []
        self.logs = []
    
    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {msg}"
        self.logs.append(log_entry)
        print(log_entry)
    
    async def processar(self, clinica_id: str, telefone: str, mensagem: str) -> dict:
        """Processa mensagem e retorna debug completo."""
        
        self.ferramentas_chamadas = []
        self.logs = []
        
        self.log(f"📩 MENSAGEM: '{mensagem}'")
        self.log(f"📱 TELEFONE: {telefone}")
        self.log("-" * 50)
        
        # Importa ferramentas
        from tools import (
            verificar_cliente, cadastrar_cliente, ver_horarios, 
            agendar_consulta, ver_info_clinica, atualizar_rascunho
        )
        
        state = {
            "clinica_id": clinica_id,
            "telefone": telefone,
            "cliente_id": None,
            "rascunho_cadastro": {}
        }
        
        # PASSO 1: Sempre verificar cliente primeiro
        self.log("🔍 Chamando: verificar_cliente")
        resultado = await verificar_cliente(self.db, clinica_id, telefone)
        self.ferramentas_chamadas.append(("verificar_cliente", {}, resultado))
        self.log(f"   Resultado: existe={resultado.get('existe')}")
        
        if resultado.get("existe"):
            cliente = resultado.get("cliente", {})
            state["cliente_id"] = cliente.get("id")
            state["dados_cliente"] = cliente
            self.log(f"   Cliente: {cliente.get('nome')}")
            
            if resultado.get("consulta_agendada"):
                consulta = resultado["consulta_agendada"]
                self.log(f"   Consulta: {consulta.get('data_formatada')}")
        
        self.log("-" * 50)
        
        # PASSO 2: Analisar intenção da mensagem
        intencao = self._detectar_intencao(mensagem)
        self.log(f"🎯 INTENÇÃO DETECTADA: {intencao}")
        self.log("-" * 50)
        
        # PASSO 3: Executar ação baseada na intenção
        if not resultado.get("existe"):
            # Cliente novo - precisa cadastrar
            self.log("👤 Cliente NOVO - iniciando cadastro")
            
            # Simula coleta de dados
            dados_na_mensagem = self._extrair_dados(mensagem)
            for campo, valor in dados_na_mensagem.items():
                self.log(f"📝 Chamando: atualizar_rascunho({campo}={valor})")
                res = atualizar_rascunho(state.get("rascunho_cadastro", {}), campo, valor)
                self.ferramentas_chamadas.append(("atualizar_rascunho", {"campo": campo, "valor": valor}, res))
                state["rascunho_cadastro"] = res.get("rascunho", {})
                self.log(f"   Faltam: {res.get('campos_faltando')}")
        
        elif intencao == "AGENDAR":
            self.log("📅 Buscando horários...")
            self.log("🔍 Chamando: ver_horarios")
            horarios = await ver_horarios(self.db, clinica_id)
            self.ferramentas_chamadas.append(("ver_horarios", {}, horarios))
            self.log(f"   Encontrados: {horarios.get('total_dias')} dias")
        
        elif intencao == "VALOR":
            self.log("💰 Buscando valores...")
            self.log("🔍 Chamando: ver_info_clinica(tipo=valores)")
            info = await ver_info_clinica(self.db, clinica_id, tipo="valores")
            self.ferramentas_chamadas.append(("ver_info_clinica", {"tipo": "valores"}, info))
            self.log(f"   Valor: {info.get('valores', {}).get('consulta_particular')}")
        
        elif intencao == "CONVENIO":
            self.log("🏥 Buscando convênios...")
            self.log("🔍 Chamando: ver_info_clinica(tipo=convenios)")
            info = await ver_info_clinica(self.db, clinica_id, tipo="convenios")
            self.ferramentas_chamadas.append(("ver_info_clinica", {"tipo": "convenios"}, info))
            self.log(f"   Convênios: {info.get('convenios')}")
        
        self.log("=" * 50)
        self.log("📊 RESUMO DAS FERRAMENTAS CHAMADAS:")
        for i, (nome, args, _) in enumerate(self.ferramentas_chamadas, 1):
            args_str = json.dumps(args, ensure_ascii=False) if args else ""
            self.log(f"   {i}. {nome}({args_str})")
        
        return {
            "ferramentas_chamadas": self.ferramentas_chamadas,
            "logs": self.logs,
            "state": state
        }
    
    def _detectar_intencao(self, mensagem: str) -> str:
        """Detecta intenção baseado em palavras-chave."""
        msg = mensagem.lower()
        
        # Ordem importa! Mais específico primeiro
        if any(p in msg for p in ["valor", "preço", "quanto custa", "quanto é"]):
            return "VALOR"
        if any(p in msg for p in ["convênio", "plano", "aceita", "unimed", "bradesco", "amil"]):
            return "CONVENIO"
        if any(p in msg for p in ["remarcar", "mudar", "alterar"]):
            return "REMARCAR"
        if any(p in msg for p in ["cancelar", "desmarcar"]):
            return "CANCELAR"
        if any(p in msg for p in ["confirmo", "confirmado", "vou sim"]):
            return "CONFIRMAR"
        if any(p in msg for p in ["agendar", "marcar", "consulta", "horário", "disponível"]):
            return "AGENDAR"
        
        return "DESCONHECIDO"
    
    def _extrair_dados(self, mensagem: str) -> dict:
        """Extrai dados da mensagem (simplificado)."""
        import re
        dados = {}
        
        # CPF
        cpf_match = re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', mensagem)
        if cpf_match:
            dados["cpf"] = cpf_match.group()
        
        # Data nascimento
        data_match = re.search(r'\d{2}/\d{2}/\d{4}', mensagem)
        if data_match:
            dados["data_nascimento"] = data_match.group()
        
        return dados


# ============================================================================
# CENÁRIOS DE TESTE
# ============================================================================

async def teste_cliente_novo():
    """Testa fluxo de cliente novo."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 1: CLIENTE NOVO QUER AGENDAR")
    print("=" * 60 + "\n")
    
    db = MockDB()
    agente = AgenteDebug(db)
    
    resultado = await agente.processar(
        clinica_id="clinica-123",
        telefone="21999998888",
        mensagem="Oi, quero agendar uma consulta"
    )
    
    # Verifica
    ferramentas = [f[0] for f in resultado["ferramentas_chamadas"]]
    assert "verificar_cliente" in ferramentas, "❌ Deveria chamar verificar_cliente"
    print("\n✅ verificar_cliente foi chamado")
    
    return resultado


async def teste_cliente_existente():
    """Testa fluxo de cliente já cadastrado."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 2: CLIENTE EXISTENTE QUER AGENDAR")
    print("=" * 60 + "\n")
    
    db = MockDB()
    
    # Pré-cadastra cliente
    db.pacientes["21999998888"] = {
        "id": "pac-123",
        "nome": "João Silva",
        "cpf": "12345678900",
        "data_nascimento": "1990-05-15",
        "convenio_nome": "Unimed",
        "telefone": "21999998888"
    }
    
    agente = AgenteDebug(db)
    
    resultado = await agente.processar(
        clinica_id="clinica-123",
        telefone="21999998888",
        mensagem="Quero marcar uma consulta"
    )
    
    # Verifica
    ferramentas = [f[0] for f in resultado["ferramentas_chamadas"]]
    assert "verificar_cliente" in ferramentas, "❌ Deveria chamar verificar_cliente"
    assert "ver_horarios" in ferramentas, "❌ Deveria chamar ver_horarios"
    print("\n✅ verificar_cliente e ver_horarios foram chamados")
    
    return resultado


async def teste_cliente_pergunta_valor():
    """Testa cliente perguntando valor."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 3: CLIENTE PERGUNTA VALOR")
    print("=" * 60 + "\n")
    
    db = MockDB()
    
    # Pré-cadastra cliente
    db.pacientes["21999998888"] = {
        "id": "pac-123",
        "nome": "Maria Santos",
        "cpf": "98765432100",
        "data_nascimento": "1985-03-20",
        "convenio_nome": "Particular",
        "telefone": "21999998888"
    }
    
    agente = AgenteDebug(db)
    
    resultado = await agente.processar(
        clinica_id="clinica-123",
        telefone="21999998888",
        mensagem="Quanto custa a consulta?"
    )
    
    # Verifica
    ferramentas = [f[0] for f in resultado["ferramentas_chamadas"]]
    assert "verificar_cliente" in ferramentas, "❌ Deveria chamar verificar_cliente"
    assert "ver_info_clinica" in ferramentas, "❌ Deveria chamar ver_info_clinica"
    print("\n✅ verificar_cliente e ver_info_clinica foram chamados")
    
    return resultado


async def teste_cliente_pergunta_convenio():
    """Testa cliente perguntando sobre convênios."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 4: CLIENTE PERGUNTA CONVÊNIO")
    print("=" * 60 + "\n")
    
    db = MockDB()
    agente = AgenteDebug(db)
    
    resultado = await agente.processar(
        clinica_id="clinica-123",
        telefone="21777778888",
        mensagem="Vocês aceitam Unimed?"
    )
    
    # Verifica
    ferramentas = [f[0] for f in resultado["ferramentas_chamadas"]]
    assert "verificar_cliente" in ferramentas, "❌ Deveria chamar verificar_cliente"
    print("\n✅ verificar_cliente foi chamado")
    
    return resultado


async def teste_interativo():
    """Modo interativo para testar mensagens."""
    print("\n" + "=" * 60)
    print("🎮 MODO INTERATIVO")
    print("=" * 60)
    print("Digite mensagens para testar. 'sair' para encerrar.\n")
    
    db = MockDB()
    
    # Pergunta se quer simular cliente existente
    simular = input("Simular cliente existente? (s/n): ").strip().lower()
    if simular == 's':
        nome = input("Nome do cliente: ").strip() or "João Silva"
        db.pacientes["21999998888"] = {
            "id": "pac-123",
            "nome": nome,
            "cpf": "12345678900",
            "data_nascimento": "1990-05-15",
            "convenio_nome": "Unimed",
            "telefone": "21999998888"
        }
        print(f"✅ Cliente '{nome}' cadastrado\n")
    
    agente = AgenteDebug(db)
    
    while True:
        mensagem = input("\n📱 Mensagem: ").strip()
        if mensagem.lower() == 'sair':
            break
        
        if not mensagem:
            continue
        
        await agente.processar(
            clinica_id="clinica-123",
            telefone="21999998888",
            mensagem=mensagem
        )


# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("=" * 60)
    print("🔧 DEBUG DO AGENTE - VERIFICAÇÃO DE FERRAMENTAS")
    print("=" * 60)
    
    print("\nEscolha uma opção:")
    print("1. Rodar todos os testes")
    print("2. Modo interativo")
    print("3. Teste específico (cliente novo)")
    print("4. Teste específico (cliente existente)")
    print("5. Teste específico (pergunta valor)")
    print("6. Teste específico (pergunta convênio)")
    
    opcao = input("\nOpção: ").strip()
    
    if opcao == "1":
        await teste_cliente_novo()
        await teste_cliente_existente()
        await teste_cliente_pergunta_valor()
        await teste_cliente_pergunta_convenio()
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
    elif opcao == "2":
        await teste_interativo()
    elif opcao == "3":
        await teste_cliente_novo()
    elif opcao == "4":
        await teste_cliente_existente()
    elif opcao == "5":
        await teste_cliente_pergunta_valor()
    elif opcao == "6":
        await teste_cliente_pergunta_convenio()
    else:
        print("Opção inválida")


if __name__ == "__main__":
    asyncio.run(main())
