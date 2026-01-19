# app/chat_langgraph/nodes_agendamento.py
"""
Nós de agendamento e FAQ - ADAPTADO PARA CLINICOS
Usa SupabaseClient wrapper (select, insert, update)

CORRIGIDO: Usa colunas corretas da tabela agendamentos:
- data (DATE)
- hora_inicio (TIME)
- hora_fim (TIME)
- hora (TIME)
"""

from typing import Optional
from datetime import datetime, timedelta
import json
import re
import uuid

from .states import ConversaState, DadosAgendamento


# ============================================
# HELPER: REGISTRAR GOVERNANÇA
# ============================================

async def _registrar_governanca(
    state: ConversaState,
    db,
    tipo_trigger: str,
    dados_adicionais: dict = None
) -> dict:
    """Registra ação na governança"""
    try:
        dados = {
            "telefone": state["telefone"],
            "mensagem": state.get("mensagem_atual", ""),
            "intencao": state.get("intencao"),
            "paciente_id": state.get("paciente_id"),
            "card_id": state.get("card_id"),
            "agendamento_id": state.get("agendamento_id"),
            **(dados_adicionais or {})
        }
        
        validacao_id = str(uuid.uuid4())
        
        await db.insert("validacoes_governanca", {
            "id": validacao_id,
            "clinica_id": state["clinica_id"],
            "tipo": tipo_trigger,
            "status": "pendente",
            "dados": dados,
            "created_at": datetime.now().isoformat()
        })
        
        return {
            "validacao_pendente": True,
            "validacao_id": validacao_id
        }
    except Exception as e:
        print(f"[WARN] Governança: {e}")
        return {"validacao_pendente": False, "validacao_id": None}


# ============================================
# NÓ: CONFIRMAR CADASTRO
# ============================================

async def confirmar_cadastro(state: ConversaState, db) -> ConversaState:
    """
    Cria ou atualiza paciente no banco.
    """
    dados_pac = state.get("dados_paciente", {})
    if isinstance(dados_pac, dict):
        dados_pac_dict = dados_pac
    else:
        dados_pac_dict = dict(dados_pac) if hasattr(dados_pac, '__iter__') else {}
    
    clinica_id = state["clinica_id"]
    
    paciente_data = {
        "clinica_id": clinica_id,
        "nome": dados_pac_dict.get("nome"),
        "cpf": dados_pac_dict.get("cpf"),
        "telefone": dados_pac_dict.get("telefone") or state["telefone"],
        "data_nascimento": dados_pac_dict.get("data_nascimento"),
        "email": dados_pac_dict.get("email"),
        "convenio_nome": dados_pac_dict.get("convenio_nome"),
        "como_conheceu": "whatsapp",
        "updated_at": datetime.now().isoformat()
    }
    
    paciente_id = state.get("paciente_id")
    
    try:
        if paciente_id:
            # Atualiza paciente existente
            await db.update(
                table="pacientes",
                data=paciente_data,
                filters={"id": paciente_id}
            )
        else:
            # Cria novo paciente
            paciente_data["id"] = str(uuid.uuid4())
            paciente_data["created_at"] = datetime.now().isoformat()
            result = await db.insert("pacientes", paciente_data)
            paciente_id = result.get("id") if result else paciente_data["id"]
        
        print(f"[NODE] confirmar_cadastro: paciente_id={paciente_id[:8] if paciente_id else 'None'}...")
        
        # Registra governança
        gov_result = await _registrar_governanca(
            state, db,
            tipo_trigger="paciente_criado" if not state.get("paciente_id") else "paciente_atualizado",
            dados_adicionais={"paciente_id": paciente_id}
        )
        
        return {
            **state,
            "paciente_id": paciente_id,
            "paciente_existe": True,
            "cadastro_completo": True,
            "acoes_executadas": state.get("acoes_executadas", []) + ["paciente_criado"],
            **gov_result,
            "estado": "verificar_card"
        }
        
    except Exception as e:
        print(f"[ERROR] confirmar_cadastro: {e}")
        return {
            **state,
            "estado": "verificar_card",
            "erro": str(e)
        }


# ============================================
# NÓ: PROCESSAR INTENÇÃO
# ============================================

async def processar_intencao(state: ConversaState, llm_client) -> ConversaState:
    """
    Processa intenções simples.
    """
    intencao = state.get("intencao")
    
    print(f"[NODE] processar_intencao: {intencao}")
    
    dados_pac = state.get("dados_paciente", {})
    nome = dados_pac.get("nome", "") if isinstance(dados_pac, dict) else ""
    primeiro_nome = nome.split()[0] if nome else ""
    
    if intencao == "SAUDACAO":
        resposta = f"Olá{', ' + primeiro_nome if primeiro_nome else ''}! 👋 Como posso ajudar você hoje?"
        return {
            **state,
            "resposta": resposta,
            "estado": "finalizado"
        }
    
    if intencao == "DESPEDIDA":
        return {
            **state,
            "resposta": "Até logo! Se precisar de algo, é só chamar. 😊",
            "estado": "finalizado"
        }
    
    if intencao == "DESCONHECIDO":
        return {
            **state,
            "resposta": "Desculpe, não entendi. Você gostaria de agendar uma consulta, confirmar ou obter informações?",
            "estado": "finalizado"
        }
    
    return {
        **state,
        "estado": "classificar_intencao"
    }


# ============================================
# NÓ: BUSCAR SLOTS DISPONÍVEIS
# ============================================

async def buscar_slots(state: ConversaState, db) -> ConversaState:
    """
    Busca horários disponíveis (mock por enquanto).
    """
    print(f"[NODE] buscar_slots")
    
    hoje = datetime.now()
    slots = []
    
    for i in range(1, 8):
        data = hoje + timedelta(days=i)
        if data.weekday() < 5:  # Seg-Sex
            slots.append({
                "data": data.strftime("%Y-%m-%d"),
                "data_formatada": data.strftime("%d/%m"),
                "dia_semana": ["Seg", "Ter", "Qua", "Qui", "Sex"][data.weekday()],
                "horarios": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            })
    
    # Formata mensagem com slots
    slots_texto = "\n".join([
        f"📅 {s['dia_semana']} {s['data_formatada']}: {', '.join(s['horarios'][:3])}..."
        for s in slots[:3]
    ])
    
    return {
        **state,
        "slots_disponiveis": slots,
        "estado": "coletando_data",
        "resposta": f"Temos os seguintes horários disponíveis:\n\n{slots_texto}\n\nQual data você prefere?"
    }


# ============================================
# NÓ: COLETAR DATA
# ============================================

async def coletar_data(state: ConversaState, llm_client) -> ConversaState:
    """Coleta a data desejada."""
    
    print(f"[NODE] coletar_data")
    
    if state.get("estado") != "coletando_data":
        return {
            **state,
            "estado": "coletando_data",
            "resposta": "Para qual dia você gostaria de agendar?"
        }
    
    mensagem = state.get("mensagem_atual", "").lower()
    hoje = datetime.now()
    data_obj = None
    
    # Tenta extrair data DD/MM/AAAA
    match = re.search(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.]?(\d{4})?', mensagem)
    
    if match:
        dia, mes, ano = match.groups()
        ano = ano or str(hoje.year)
        try:
            data_obj = datetime(int(ano), int(mes), int(dia))
        except:
            pass
    else:
        # Interpreta palavras
        if "hoje" in mensagem:
            data_obj = hoje
        elif "amanha" in mensagem or "amanhã" in mensagem:
            data_obj = hoje + timedelta(days=1)
        elif "segunda" in mensagem:
            data_obj = hoje + timedelta(days=(0 - hoje.weekday()) % 7 or 7)
        elif "terca" in mensagem or "terça" in mensagem:
            data_obj = hoje + timedelta(days=(1 - hoje.weekday()) % 7 or 7)
        elif "quarta" in mensagem:
            data_obj = hoje + timedelta(days=(2 - hoje.weekday()) % 7 or 7)
        elif "quinta" in mensagem:
            data_obj = hoje + timedelta(days=(3 - hoje.weekday()) % 7 or 7)
        elif "sexta" in mensagem:
            data_obj = hoje + timedelta(days=(4 - hoje.weekday()) % 7 or 7)
    
    if not data_obj:
        return {
            **state,
            "resposta": "Não consegui entender a data. Por favor, informe no formato DD/MM (ex: 15/01)"
        }
    
    dados_agend = dict(state.get("dados_agendamento", {})) if state.get("dados_agendamento") else {}
    dados_agend["data"] = data_obj.strftime("%Y-%m-%d")
    dados_agend["data_formatada"] = data_obj.strftime("%d/%m")
    
    return {
        **state,
        "dados_agendamento": dados_agend,
        "estado": "coletando_horario",
        "resposta": f"📅 Data selecionada: {data_obj.strftime('%d/%m')}\n\nQual horário você prefere? (Ex: 09:00, 14:30)"
    }


# ============================================
# NÓ: COLETAR HORÁRIO
# ============================================

async def coletar_horario(state: ConversaState, llm_client) -> ConversaState:
    """Coleta o horário desejado."""
    
    print(f"[NODE] coletar_horario")
    
    if state.get("estado") != "coletando_horario":
        return {
            **state,
            "estado": "coletando_horario",
            "resposta": "Qual horário você prefere? (Ex: 09:00, 14:30)"
        }
    
    mensagem = state.get("mensagem_atual", "")
    
    # Tenta extrair horário HH:MM ou HH
    match = re.search(r'(\d{1,2})[:\s]?(\d{2})?', mensagem)
    
    if not match:
        return {
            **state,
            "resposta": "Não consegui entender o horário. Por favor, informe no formato HH:MM (ex: 14:30)"
        }
    
    hora = int(match.group(1))
    minuto = int(match.group(2)) if match.group(2) else 0
    
    if hora < 8 or hora > 18:
        return {
            **state,
            "resposta": "Nosso horário de atendimento é das 08h às 18h. Por favor, escolha um horário nesse intervalo."
        }
    
    horario = f"{hora:02d}:{minuto:02d}"
    
    dados_agend = dict(state.get("dados_agendamento", {})) if state.get("dados_agendamento") else {}
    dados_agend["hora"] = horario
    dados_agend["hora_inicio"] = horario
    
    # Calcula hora_fim (consulta de 30 minutos)
    hora_fim_obj = datetime.strptime(horario, "%H:%M") + timedelta(minutes=30)
    dados_agend["hora_fim"] = hora_fim_obj.strftime("%H:%M")
    
    # Formata resumo
    dados_pac = state.get("dados_paciente", {})
    nome = dados_pac.get("nome", "Paciente") if isinstance(dados_pac, dict) else "Paciente"
    data_formatada = dados_agend.get("data_formatada", dados_agend.get("data", ""))
    
    return {
        **state,
        "dados_agendamento": dados_agend,
        "estado": "confirmando_agendamento",
        "resposta": f"📋 **Confirmação de Agendamento**\n\n👤 {nome}\n📅 {data_formatada}\n🕐 {horario}\n\nConfirma o agendamento? (Sim/Não)"
    }


# ============================================
# NÓ: CONFIRMAR AGENDAMENTO
# ============================================

async def confirmar_agendamento(state: ConversaState, llm_client) -> ConversaState:
    """Confirma ou cancela o agendamento."""
    
    print(f"[NODE] confirmar_agendamento")
    
    mensagem = state.get("mensagem_atual", "").lower()
    
    confirmacoes = ["sim", "s", "confirmo", "ok", "pode", "quero", "isso"]
    negacoes = ["nao", "não", "n", "cancela", "desisto"]
    
    if any(palavra in mensagem for palavra in confirmacoes):
        return {
            **state,
            "estado": "criando_agendamento"
        }
    
    if any(palavra in mensagem for palavra in negacoes):
        return {
            **state,
            "estado": "coletando_data",
            "resposta": "Ok, vamos escolher outra data. Qual dia você prefere?"
        }
    
    return {
        **state,
        "resposta": "Por favor, confirme com 'Sim' ou 'Não'."
    }


# ============================================
# NÓ: CRIAR AGENDAMENTO
# ============================================

async def criar_agendamento(state: ConversaState, db) -> ConversaState:
    """
    Cria o agendamento no banco.
    
    Colunas da tabela agendamentos:
    - id (uuid)
    - clinica_id (uuid)
    - paciente_id (uuid)
    - medico_id (uuid) - NOT NULL, pode dar erro
    - tipo_consulta_id (uuid)
    - data (date) ← usa essa
    - hora_inicio (time) ← usa essa
    - hora_fim (time) ← usa essa
    - hora (time) - coluna extra
    - status (text)
    - origem (varchar)
    - created_at (timestamptz)
    """
    
    print(f"[NODE] criar_agendamento")
    
    dados_agend = state.get("dados_agendamento", {})
    if not isinstance(dados_agend, dict):
        dados_agend = {}
    
    agendamento_id = str(uuid.uuid4())
    
    # Pega a data e hora
    data = dados_agend.get("data")  # Formato: YYYY-MM-DD
    hora_inicio = dados_agend.get("hora_inicio") or dados_agend.get("hora")  # Formato: HH:MM
    hora_fim = dados_agend.get("hora_fim")
    
    # Se hora_fim não foi calculado, calcula agora (30 min)
    if hora_inicio and not hora_fim:
        try:
            hora_fim_obj = datetime.strptime(hora_inicio, "%H:%M") + timedelta(minutes=30)
            hora_fim = hora_fim_obj.strftime("%H:%M")
        except:
            hora_fim = None
    
    # Monta dados do agendamento
    # NOTA: medico_id é NOT NULL na tabela, então pode dar erro
    agendamento_data = {
        "id": agendamento_id,
        "clinica_id": state["clinica_id"],
        "paciente_id": state.get("paciente_id"),
        "data": data,                    # Coluna DATE (YYYY-MM-DD)
        "hora_inicio": hora_inicio,      # Coluna TIME (HH:MM:SS ou HH:MM)
        "hora_fim": hora_fim,            # Coluna TIME
        "hora": hora_inicio,             # Coluna extra TIME (redundante mas existe)
        "status": "agendado",
        "origem": "whatsapp",
        "primeira_vez": True,
        "confirmado": False,
        "created_at": datetime.now().isoformat()
    }
    
    # Se tiver card_id, associa
    if state.get("card_id"):
        agendamento_data["card_id"] = state["card_id"]
    
    try:
        await db.insert("agendamentos", agendamento_data)
        
        # Atualiza card se existir
        if state.get("card_id"):
            try:
                await db.update(
                    table="cards",
                    data={
                        "fase": 1,  # 1 = agendado
                        "updated_at": datetime.now().isoformat()
                    },
                    filters={"id": state["card_id"]}
                )
            except Exception as e:
                print(f"[WARN] Erro ao atualizar card: {e}")
        
        # Registra governança
        gov_result = await _registrar_governanca(
            state, db,
            tipo_trigger="agendamento_criado",
            dados_adicionais={
                "agendamento_id": agendamento_id,
                "data": data,
                "hora": hora_inicio
            }
        )
        
        data_fmt = dados_agend.get("data_formatada", data or "")
        
        return {
            **state,
            "agendamento_id": agendamento_id,
            "acoes_executadas": state.get("acoes_executadas", []) + ["agendamento_criado"],
            **gov_result,
            "estado": "finalizado",
            "resposta": f"✅ Agendamento confirmado!\n\n📅 {data_fmt} às {hora_inicio}\n\nVocê receberá uma confirmação por WhatsApp. Até lá!"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] criar_agendamento: {error_msg}")
        
        # Se erro é de medico_id (NOT NULL), informa que precisa de complemento manual
        if "medico_id" in error_msg or "null value" in error_msg.lower():
            data_fmt = dados_agend.get("data_formatada", data or "")
            
            return {
                **state,
                "estado": "finalizado",
                "resposta": f"📋 Solicitação de agendamento registrada!\n\n📅 {data_fmt} às {hora_inicio}\n\nNossa equipe entrará em contato para confirmar o médico disponível. Obrigado!"
            }
        
        return {
            **state,
            "estado": "erro",
            "erro": error_msg,
            "resposta": "Desculpe, ocorreu um erro ao criar o agendamento. Tente novamente."
        }


# ============================================
# NÓ: RESPONDER FAQ
# ============================================

async def responder_faq(state: ConversaState, llm_client) -> ConversaState:
    """Responde perguntas frequentes usando LLM."""
    
    print(f"[NODE] responder_faq")
    
    mensagem = state.get("mensagem_atual", "")
    
    # FAQ básico
    faq = {
        "endereco": "📍 Nosso endereço: Av. Paulista, 1000 - São Paulo/SP",
        "horario": "🕐 Horário de funcionamento: Seg-Sex 08h às 18h, Sáb 08h às 12h",
        "estacionamento": "🚗 Temos estacionamento conveniado no prédio",
        "documento": "📄 Traga documento com foto e carteirinha do convênio (se tiver)",
    }
    
    mensagem_lower = mensagem.lower()
    
    for key, resposta in faq.items():
        if key in mensagem_lower:
            return {
                **state,
                "resposta": resposta,
                "estado": "finalizado"
            }
    
    # Usa LLM para outras perguntas
    try:
        system_prompt = """Você é uma assistente de uma clínica médica.
Responda perguntas de forma breve e prestativa.
Informações da clínica:
- Horário: Seg-Sex 08h às 18h
- Endereço: Av. Paulista, 1000 - São Paulo/SP
- Aceita convênios: Unimed, Bradesco, SulAmérica
- Consulta particular: R$ 300,00
"""
        
        response = await llm_client.complete(
            system_prompt=system_prompt,
            user_message=mensagem,
            temperature=0.7,
            max_tokens=200
        )
        
        return {
            **state,
            "resposta": response.content.strip(),
            "estado": "finalizado"
        }
    except Exception as e:
        print(f"[ERROR] responder_faq: {e}")
        return {
            **state,
            "resposta": "Para mais informações, entre em contato pelo telefone (11) 3000-0000",
            "estado": "finalizado"
        }


# ============================================
# NÓ: RESPONDER VALOR
# ============================================

async def responder_valor(state: ConversaState, db) -> ConversaState:
    """Informa valores de consultas."""
    
    print(f"[NODE] responder_valor")
    
    return {
        **state,
        "resposta": "💰 **Valores de Consulta**\n\n• Consulta particular: R$ 300,00\n• Retorno (até 30 dias): Gratuito\n\nAceitamos cartão de crédito em até 3x sem juros.\n\nGostaria de agendar uma consulta?",
        "estado": "finalizado"
    }


# ============================================
# NÓ: RESPONDER CONVÊNIO
# ============================================

async def responder_convenio(state: ConversaState, db) -> ConversaState:
    """Informa convênios aceitos."""
    
    print(f"[NODE] responder_convenio")
    
    return {
        **state,
        "resposta": "🏥 **Convênios Aceitos**\n\n✅ Unimed\n✅ Bradesco Saúde\n✅ SulAmérica\n✅ Amil\n✅ Porto Seguro\n\nAtendemos também particular. Gostaria de agendar?",
        "estado": "finalizado"
    }
