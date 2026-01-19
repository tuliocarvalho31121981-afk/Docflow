# app/chat_langgraph/nodes.py
"""
Nós do grafo LangGraph - FASE 0: PRÉ-AGENDAMENTO
Fluxo NATURAL - Responde primeiro, captura lead de forma silenciosa

PRINCÍPIOS:
1. Verificar cadastro é SILENCIOSO (não pergunta nada)
2. Classificar intenção PRIMEIRO (entender o que quer)
3. Responder a dúvida + pedir dado mínimo (nome) na mesma mensagem
4. Extrair dados DURANTE a conversa (CPF, convênio vão aparecendo)
5. Card é criado com telefone + nome + intenção (mínimo pra lead)

FLUXO:
Mensagem → Verifica Cadastro (silencioso) → Classifica Intenção → 
Responde + Captura Lead → Extrai dados nas próximas mensagens
"""

from typing import Optional
from datetime import datetime, timedelta
import re
import uuid
import json

from .states import ConversaState, DadosPaciente


# ============================================
# HELPERS
# ============================================

async def _registrar_governanca(state: ConversaState, db, tipo_trigger: str, dados_adicionais: dict = None) -> dict:
    """Registra ação na governança."""
    try:
        validacao_id = str(uuid.uuid4())
        await db.insert("validacoes_governanca", {
            "id": validacao_id,
            "clinica_id": state["clinica_id"],
            "tipo": tipo_trigger,
            "status": "pendente",
            "dados": {
                "telefone": state["telefone"],
                "mensagem": state.get("mensagem_atual", ""),
                "intencao": state.get("intencao"),
                "paciente_id": state.get("paciente_id"),
                "card_id": state.get("card_id"),
                **(dados_adicionais or {})
            },
            "created_at": datetime.now().isoformat()
        })
        return {"validacao_pendente": True, "validacao_id": validacao_id}
    except Exception as e:
        print(f"[WARN] Governança: {e}")
        return {"validacao_pendente": False, "validacao_id": None}


def _formatar_telefone(telefone: str) -> str:
    """Formata telefone: (11) 99999-9999"""
    telefone = re.sub(r'\D', '', telefone)
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    return telefone


def _extrair_nome(mensagem: str) -> Optional[str]:
    """Tenta extrair nome de uma mensagem."""
    # Remove saudações comuns
    msg = re.sub(r'^(oi|olá|ola|bom dia|boa tarde|boa noite|hey|hello)[,!\s]*', '', mensagem.lower(), flags=re.IGNORECASE)
    msg = re.sub(r'(obrigad[oa]|valeu|vlw|brigad[oa])[,!\s]*$', '', msg, flags=re.IGNORECASE)
    
    # Se sobrou algo que parece nome (2+ palavras, só letras)
    msg = msg.strip().title()
    palavras = msg.split()
    
    # Filtra palavras que não são nome
    palavras_invalidas = ['eu', 'sou', 'meu', 'nome', 'é', 'e', 'sim', 'não', 'nao', 'ok', 'quero', 'gostaria', 'preciso']
    palavras = [p for p in palavras if p.lower() not in palavras_invalidas and len(p) > 1]
    
    if len(palavras) >= 2:
        nome = ' '.join(palavras[:4])  # Máximo 4 palavras
        # Verifica se parece nome (só letras)
        if re.match(r'^[A-Za-zÀ-ÿ\s]+$', nome):
            return nome
    
    return None


def _extrair_cpf(mensagem: str) -> Optional[str]:
    """Tenta extrair CPF de uma mensagem."""
    numeros = re.sub(r'\D', '', mensagem)
    if len(numeros) == 11:
        return numeros
    return None


def _extrair_convenio(mensagem: str) -> Optional[str]:
    """Tenta extrair convênio de uma mensagem."""
    convenios_conhecidos = [
        'unimed', 'bradesco', 'sulamerica', 'sul america', 'amil', 
        'porto seguro', 'notredame', 'notre dame', 'hapvida', 
        'prevent senior', 'omint', 'golden cross', 'medial',
        'particular', 'nenhum', 'não tenho', 'nao tenho'
    ]
    
    msg_lower = mensagem.lower()
    
    for convenio in convenios_conhecidos:
        if convenio in msg_lower:
            if convenio in ['particular', 'nenhum', 'não tenho', 'nao tenho']:
                return 'Particular'
            return convenio.title()
    
    return None


# ============================================
# NÓ 1: VERIFICAR CADASTRO (SILENCIOSO)
# ============================================

async def verificar_cadastro(state: ConversaState, db) -> ConversaState:
    """
    Verifica se paciente existe - NÃO RESPONDE NADA.
    Apenas carrega os dados para usar depois.
    """
    telefone = state["telefone"]
    clinica_id = state["clinica_id"]
    
    print(f"[NODE] verificar_cadastro (silencioso): {telefone[:4]}***")
    
    try:
        paciente = await db.select_one(
            table="pacientes",
            filters={"clinica_id": clinica_id, "telefone": telefone}
        )
        
        if paciente:
            # Calcula tempo desde última atualização
            meses_desde_atualizacao = 0
            updated_at = paciente.get("updated_at")
            if updated_at:
                try:
                    last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    meses_desde_atualizacao = (datetime.now(last_update.tzinfo) - last_update).days // 30
                except:
                    pass
            
            # Verifica campos obrigatórios
            campos_obrigatorios = ["nome", "cpf", "data_nascimento"]
            cadastro_completo = all(paciente.get(campo) for campo in campos_obrigatorios)
            
            print(f"[NODE] Paciente encontrado: {paciente.get('nome')} (completo={cadastro_completo})")
            
            return {
                **state,
                "paciente_id": paciente["id"],
                "paciente_existe": True,
                "cadastro_completo": cadastro_completo,
                "meses_desde_atualizacao": meses_desde_atualizacao,
                "dados_paciente": {
                    "nome": paciente.get("nome"),
                    "cpf": paciente.get("cpf"),
                    "data_nascimento": paciente.get("data_nascimento"),
                    "telefone": telefone,
                    "email": paciente.get("email"),
                    "convenio_id": paciente.get("convenio_id"),
                    "convenio_nome": paciente.get("convenio_nome") or "Particular",
                },
                "estado": "classificar_intencao"
                # NÃO tem "resposta" - é silencioso
            }
    
    except Exception as e:
        print(f"[WARN] Erro ao buscar paciente: {e}")
    
    # Não encontrou - continua silencioso
    print(f"[NODE] Paciente não encontrado - continua silencioso")
    
    return {
        **state,
        "paciente_existe": False,
        "cadastro_completo": False,
        "dados_paciente": {"telefone": telefone},
        "estado": "classificar_intencao"
        # NÃO tem "resposta" - é silencioso
    }


# ============================================
# NÓ 2: CLASSIFICAR INTENÇÃO
# ============================================

async def classificar_intencao(state: ConversaState, llm_client) -> ConversaState:
    """
    Classifica a intenção do paciente.
    Também tenta extrair dados da mensagem (nome, CPF, convênio).
    """
    mensagem = state.get("mensagem_atual", "")
    
    print(f"[NODE] classificar_intencao: '{mensagem[:50]}...'")
    
    # === EXTRAÇÃO SILENCIOSA DE DADOS ===
    dados_paciente = dict(state.get("dados_paciente", {})) or {}
    dados_extraidos = {}
    
    # Tenta extrair nome se não tem
    if not dados_paciente.get("nome"):
        nome_extraido = _extrair_nome(mensagem)
        if nome_extraido:
            dados_extraidos["nome"] = nome_extraido
            print(f"[NODE] Nome extraído: {nome_extraido}")
    
    # Tenta extrair CPF se não tem
    if not dados_paciente.get("cpf"):
        cpf_extraido = _extrair_cpf(mensagem)
        if cpf_extraido:
            dados_extraidos["cpf"] = cpf_extraido
            print(f"[NODE] CPF extraído: {cpf_extraido[:3]}***")
    
    # Tenta extrair convênio se não tem
    if not dados_paciente.get("convenio_nome") or dados_paciente.get("convenio_nome") == "Particular":
        convenio_extraido = _extrair_convenio(mensagem)
        if convenio_extraido:
            dados_extraidos["convenio_nome"] = convenio_extraido
            print(f"[NODE] Convênio extraído: {convenio_extraido}")
    
    # Atualiza dados do paciente
    dados_paciente.update(dados_extraidos)
    
    # === CLASSIFICAÇÃO COM LLM ===
    system_prompt = """Você é um classificador de intenções para uma clínica médica.
Analise a mensagem e retorne APENAS a intenção em uma palavra.

INTENÇÕES POSSÍVEIS:
- AGENDAR: Quer marcar consulta, atendimento, horário
- REMARCAR: Quer mudar data/hora de consulta existente
- CANCELAR: Quer cancelar consulta
- CONFIRMAR: Confirma presença em consulta
- VALOR: Pergunta preço, quanto custa, valor
- CONVENIO: Pergunta se aceita plano, convênio, qual plano
- FAQ: Dúvida geral (endereço, horário funcionamento, estacionamento, etc)
- EXAMES: Quer enviar exames, resultados
- SAUDACAO: Só cumprimento (oi, olá, bom dia) sem pedir nada específico
- DESPEDIDA: Tchau, obrigado, até logo
- RETORNO: Pergunta sobre retorno de consulta
- DESCONHECIDO: Não conseguiu identificar

Retorne APENAS uma palavra."""

    try:
        response = await llm_client.complete(
            system_prompt=system_prompt,
            user_message=f"Mensagem: {mensagem}",
            temperature=0.1,
            max_tokens=20
        )
        
        intencao = response.content.strip().upper()
        
        intencoes_validas = [
            "AGENDAR", "REMARCAR", "CANCELAR", "CONFIRMAR",
            "VALOR", "CONVENIO", "FAQ", "EXAMES", "SAUDACAO", 
            "DESPEDIDA", "RETORNO", "DESCONHECIDO"
        ]
        
        if intencao not in intencoes_validas:
            intencao = "DESCONHECIDO"
        
        print(f"[NODE] Intenção: {intencao}")
        
        return {
            **state,
            "intencao": intencao,
            "confianca_intencao": 0.85,
            "dados_paciente": dados_paciente,
            "dados_extraidos_agora": dados_extraidos,
            "estado": "gerar_resposta"
        }
        
    except Exception as e:
        print(f"[ERROR] Classificação: {e}")
        return {
            **state,
            "intencao": "DESCONHECIDO",
            "confianca_intencao": 0.0,
            "dados_paciente": dados_paciente,
            "estado": "gerar_resposta"
        }


# ============================================
# NÓ 3: GERAR RESPOSTA CONTEXTUAL
# ============================================

async def gerar_resposta(state: ConversaState, llm_client) -> ConversaState:
    """
    Gera resposta baseada na intenção + situação do cadastro.
    
    REGRA: Sempre responde a dúvida + pede dado faltante de forma natural.
    """
    intencao = state.get("intencao", "DESCONHECIDO")
    paciente_existe = state.get("paciente_existe", False)
    cadastro_completo = state.get("cadastro_completo", False)
    dados = state.get("dados_paciente", {}) or {}
    nome = dados.get("nome", "")
    primeiro_nome = nome.split()[0] if nome else ""
    
    print(f"[NODE] gerar_resposta: {intencao} (existe={paciente_existe}, completo={cadastro_completo})")
    
    # === MONTA RESPOSTA BASE POR INTENÇÃO ===
    
    respostas_base = {
        "SAUDACAO": "Olá! 👋 Seja bem-vindo(a)! Como posso ajudar você hoje?",
        
        "VALOR": """💰 **Valores de Consulta**

• Consulta particular: R$ 300,00
• Retorno (até 30 dias): Gratuito

Aceitamos cartão em até 3x sem juros.
Também atendemos diversos convênios!

Quer agendar sua consulta?""",
        
        "CONVENIO": """🏥 **Convênios Aceitos**

✅ Unimed
✅ Bradesco Saúde
✅ SulAmérica
✅ Amil
✅ Porto Seguro
✅ NotreDame
✅ Hapvida

Também atendemos particular.

Qual é o seu convênio?""",
        
        "FAQ": "Como posso ajudar você?",
        
        "AGENDAR": """Ótimo! Vou te ajudar a agendar sua consulta! 📅

Temos horários disponíveis essa semana.""",
        
        "REMARCAR": "Claro! Vou te ajudar a remarcar sua consulta.",
        
        "CANCELAR": "Entendi. Posso saber o motivo do cancelamento? Assim podemos melhorar nosso atendimento.",
        
        "CONFIRMAR": "✅ Presença confirmada! Te esperamos no dia da consulta.",
        
        "EXAMES": "Pode enviar os exames aqui mesmo! 📎 Aceito foto ou PDF.",
        
        "DESPEDIDA": "Até logo! 👋 Qualquer coisa é só chamar. Tenha um ótimo dia!",
        
        "RETORNO": """Retornos são gratuitos em até 30 dias após a consulta.

Quer agendar um horário de retorno?""",
        
        "DESCONHECIDO": "Como posso ajudar você hoje? Quer agendar uma consulta ou tirar alguma dúvida?"
    }
    
    resposta = respostas_base.get(intencao, respostas_base["DESCONHECIDO"])
    
    # === PERSONALIZA COM NOME SE TIVER ===
    
    if primeiro_nome:
        # Substitui início genérico por personalizado
        if resposta.startswith("Olá!"):
            resposta = resposta.replace("Olá!", f"Olá, {primeiro_nome}!", 1)
        elif resposta.startswith("Ótimo!"):
            resposta = resposta.replace("Ótimo!", f"Ótimo, {primeiro_nome}!", 1)
        elif resposta.startswith("Claro!"):
            resposta = resposta.replace("Claro!", f"Claro, {primeiro_nome}!", 1)
        elif not any(resposta.startswith(x) for x in ["💰", "🏥", "✅"]):
            resposta = f"{primeiro_nome}, {resposta[0].lower()}{resposta[1:]}"
    
    # === ADICIONA PEDIDO DE DADO FALTANTE ===
    
    complemento = ""
    proximo_estado = "verificar_card"
    
    if not paciente_existe or not nome:
        # Não tem nome - pede de forma natural
        if intencao == "SAUDACAO":
            complemento = "\n\nQual é o seu nome?"
        elif intencao in ["VALOR", "CONVENIO", "FAQ", "RETORNO"]:
            complemento = "\n\nA propósito, qual é o seu nome? 😊"
        elif intencao == "AGENDAR":
            complemento = "\n\nPra eu reservar seu horário, qual é o seu nome completo?"
            proximo_estado = "aguardar_nome"
        elif intencao not in ["DESPEDIDA"]:
            complemento = "\n\nQual é o seu nome?"
        
    elif paciente_existe and not cadastro_completo:
        # Tem nome mas falta algo - confirma nome e pede o que falta
        if not dados.get("cpf"):
            if intencao == "AGENDAR":
                complemento = f"\n\n{primeiro_nome}, pra confirmar o agendamento, preciso do seu CPF."
                proximo_estado = "aguardar_cpf"
    
    # Não pede nada na despedida
    if intencao == "DESPEDIDA":
        complemento = ""
        proximo_estado = "finalizar"
    
    resposta_final = resposta + complemento
    
    return {
        **state,
        "resposta": resposta_final,
        "estado": proximo_estado
    }


# ============================================
# NÓ 4: AGUARDAR NOME
# ============================================

async def aguardar_nome(state: ConversaState, db) -> ConversaState:
    """
    Processa resposta esperando nome.
    Extrai nome e decide próximo passo.
    """
    mensagem = state.get("mensagem_atual", "").strip()
    dados_paciente = dict(state.get("dados_paciente", {})) or {}
    
    print(f"[NODE] aguardar_nome: '{mensagem}'")
    
    # Tenta extrair nome
    nome = _extrair_nome(mensagem)
    
    if not nome:
        # Mensagem pode ser o nome direto
        nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', mensagem).strip().title()
        if len(nome_limpo.split()) >= 2:
            nome = nome_limpo
    
    if not nome:
        return {
            **state,
            "resposta": "Desculpe, não entendi. Pode me dizer seu **nome completo**? (nome e sobrenome)"
        }
    
    dados_paciente["nome"] = nome
    primeiro_nome = nome.split()[0]
    
    # Verifica se precisa criar paciente
    paciente_id = state.get("paciente_id")
    
    if not paciente_id:
        # Cria paciente mínimo (telefone + nome)
        paciente_id = str(uuid.uuid4())
        try:
            await db.insert("pacientes", {
                "id": paciente_id,
                "clinica_id": state["clinica_id"],
                "nome": nome,
                "telefone": state["telefone"],
                "como_conheceu": "whatsapp",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            print(f"[NODE] Paciente criado: {paciente_id[:8]}...")
        except Exception as e:
            print(f"[WARN] Erro ao criar paciente: {e}")
    else:
        # Atualiza nome se não tinha
        try:
            await db.update(
                table="pacientes",
                data={"nome": nome, "updated_at": datetime.now().isoformat()},
                filters={"id": paciente_id}
            )
        except Exception as e:
            print(f"[WARN] Erro ao atualizar nome: {e}")
    
    # Decide próximo passo baseado na intenção original
    intencao = state.get("intencao", "DESCONHECIDO")
    
    if intencao == "AGENDAR":
        resposta = f"Prazer, {primeiro_nome}! 😊\n\nPra confirmar o agendamento, preciso do seu **CPF**."
        proximo_estado = "aguardar_cpf"
    else:
        resposta = f"Prazer, {primeiro_nome}! 😊\n\nComo posso te ajudar?"
        proximo_estado = "verificar_card"
    
    return {
        **state,
        "paciente_id": paciente_id,
        "paciente_existe": True,
        "dados_paciente": dados_paciente,
        "resposta": resposta,
        "estado": proximo_estado
    }


# ============================================
# NÓ 5: AGUARDAR CPF
# ============================================

async def aguardar_cpf(state: ConversaState, db) -> ConversaState:
    """
    Processa resposta esperando CPF.
    """
    mensagem = state.get("mensagem_atual", "")
    dados_paciente = dict(state.get("dados_paciente", {})) or {}
    paciente_id = state.get("paciente_id")
    
    print(f"[NODE] aguardar_cpf")
    
    cpf = _extrair_cpf(mensagem)
    
    if not cpf:
        return {
            **state,
            "resposta": "CPF inválido. Por favor, me envie os **11 dígitos** do seu CPF."
        }
    
    dados_paciente["cpf"] = cpf
    
    # Atualiza no banco
    if paciente_id:
        try:
            await db.update(
                table="pacientes",
                data={"cpf": cpf, "updated_at": datetime.now().isoformat()},
                filters={"id": paciente_id}
            )
        except Exception as e:
            print(f"[WARN] Erro ao atualizar CPF: {e}")
    
    primeiro_nome = dados_paciente.get("nome", "").split()[0] if dados_paciente.get("nome") else ""
    
    # Verifica se precisa de data de nascimento
    if not dados_paciente.get("data_nascimento"):
        return {
            **state,
            "dados_paciente": dados_paciente,
            "resposta": f"Perfeito! 👍 Qual sua **data de nascimento**? (DD/MM/AAAA)",
            "estado": "aguardar_nascimento"
        }
    
    # Cadastro completo - segue pro agendamento
    return {
        **state,
        "dados_paciente": dados_paciente,
        "cadastro_completo": True,
        "estado": "verificar_card"
    }


# ============================================
# NÓ 6: AGUARDAR NASCIMENTO
# ============================================

async def aguardar_nascimento(state: ConversaState, db) -> ConversaState:
    """
    Processa resposta esperando data de nascimento.
    """
    mensagem = state.get("mensagem_atual", "")
    dados_paciente = dict(state.get("dados_paciente", {})) or {}
    paciente_id = state.get("paciente_id")
    
    print(f"[NODE] aguardar_nascimento")
    
    # Extrai data
    match = re.search(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})', mensagem)
    
    if not match:
        return {
            **state,
            "resposta": "Não entendi a data. Use o formato **DD/MM/AAAA** (ex: 15/03/1990)"
        }
    
    dia, mes, ano = match.groups()
    
    try:
        data_nasc = datetime(int(ano), int(mes), int(dia))
        idade = (datetime.now() - data_nasc).days // 365
        if idade < 0 or idade > 120:
            raise ValueError("Idade inválida")
        
        data_formatada = data_nasc.strftime("%Y-%m-%d")
        dados_paciente["data_nascimento"] = data_formatada
        
    except:
        return {
            **state,
            "resposta": "Data inválida. Use o formato **DD/MM/AAAA** (ex: 15/03/1990)"
        }
    
    # Atualiza no banco
    if paciente_id:
        try:
            await db.update(
                table="pacientes",
                data={"data_nascimento": data_formatada, "updated_at": datetime.now().isoformat()},
                filters={"id": paciente_id}
            )
        except Exception as e:
            print(f"[WARN] Erro ao atualizar nascimento: {e}")
    
    primeiro_nome = dados_paciente.get("nome", "").split()[0] if dados_paciente.get("nome") else ""
    
    # Verifica se precisa de convênio
    if not dados_paciente.get("convenio_nome"):
        return {
            **state,
            "dados_paciente": dados_paciente,
            "resposta": f"Ótimo! 👍 Você tem **plano de saúde**?\n\nSe sim, qual? Se não, digite **PARTICULAR**.",
            "estado": "aguardar_convenio"
        }
    
    # Cadastro completo
    return {
        **state,
        "dados_paciente": dados_paciente,
        "cadastro_completo": True,
        "resposta": f"Perfeito, {primeiro_nome}! Cadastro completo! ✅",
        "estado": "verificar_card"
    }


# ============================================
# NÓ 7: AGUARDAR CONVÊNIO
# ============================================

async def aguardar_convenio(state: ConversaState, db) -> ConversaState:
    """
    Processa resposta esperando convênio.
    """
    mensagem = state.get("mensagem_atual", "").strip()
    dados_paciente = dict(state.get("dados_paciente", {})) or {}
    paciente_id = state.get("paciente_id")
    
    print(f"[NODE] aguardar_convenio: '{mensagem}'")
    
    # Detecta convênio
    convenio = _extrair_convenio(mensagem)
    
    if not convenio:
        # Assume o que digitou como convênio
        if mensagem.lower() in ["não", "nao", "n", "sem", "nenhum"]:
            convenio = "Particular"
        else:
            convenio = mensagem.title()
    
    dados_paciente["convenio_nome"] = convenio
    
    # Atualiza no banco
    if paciente_id:
        try:
            await db.update(
                table="pacientes",
                data={"convenio_nome": convenio, "updated_at": datetime.now().isoformat()},
                filters={"id": paciente_id}
            )
        except Exception as e:
            print(f"[WARN] Erro ao atualizar convênio: {e}")
    
    primeiro_nome = dados_paciente.get("nome", "").split()[0] if dados_paciente.get("nome") else ""
    
    return {
        **state,
        "dados_paciente": dados_paciente,
        "cadastro_completo": True,
        "resposta": f"Perfeito, {primeiro_nome}! Cadastro completo! ✅",
        "estado": "verificar_card"
    }


# ============================================
# NÓ: VERIFICAR CARD
# ============================================

async def verificar_card(state: ConversaState, db) -> ConversaState:
    """
    Verifica se paciente tem card ativo.
    Se não tem, cria um novo.
    """
    paciente_id = state.get("paciente_id")
    clinica_id = state["clinica_id"]
    
    print(f"[NODE] verificar_card: {paciente_id[:8] if paciente_id else 'None'}...")
    
    if not paciente_id:
        return {
            **state,
            "tem_card_ativo": False,
            "estado": "criar_card"
        }
    
    try:
        cards = await db.select(
            table="cards",
            filters={"clinica_id": clinica_id, "paciente_id": paciente_id},
            order_by="created_at",
            order_asc=False,
            limit=1
        )
        
        fases_ativas = [0, 1, 2, 3, "lead", "agendado", "confirmado", "em_atendimento"]
        
        for card in cards:
            if card.get("fase") in fases_ativas:
                print(f"[NODE] Card encontrado: fase={card['fase']}")
                return {
                    **state,
                    "tem_card_ativo": True,
                    "card_id": card["id"],
                    "card_fase": card["fase"],
                    "estado": "finalizar"
                }
    
    except Exception as e:
        print(f"[WARN] Erro ao buscar card: {e}")
    
    return {
        **state,
        "tem_card_ativo": False,
        "estado": "criar_card"
    }


# ============================================
# NÓ: CRIAR CARD
# ============================================

async def criar_card(state: ConversaState, db) -> ConversaState:
    """
    Cria card LEAD no Kanban.
    """
    clinica_id = state["clinica_id"]
    paciente_id = state.get("paciente_id")
    intencao = state.get("intencao", "DESCONHECIDO")
    
    print(f"[NODE] criar_card: intencao={intencao}")
    
    card_id = str(uuid.uuid4())
    
    try:
        await db.insert("cards", {
            "id": card_id,
            "clinica_id": clinica_id,
            "paciente_id": paciente_id,
            "fase": 0,  # Lead
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        print(f"[NODE] Card criado: {card_id[:8]}...")
        
        await _registrar_governanca(
            state, db, "card_criado",
            {"card_id": card_id, "fase": 0, "intencao_inicial": intencao}
        )
        
        return {
            **state,
            "card_id": card_id,
            "tem_card_ativo": True,
            "card_fase": 0,
            "acoes_executadas": state.get("acoes_executadas", []) + ["card_criado"],
            "estado": "finalizar"
        }
        
    except Exception as e:
        print(f"[WARN] Erro ao criar card: {e}")
        return {
            **state,
            "estado": "finalizar"
        }


# ============================================
# EXPORTAÇÕES PARA COMPATIBILIDADE
# ============================================

# Estes nós são chamados pelo graph.py mas a lógica agora está diferente
# Mantidos para não quebrar imports

async def coletar_nome(state: ConversaState, llm_client) -> ConversaState:
    """Redirecionado para aguardar_nome."""
    return {**state, "estado": "aguardar_nome"}

async def coletar_cpf(state: ConversaState, llm_client) -> ConversaState:
    """Redirecionado para aguardar_cpf."""
    return {**state, "estado": "aguardar_cpf"}

async def coletar_nascimento(state: ConversaState, llm_client) -> ConversaState:
    """Redirecionado para aguardar_nascimento."""
    return {**state, "estado": "aguardar_nascimento"}

async def coletar_convenio(state: ConversaState, db, llm_client) -> ConversaState:
    """Redirecionado para aguardar_convenio."""
    return {**state, "estado": "aguardar_convenio"}
