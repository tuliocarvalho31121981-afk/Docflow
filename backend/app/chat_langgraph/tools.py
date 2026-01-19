# app/chat_langgraph/tools.py
"""
Ferramentas do Agente - Fase 0 (Pré-Agendamento)

FLUXO PRINCIPAL:
1. verificar_cliente - Identifica cliente pelo telefone
2. cadastrar_cliente - Cria paciente + card
3. atualizar_card - Registra intenção, atualiza interação
4. ver_horarios - Lista disponíveis
5. agendar_consulta - Marca na agenda + vincula ao card

AUXILIARES:
- ver_info_clinica: Valores, convênios, endereço
- atualizar_rascunho: Preenche formulário em memória
- gerenciar_consulta: Confirmar, remarcar, cancelar
"""

import re
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


# ============================================================================
# RESULTADO PADRÃO
# ============================================================================

@dataclass
class ToolResult:
    """Resultado padronizado de uma ferramenta."""
    sucesso: bool
    dados: Optional[Dict[str, Any]] = None
    erro: Optional[str] = None

    def to_dict(self) -> dict:
        if self.sucesso:
            return self.dados or {}
        return {"erro": self.erro}


# ============================================================================
# TOOL 1: VERIFICAR CLIENTE
# ============================================================================

async def verificar_cliente(db, clinica_id: str, telefone: str) -> dict:
    """
    Verifica se cliente existe e retorna contexto completo.
    
    SEMPRE chamar no início de toda conversa.
    
    Retorna:
    - Se existe ou não
    - Dados cadastrais (se existir)
    - Se tem consulta agendada (e qual)
    - Se tem card ativo (e em qual coluna)
    - Se convênio está válido
    """
    resultado = {
        "existe": False,
        "cliente": None,
        "consulta_agendada": None,
        "card": None,
        "convenio_valido": None
    }
    
    try:
        # Busca cliente pelo celular
        cliente = await db.select_one(
            table="pacientes",
            filters={"clinica_id": clinica_id, "celular": telefone}
        )
        
        # Se não achou por celular, tenta por whatsapp
        if not cliente:
            cliente = await db.select_one(
                table="pacientes",
                filters={"clinica_id": clinica_id, "whatsapp": telefone}
            )
        
        if not cliente:
            return resultado
        
        resultado["existe"] = True
        resultado["cliente"] = {
            "id": cliente["id"],
            "nome": cliente.get("nome"),
            "nome_curto": cliente.get("nome", "").split()[0] if cliente.get("nome") else None,
            "cpf": cliente.get("cpf"),
            "data_nascimento": str(cliente.get("data_nascimento")) if cliente.get("data_nascimento") else None,
            "convenio": cliente.get("convenio_nome"),
            "carteirinha": cliente.get("convenio_numero"),
            "cadastro_completo": all([
                cliente.get("nome"),
                cliente.get("cpf"),
                cliente.get("data_nascimento"),
                cliente.get("convenio_nome") or True  # Particular é válido
            ])
        }
        
        # Busca card ativo do cliente
        cards = await db.select(
            table="cards",
            filters={
                "clinica_id": clinica_id,
                "paciente_id": cliente["id"],
                "status": "ativo"
            },
            order_by="created_at",
            order_asc=False,
            limit=1
        )
        
        if cards:
            card = cards[0]
            resultado["card"] = {
                "id": card["id"],
                "fase": card.get("fase"),
                "coluna": card.get("coluna"),
                "intencao_inicial": card.get("intencao_inicial"),
                "ultima_interacao": str(card.get("ultima_interacao")) if card.get("ultima_interacao") else None,
                "tentativa_reativacao": card.get("tentativa_reativacao", 0),
                "convenio_validado": card.get("convenio_validado", False),
                "convenio_status": card.get("convenio_status"),
            }
        
        # Busca consulta agendada (se tiver)
        agendamentos = await db.select(
            table="agendamentos",
            filters={
                "clinica_id": clinica_id,
                "paciente_id": cliente["id"],
                "status": "agendado"
            },
            order_by="data",
            limit=1
        )
        
        if agendamentos:
            ag = agendamentos[0]
            data_str = str(ag["data"]) if ag.get("data") else None
            if data_str:
                try:
                    data_obj = datetime.strptime(data_str[:10], "%Y-%m-%d")
                    dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][data_obj.weekday()]
                    hora = ag.get("hora") or ag.get("hora_inicio")
                    hora_str = str(hora)[:5] if hora else ""
                    
                    resultado["consulta_agendada"] = {
                        "id": ag["id"],
                        "data": data_str[:10],
                        "hora": hora_str,
                        "data_formatada": f"{dia_semana}, {data_obj.strftime('%d/%m')} às {hora_str}",
                        "medico": ag.get("medico_nome", "Dr. Carlos"),
                        "tipo": "Retorno" if not ag.get("primeira_vez", True) else "Primeira vez",
                        "confirmada": ag.get("confirmado", False)
                    }
                except:
                    pass
        
        # Valida convênio (simplificado)
        convenio = cliente.get("convenio_nome")
        if convenio and convenio.lower() != "particular":
            resultado["convenio_valido"] = True
        else:
            resultado["convenio_valido"] = None  # Particular não precisa validar
        
        return resultado
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 2: CADASTRAR CLIENTE
# ============================================================================

async def cadastrar_cliente(
    db,
    clinica_id: str,
    telefone: str,
    nome: str,
    cpf: str,
    data_nascimento: str,
    convenio: str,
    carteirinha: Optional[str] = None,
    intencao_inicial: Optional[str] = None
) -> dict:
    """
    Cadastra cliente novo OU atualiza existente.
    Também cria o card automaticamente na Fase 0.
    
    Recebe todos os dados de uma vez (formulário completo).
    """
    try:
        # Limpa CPF
        cpf_limpo = re.sub(r'\D', '', cpf)
        if len(cpf_limpo) != 11:
            return {"erro": "CPF deve ter 11 dígitos"}
        
        # Normaliza data de nascimento
        data_nasc = _normalizar_data(data_nascimento)
        if not data_nasc:
            return {"erro": "Data de nascimento inválida. Use DD/MM/AAAA"}
        
        # Verifica se já existe pelo telefone
        existente = await db.select_one(
            table="pacientes",
            filters={"clinica_id": clinica_id, "celular": telefone}
        )
        
        # Se não achou por celular, tenta por whatsapp
        if not existente:
            existente = await db.select_one(
                table="pacientes",
                filters={"clinica_id": clinica_id, "whatsapp": telefone}
            )
        
        # Monta dados do paciente
        agora = datetime.now()
        dados_paciente = {
            "nome": nome.strip().title(),
            "cpf": cpf_limpo,
            "data_nascimento": data_nasc,
            "convenio_nome": convenio.strip() if convenio else "Particular",
            "convenio_numero": carteirinha,
            "celular": telefone,
            "whatsapp": telefone,
            "updated_at": agora.isoformat()
        }
        
        if existente:
            # Atualiza paciente existente
            cliente_id = existente["id"]
            await db.update(
                table="pacientes",
                data=dados_paciente,
                filters={"id": cliente_id}
            )
        else:
            # Cria novo paciente
            cliente_id = str(uuid.uuid4())
            dados_paciente.update({
                "id": cliente_id,
                "clinica_id": clinica_id,
                "ativo": True,
                "como_conheceu": "whatsapp",
                "created_at": agora.isoformat()
            })
            await db.insert("pacientes", dados_paciente)
        
        # Verifica se já tem card ativo
        cards_existentes = await db.select(
            table="cards",
            filters={
                "clinica_id": clinica_id,
                "paciente_id": cliente_id,
                "status": "ativo"
            },
            limit=1
        )
        
        if cards_existentes:
            # Atualiza card existente
            card_id = cards_existentes[0]["id"]
            await db.update(
                table="cards",
                data={
                    "paciente_nome": nome.strip().title(),
                    "intencao_inicial": intencao_inicial,
                    "ultima_interacao": agora.isoformat(),
                    "updated_at": agora.isoformat()
                },
                filters={"id": card_id}
            )
        else:
            # Cria card novo na Fase 0
            card_id = str(uuid.uuid4())
            await db.insert("cards", {
                "id": card_id,
                "clinica_id": clinica_id,
                "paciente_id": cliente_id,
                "paciente_nome": nome.strip().title(),
                "paciente_telefone": telefone,
                "fase": 0,
                "coluna": "pre_agendamento",
                "status": "ativo",
                "prioridade": "normal",
                "origem": "whatsapp",
                "intencao_inicial": intencao_inicial,
                "ultima_interacao": agora.isoformat(),
                "tentativa_reativacao": 0,
                "convenio_validado": False,
                "fase0_em": agora.isoformat(),
                "created_at": agora.isoformat(),
                "updated_at": agora.isoformat()
            })
        
        return {
            "sucesso": True,
            "cliente_id": cliente_id,
            "card_id": card_id,
            "nome": nome.strip().title(),
            "convenio": convenio.strip() if convenio else "Particular",
            "eh_particular": convenio.lower() == "particular" if convenio else True
        }
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 3: ATUALIZAR CARD
# ============================================================================

async def atualizar_card(
    db,
    clinica_id: str,
    card_id: str,
    intencao_inicial: Optional[str] = None,
    coluna: Optional[str] = None,
    motivo_saida: Optional[str] = None,
    convenio_status: Optional[str] = None
) -> dict:
    """
    Atualiza dados do card.
    
    Usado para:
    - Registrar intenção inicial
    - Mover entre colunas
    - Registrar motivo de saída
    - Atualizar status do convênio
    """
    try:
        agora = datetime.now()
        update_data = {
            "ultima_interacao": agora.isoformat(),
            "updated_at": agora.isoformat()
        }
        
        if intencao_inicial:
            update_data["intencao_inicial"] = intencao_inicial
        
        if coluna:
            update_data["coluna"] = coluna
            # Atualiza tentativa de reativação se for coluna de reativação
            if coluna == "reativacao_1":
                update_data["tentativa_reativacao"] = 1
            elif coluna == "reativacao_2":
                update_data["tentativa_reativacao"] = 2
            elif coluna == "reativacao_3":
                update_data["tentativa_reativacao"] = 3
            elif coluna == "perdido":
                update_data["status"] = "perdido"
        
        if motivo_saida:
            update_data["motivo_saida"] = motivo_saida
        
        if convenio_status:
            update_data["convenio_status"] = convenio_status
            update_data["convenio_validado"] = convenio_status not in ["nao_validado", None]
        
        await db.update(
            table="cards",
            data=update_data,
            filters={"id": card_id}
        )
        
        return {
            "sucesso": True,
            "card_id": card_id,
            "atualizado": list(update_data.keys())
        }
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 4: VER HORÁRIOS
# ============================================================================

async def ver_horarios(db, clinica_id: str, dias: int = 7) -> dict:
    """
    Lista horários disponíveis para agendamento.
    
    Retorna próximos dias úteis com slots disponíveis.
    """
    try:
        hoje = datetime.now()
        slots = []
        
        for i in range(1, dias + 1):
            data = hoje + timedelta(days=i)
            
            # Pula fim de semana
            if data.weekday() >= 5:
                continue
            
            dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][data.weekday()]
            
            # TODO: Em produção, buscar da tabela de agenda real
            horarios_do_dia = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            
            slots.append({
                "data": data.strftime("%Y-%m-%d"),
                "data_formatada": f"{dia_semana}, {data.strftime('%d/%m')}",
                "horarios": horarios_do_dia
            })
            
            if len(slots) >= 5:
                break
        
        return {
            "horarios_disponiveis": slots,
            "total_dias": len(slots)
        }
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 5: AGENDAR CONSULTA
# ============================================================================

async def agendar_consulta(
    db,
    clinica_id: str,
    cliente_id: str,
    data: str,
    hora: str
) -> dict:
    """
    Cria o agendamento da consulta.
    Move o card da Fase 0 para Fase 1 (Pré-Consulta).
    
    Pré-requisitos:
    - Cliente cadastrado (com ID)
    - Data e hora escolhidos
    """
    try:
        # Busca o card do cliente
        cards = await db.select(
            table="cards",
            filters={"clinica_id": clinica_id, "paciente_id": cliente_id, "status": "ativo"},
            order_by="created_at",
            order_asc=False,
            limit=1
        )
        card_id = cards[0]["id"] if cards else None
        
        # Busca médico da clínica
        medicos = await db.select(
            table="usuarios",
            filters={"clinica_id": clinica_id, "tipo": "medico", "ativo": True},
            limit=1
        )
        
        if not medicos:
            todos_usuarios = await db.select(
                table="usuarios",
                filters={"clinica_id": clinica_id, "ativo": True},
                limit=10
            )
            medicos = [u for u in todos_usuarios if u.get("crm")]
        
        if not medicos:
            return {"erro": "Nenhum médico cadastrado na clínica. Configure um médico primeiro."}
        
        medico = medicos[0]
        medico_id = medico["id"]
        medico_nome = medico.get("nome", "Dr.")
        
        # Calcula hora fim (30 min)
        hora_inicio = datetime.strptime(hora, "%H:%M")
        hora_fim = (hora_inicio + timedelta(minutes=30)).strftime("%H:%M")
        
        # Cria agendamento
        agora = datetime.now()
        agendamento_id = str(uuid.uuid4())
        await db.insert("agendamentos", {
            "id": agendamento_id,
            "clinica_id": clinica_id,
            "paciente_id": cliente_id,
            "medico_id": medico_id,
            "card_id": card_id,
            "data": data,
            "hora_inicio": hora,
            "hora_fim": hora_fim,
            "hora": hora,
            "status": "agendado",
            "origem": "whatsapp",
            "primeira_vez": True,
            "confirmado": False,
            "created_at": agora.isoformat(),
            "updated_at": agora.isoformat()
        })
        
        # Atualiza card: vincula agendamento e move para Fase 1
        if card_id:
            await db.update(
                table="cards",
                data={
                    "agendamento_id": agendamento_id,
                    "medico_id": medico_id,
                    "data_agendamento": data,
                    "hora_agendamento": hora,
                    "fase": 1,
                    "coluna": "pre_consulta",
                    "fase1_em": agora.isoformat(),
                    "ultima_interacao": agora.isoformat(),
                    "updated_at": agora.isoformat()
                },
                filters={"id": card_id}
            )
        
        # Formata data para resposta
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][data_obj.weekday()]
        
        return {
            "sucesso": True,
            "agendamento_id": agendamento_id,
            "card_id": card_id,
            "medico_nome": medico_nome,
            "data": data,
            "hora": hora,
            "data_formatada": f"{dia_semana}, {data_obj.strftime('%d/%m')} às {hora}",
            "fase_atual": 1,
            "coluna_atual": "pre_consulta"
        }
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 6: VER CONSULTA
# ============================================================================

async def ver_consulta(db, clinica_id: str, cliente_id: str) -> dict:
    """
    Retorna dados da consulta agendada do cliente.
    """
    try:
        agendamentos = await db.select(
            table="agendamentos",
            filters={
                "clinica_id": clinica_id,
                "paciente_id": cliente_id,
                "status": "agendado"
            },
            order_by="data",
            limit=1
        )
        
        if not agendamentos:
            return {"tem_consulta": False}
        
        ag = agendamentos[0]
        data_str = str(ag["data"])[:10]
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][data_obj.weekday()]
        hora = ag.get("hora") or ag.get("hora_inicio")
        
        return {
            "tem_consulta": True,
            "consulta": {
                "id": ag["id"],
                "data": data_str,
                "hora": str(hora)[:5] if hora else None,
                "data_formatada": f"{dia_semana}, {data_obj.strftime('%d/%m')} às {str(hora)[:5] if hora else ''}",
                "medico": ag.get("medico_nome", "Dr. Carlos"),
                "confirmada": ag.get("confirmado", False),
                "tipo": "Retorno" if not ag.get("primeira_vez", True) else "Primeira consulta"
            }
        }
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 7: GERENCIAR CONSULTA
# ============================================================================

async def gerenciar_consulta(
    db,
    clinica_id: str,
    agendamento_id: str,
    acao: str,
    nova_data: Optional[str] = None,
    nova_hora: Optional[str] = None,
    motivo: Optional[str] = None
) -> dict:
    """
    Confirma, cancela ou remarca uma consulta.
    
    acao: "confirmar", "cancelar", "remarcar"
    """
    try:
        agora = datetime.now()
        
        if acao == "confirmar":
            await db.update(
                table="agendamentos",
                data={"confirmado": True, "updated_at": agora.isoformat()},
                filters={"id": agendamento_id}
            )
            return {"sucesso": True, "acao": "confirmada"}
        
        elif acao == "cancelar":
            # Atualiza agendamento
            await db.update(
                table="agendamentos",
                data={
                    "status": "cancelado",
                    "motivo_cancelamento": motivo,
                    "updated_at": agora.isoformat()
                },
                filters={"id": agendamento_id}
            )
            
            # Move card para reativação
            cards = await db.select(
                table="cards",
                filters={"agendamento_id": agendamento_id},
                limit=1
            )
            if cards:
                await db.update(
                    table="cards",
                    data={
                        "coluna": "reativacao_1",
                        "fase": 0,
                        "motivo_saida": "cancelou",
                        "tentativa_reativacao": 1,
                        "ultima_interacao": agora.isoformat(),
                        "updated_at": agora.isoformat()
                    },
                    filters={"id": cards[0]["id"]}
                )
            
            return {"sucesso": True, "acao": "cancelada", "motivo": motivo}
        
        elif acao == "remarcar":
            if not nova_data or not nova_hora:
                return {"erro": "Para remarcar, preciso da nova data e hora"}
            
            await db.update(
                table="agendamentos",
                data={
                    "data": nova_data,
                    "hora": nova_hora,
                    "hora_inicio": nova_hora,
                    "confirmado": False,
                    "updated_at": agora.isoformat()
                },
                filters={"id": agendamento_id}
            )
            
            # Atualiza card
            cards = await db.select(
                table="cards",
                filters={"agendamento_id": agendamento_id},
                limit=1
            )
            if cards:
                await db.update(
                    table="cards",
                    data={
                        "data_agendamento": nova_data,
                        "hora_agendamento": nova_hora,
                        "ultima_interacao": agora.isoformat(),
                        "updated_at": agora.isoformat()
                    },
                    filters={"id": cards[0]["id"]}
                )
            
            data_obj = datetime.strptime(nova_data, "%Y-%m-%d")
            dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][data_obj.weekday()]
            
            return {
                "sucesso": True,
                "acao": "remarcada",
                "nova_data_formatada": f"{dia_semana}, {data_obj.strftime('%d/%m')} às {nova_hora}"
            }
        
        else:
            return {"erro": f"Ação desconhecida: {acao}"}
        
    except Exception as e:
        return {"erro": str(e)}


# ============================================================================
# TOOL 8: VER INFO CLÍNICA
# ============================================================================

async def ver_info_clinica(db, clinica_id: str, tipo: str = "tudo") -> dict:
    """
    Retorna informações da clínica: valores, convênios, endereço.
    
    tipo: "valores", "convenios", "endereco", "tudo"
    """
    # TODO: Em produção, buscar do banco
    info = {
        "valores": {
            "consulta_particular": "R$ 300,00",
            "retorno_30_dias": "Gratuito",
            "formas_pagamento": ["Dinheiro", "PIX", "Cartão crédito (até 3x)", "Cartão débito"]
        },
        "convenios": [
            "Unimed",
            "Bradesco Saúde",
            "SulAmérica",
            "Amil",
            "Porto Seguro",
            "NotreDame Intermédica"
        ],
        "endereco": {
            "completo": "Rua das Flores, 123 - Sala 45 - Centro",
            "referencia": "Próximo ao Metrô República",
            "estacionamento": "Estacionamento conveniado no prédio"
        },
        "horario_funcionamento": "Segunda a Sexta: 8h às 18h | Sábado: 8h às 12h"
    }
    
    if tipo == "tudo":
        return info
    elif tipo in info:
        return {tipo: info[tipo]}
    else:
        return info


# ============================================================================
# TOOL 9: ATUALIZAR RASCUNHO (Formulário em memória)
# ============================================================================

def atualizar_rascunho(rascunho_atual: dict, campo: str, valor: str) -> dict:
    """
    Preenche um campo no rascunho de cadastro.
    
    Não salva no banco - só na memória (state).
    Quando estiver completo, chama cadastrar_cliente.
    """
    rascunho = dict(rascunho_atual) if rascunho_atual else {}
    
    # Normaliza o campo
    campo = campo.lower().strip()
    
    if campo in ["nome", "nome_completo"]:
        rascunho["nome"] = valor.strip().title()
    
    elif campo == "cpf":
        rascunho["cpf"] = re.sub(r'\D', '', valor)
    
    elif campo in ["nascimento", "data_nascimento", "data de nascimento"]:
        rascunho["data_nascimento"] = _normalizar_data(valor)
    
    elif campo in ["convenio", "convênio", "plano"]:
        rascunho["convenio"] = valor.strip()
    
    elif campo in ["carteirinha", "numero_carteirinha"]:
        rascunho["carteirinha"] = valor.strip()
    
    # Calcula status
    campos_obrigatorios = ["nome", "cpf", "data_nascimento", "convenio"]
    campos_preenchidos = [c for c in campos_obrigatorios if rascunho.get(c)]
    campos_faltando = [c for c in campos_obrigatorios if not rascunho.get(c)]
    
    return {
        "rascunho": rascunho,
        "campos_preenchidos": campos_preenchidos,
        "campos_faltando": campos_faltando,
        "completo": len(campos_faltando) == 0
    }


# ============================================================================
# HELPERS
# ============================================================================

def _normalizar_data(valor: str) -> Optional[str]:
    """Converte data de vários formatos para YYYY-MM-DD."""
    if not valor:
        return None
    
    valor = valor.strip()
    
    # DD/MM/YYYY ou DD-MM-YYYY
    match = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', valor)
    if match:
        dia, mes, ano = match.groups()
        return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
    
    # YYYY-MM-DD (já no formato correto)
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', valor)
    if match:
        return valor
    
    return None


# ============================================================================
# SCHEMAS DAS FERRAMENTAS (para o LLM)
# ============================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "verificar_cliente",
            "description": """Verifica se o cliente existe no sistema e retorna contexto completo.

QUANDO USAR: SEMPRE no início de TODA conversa, se ainda não souber quem é o cliente.

RETORNA:
- Se cliente existe ou não
- Dados cadastrais (nome, CPF, convênio)
- Se tem consulta agendada (data, hora, médico)
- Se tem card ativo (fase, coluna)
- Se cadastro está completo

DEPOIS:
- Não existe → Coletar dados para cadastro
- Existe sem consulta → Perguntar se quer agendar
- Existe com consulta → Perguntar o que precisa""",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_cliente",
            "description": """Cadastra um cliente novo no sistema e cria card na Fase 0.

QUANDO USAR: Depois de coletar TODOS os dados:
- Nome completo
- CPF  
- Data de nascimento
- Convênio (ou "Particular")
- Carteirinha (se tiver convênio)

NÃO USE se ainda falta algum dado.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome completo"
                    },
                    "cpf": {
                        "type": "string",
                        "description": "CPF (11 dígitos)"
                    },
                    "data_nascimento": {
                        "type": "string",
                        "description": "Data nascimento (YYYY-MM-DD ou DD/MM/YYYY)"
                    },
                    "convenio": {
                        "type": "string",
                        "description": "Nome do convênio ou 'Particular'"
                    },
                    "carteirinha": {
                        "type": "string",
                        "description": "Número carteirinha (se tiver convênio)"
                    },
                    "intencao_inicial": {
                        "type": "string",
                        "enum": ["marcar", "saber_valor", "saber_convenio", "faq"],
                        "description": "Intenção identificada do cliente"
                    }
                },
                "required": ["nome", "cpf", "data_nascimento", "convenio"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "atualizar_card",
            "description": """Atualiza dados do card do cliente.

QUANDO USAR:
- Para registrar intenção inicial
- Para mover card entre colunas
- Para registrar motivo de saída""",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "ID do card"
                    },
                    "intencao_inicial": {
                        "type": "string",
                        "enum": ["marcar", "saber_valor", "saber_convenio", "faq", "remarcar", "cancelar", "enviar_exames", "anamnese"],
                        "description": "Intenção do cliente"
                    },
                    "coluna": {
                        "type": "string",
                        "enum": ["pre_agendamento", "aguardando_autorizacao", "aguardando_horario", "reativacao_1", "reativacao_2", "reativacao_3", "perdido"],
                        "description": "Nova coluna do card"
                    },
                    "motivo_saida": {
                        "type": "string",
                        "enum": ["sem_plano", "caro", "horario", "cancelou", "desistiu", "outro"],
                        "description": "Motivo de saída do funil"
                    },
                    "convenio_status": {
                        "type": "string",
                        "enum": ["nao_validado", "ativo", "sem_cobertura", "aguardando_autorizacao", "particular"],
                        "description": "Status do convênio"
                    }
                },
                "required": ["card_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_horarios",
            "description": """Lista horários disponíveis para agendamento.

QUANDO USAR: Cliente quer agendar e já está cadastrado.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "dias": {
                        "type": "integer",
                        "description": "Quantos dias buscar (padrão: 7)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_consulta",
            "description": """Cria o agendamento da consulta e move card para Fase 1.

QUANDO USAR: Cliente escolheu data/hora E está cadastrado.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data (YYYY-MM-DD)"
                    },
                    "hora": {
                        "type": "string",
                        "description": "Hora (HH:MM)"
                    }
                },
                "required": ["data", "hora"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_consulta",
            "description": """Retorna dados da consulta agendada.""",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gerenciar_consulta",
            "description": """Confirma, cancela ou remarca consulta.

AÇÕES:
- "confirmar": Marca como confirmada
- "cancelar": Cancela (perguntar motivo) - Move card para reativação
- "remarcar": Muda data/hora""",
            "parameters": {
                "type": "object",
                "properties": {
                    "agendamento_id": {
                        "type": "string",
                        "description": "ID da consulta"
                    },
                    "acao": {
                        "type": "string",
                        "enum": ["confirmar", "cancelar", "remarcar"],
                        "description": "O que fazer"
                    },
                    "nova_data": {
                        "type": "string",
                        "description": "Nova data se remarcar"
                    },
                    "nova_hora": {
                        "type": "string",
                        "description": "Nova hora se remarcar"
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Motivo do cancelamento"
                    }
                },
                "required": ["agendamento_id", "acao"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_info_clinica",
            "description": """Retorna informações da clínica (valores, convênios, endereço).

QUANDO USAR: Cliente pergunta preço, convênios aceitos ou localização.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["valores", "convenios", "endereco", "tudo"],
                        "description": "Que informação (padrão: tudo)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "atualizar_rascunho",
            "description": """Salva dado no formulário em memória.

QUANDO USAR: A cada dado que o cliente informar durante cadastro.

NÃO SALVA NO BANCO - só guarda até ter todos.
Quando completo, use cadastrar_cliente.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "campo": {
                        "type": "string",
                        "enum": ["nome", "cpf", "data_nascimento", "convenio", "carteirinha"],
                        "description": "Qual campo"
                    },
                    "valor": {
                        "type": "string",
                        "description": "Valor informado"
                    }
                },
                "required": ["campo", "valor"]
            }
        }
    }
]


# ============================================================================
# EXECUTOR
# ============================================================================

async def executar_ferramenta(nome: str, args: dict, db, state: dict) -> dict:
    """Executa uma ferramenta pelo nome."""
    
    clinica_id = state.get("clinica_id")
    telefone = state.get("telefone")
    cliente_id = state.get("cliente_id")
    
    if nome == "verificar_cliente":
        return await verificar_cliente(db, clinica_id, telefone)
    
    elif nome == "cadastrar_cliente":
        return await cadastrar_cliente(
            db, clinica_id, telefone,
            nome=args.get("nome"),
            cpf=args.get("cpf"),
            data_nascimento=args.get("data_nascimento"),
            convenio=args.get("convenio"),
            carteirinha=args.get("carteirinha"),
            intencao_inicial=args.get("intencao_inicial")
        )
    
    elif nome == "atualizar_card":
        card_id = args.get("card_id") or state.get("card_id")
        if not card_id:
            return {"erro": "card_id não informado"}
        return await atualizar_card(
            db, clinica_id, card_id,
            intencao_inicial=args.get("intencao_inicial"),
            coluna=args.get("coluna"),
            motivo_saida=args.get("motivo_saida"),
            convenio_status=args.get("convenio_status")
        )
    
    elif nome == "ver_horarios":
        return await ver_horarios(db, clinica_id, dias=args.get("dias", 7))
    
    elif nome == "agendar_consulta":
        if not cliente_id:
            return {"erro": "Cliente não identificado. Use verificar_cliente primeiro."}
        return await agendar_consulta(db, clinica_id, cliente_id, args.get("data"), args.get("hora"))
    
    elif nome == "ver_consulta":
        if not cliente_id:
            return {"erro": "Cliente não identificado."}
        return await ver_consulta(db, clinica_id, cliente_id)
    
    elif nome == "gerenciar_consulta":
        return await gerenciar_consulta(
            db, clinica_id,
            agendamento_id=args.get("agendamento_id"),
            acao=args.get("acao"),
            nova_data=args.get("nova_data"),
            nova_hora=args.get("nova_hora"),
            motivo=args.get("motivo")
        )
    
    elif nome == "ver_info_clinica":
        return await ver_info_clinica(db, clinica_id, tipo=args.get("tipo", "tudo"))
    
    elif nome == "atualizar_rascunho":
        rascunho_atual = state.get("rascunho_cadastro", {})
        return atualizar_rascunho(rascunho_atual, args.get("campo"), args.get("valor"))
    
    else:
        return {"erro": f"Ferramenta desconhecida: {nome}"}
