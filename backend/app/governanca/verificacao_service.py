# -*- coding: utf-8 -*-
"""
Verificação de Evidências - Service
Verifica se tarefas do Kanban têm as evidências necessárias.

TRIGGERS:
=========
1. Mensagem WhatsApp recebida → Verifica cadastro
2. Card criado → Verifica dados iniciais
3. Mudança de fase → Verifica checklist da fase anterior

TIPOS DE EVIDÊNCIA:
==================
- log: Sistema registra automaticamente (mensagem, ação)
- documento: Precisa de arquivo anexado (anamnese, exame, SOAP)
- confirmacao: Ação humana (médico clica botão)

MODELO DE VALIDAÇÃO:
===================
- Executa primeiro, valida depois
- Primeiros 30 dias: 100% validação
- Depois: Diminui conforme performance
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from app.core.database import get_authenticated_db
from app.core.security import CurrentUser


class TipoEvidencia(str, Enum):
    """Tipos de evidência para tarefas."""
    LOG = "log"                 # Sistema registra automaticamente
    DOCUMENTO = "documento"     # Precisa de arquivo
    CONFIRMACAO = "confirmacao" # Ação humana


class TipoTrigger(str, Enum):
    """Triggers de verificação."""
    MENSAGEM_WHATSAPP = "mensagem_whatsapp"
    CARD_CRIADO = "card_criado"
    MUDANCA_FASE = "mudanca_fase"


class StatusVerificacao(str, Enum):
    """Status da verificação."""
    COMPLETO = "completo"
    INCOMPLETO = "incompleto"
    PENDENTE_VALIDACAO = "pendente_validacao"


# ============================================
# CONFIGURAÇÃO DE EVIDÊNCIAS POR TAREFA
# ============================================

EVIDENCIAS_CHECKLIST = {
    # FASE 0: AGENDADO
    "confirmacao_enviada": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Log de envio da mensagem de confirmação",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "confirmacao_consulta", "direcao": "enviada"}
    },
    "confirmado": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Log de resposta do paciente",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "confirmacao_consulta", "direcao": "recebida"}
    },
    
    # FASE 1: PRÉ-CONSULTA
    "anamnese_enviada": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Log de envio do link de anamnese",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "anamnese_solicitacao"}
    },
    "anamnese_preenchida": {
        "tipo": TipoEvidencia.DOCUMENTO,
        "descricao": "Formulário de anamnese preenchido",
        "tabela_evidencia": "evidencias",
        "filtro": {"tipo": "anamnese"}
    },
    "exames_recebidos": {
        "tipo": TipoEvidencia.DOCUMENTO,
        "descricao": "Arquivos de exames anexados",
        "tabela_evidencia": "evidencias",
        "filtro": {"tipo": "exame"},
        "opcional": True
    },
    
    # FASE 2: DIA DA CONSULTA
    "checkin_enviado": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Log de envio do pedido de check-in",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "checkin_solicitacao"}
    },
    "checkin_confirmado": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Log de confirmação de chegada",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "checkin_resposta"}
    },
    "consulta_iniciada": {
        "tipo": TipoEvidencia.CONFIRMACAO,
        "descricao": "Médico iniciou atendimento",
        "tabela_evidencia": "card_eventos",
        "filtro": {"tipo": "consulta_iniciada"}
    },
    "consulta_finalizada": {
        "tipo": TipoEvidencia.CONFIRMACAO,
        "descricao": "Médico finalizou atendimento",
        "tabela_evidencia": "card_eventos",
        "filtro": {"tipo": "consulta_finalizada"}
    },
    
    # FASE 3: PÓS-CONSULTA
    "audio_gravado": {
        "tipo": TipoEvidencia.DOCUMENTO,
        "descricao": "Áudio da consulta",
        "tabela_evidencia": "evidencias",
        "filtro": {"tipo": "audio_consulta"},
        "opcional": True
    },
    "transcricao_gerada": {
        "tipo": TipoEvidencia.DOCUMENTO,
        "descricao": "Transcrição do áudio",
        "tabela_evidencia": "evidencias",
        "filtro": {"tipo": "transcricao"},
        "opcional": True
    },
    "soap_gerado": {
        "tipo": TipoEvidencia.DOCUMENTO,
        "descricao": "SOAP gerado pela IA",
        "tabela_evidencia": "evidencias",
        "filtro": {"tipo": "soap"}
    },
    "soap_aprovado": {
        "tipo": TipoEvidencia.CONFIRMACAO,
        "descricao": "Médico aprovou o SOAP",
        "tabela_evidencia": "card_eventos",
        "filtro": {"tipo": "soap_aprovado"}
    },
    "nps_enviado": {
        "tipo": TipoEvidencia.LOG,
        "descricao": "Pesquisa NPS enviada",
        "tabela_evidencia": "mensagens",
        "filtro": {"tipo": "nps_solicitacao"}
    }
}


class VerificacaoService:
    """Serviço de verificação de evidências."""

    # ==========================================
    # TRIGGER 1: MENSAGEM WHATSAPP
    # ==========================================
    
    async def verificar_mensagem_whatsapp(
        self,
        telefone: str,
        mensagem_id: str,
        clinica_id: str,
        current_user: CurrentUser
    ) -> dict:
        """
        Trigger 1: Verifica se cadastro foi criado corretamente
        após receber mensagem do WhatsApp.
        
        Verifica:
        - Paciente existe no banco?
        - Dados básicos preenchidos?
        - Histórico de interação?
        """
        db = get_authenticated_db(current_user.access_token)
        
        verificacoes = []
        
        # 1. Verifica se paciente existe
        paciente = await db.select_one(
            table="pacientes",
            filters={"telefone": telefone, "clinica_id": clinica_id}
        )
        
        if paciente:
            verificacoes.append({
                "item": "cadastro_existe",
                "status": "ok",
                "evidencia": {
                    "tipo": "log",
                    "registro": f"Paciente ID: {paciente['id']}",
                    "created_at": paciente.get("created_at")
                }
            })
            
            # 2. Verifica dados obrigatórios
            campos_obrigatorios = ["nome", "telefone"]
            campos_faltando = [c for c in campos_obrigatorios if not paciente.get(c)]
            
            if campos_faltando:
                verificacoes.append({
                    "item": "dados_basicos",
                    "status": "incompleto",
                    "faltando": campos_faltando,
                    "evidencia": None
                })
            else:
                verificacoes.append({
                    "item": "dados_basicos",
                    "status": "ok",
                    "evidencia": {
                        "tipo": "log",
                        "campos": {c: paciente.get(c) for c in campos_obrigatorios}
                    }
                })
        else:
            verificacoes.append({
                "item": "cadastro_existe",
                "status": "incompleto",
                "evidencia": None,
                "acao_sugerida": "Criar cadastro do paciente"
            })
        
        # 3. Registra log de verificação
        await self._registrar_verificacao(
            db=db,
            clinica_id=clinica_id,
            trigger=TipoTrigger.MENSAGEM_WHATSAPP,
            referencia_tipo="mensagem",
            referencia_id=mensagem_id,
            verificacoes=verificacoes
        )
        
        return {
            "trigger": TipoTrigger.MENSAGEM_WHATSAPP.value,
            "telefone": telefone,
            "status": self._calcular_status_geral(verificacoes),
            "verificacoes": verificacoes,
            "requer_atencao": any(v["status"] == "incompleto" for v in verificacoes)
        }

    # ==========================================
    # TRIGGER 2: CARD CRIADO
    # ==========================================
    
    async def verificar_card_criado(
        self,
        card_id: str,
        current_user: CurrentUser
    ) -> dict:
        """
        Trigger 2: Verifica se card foi criado com dados corretos.
        
        Verifica:
        - Agendamento associado existe?
        - Paciente tem dados mínimos?
        - Médico atribuído?
        - Checklist inicial configurado?
        """
        db = get_authenticated_db(current_user.access_token)
        
        verificacoes = []
        
        # Busca card com relacionamentos
        card = await db.select_one(
            table="cards",
            filters={"id": card_id, "clinica_id": current_user.clinica_id}
        )
        
        if not card:
            return {"erro": "Card não encontrado"}
        
        # 1. Verifica agendamento
        agendamento = await db.select_one(
            table="agendamentos",
            filters={"id": card["agendamento_id"]}
        )
        
        if agendamento:
            verificacoes.append({
                "item": "agendamento_vinculado",
                "status": "ok",
                "evidencia": {
                    "tipo": "log",
                    "agendamento_id": agendamento["id"],
                    "data": agendamento.get("data"),
                    "hora": agendamento.get("hora_inicio")
                }
            })
        else:
            verificacoes.append({
                "item": "agendamento_vinculado",
                "status": "incompleto",
                "evidencia": None,
                "acao_sugerida": "Vincular agendamento ao card"
            })
        
        # 2. Verifica paciente
        paciente = await db.select_one(
            table="pacientes",
            filters={"id": card["paciente_id"]}
        )
        
        if paciente and paciente.get("nome") and paciente.get("telefone"):
            verificacoes.append({
                "item": "paciente_dados",
                "status": "ok",
                "evidencia": {
                    "tipo": "log",
                    "paciente_id": paciente["id"],
                    "nome": paciente["nome"],
                    "telefone": paciente["telefone"]
                }
            })
        else:
            verificacoes.append({
                "item": "paciente_dados",
                "status": "incompleto",
                "evidencia": None,
                "acao_sugerida": "Completar cadastro do paciente"
            })
        
        # 3. Verifica médico
        if card.get("medico_id"):
            verificacoes.append({
                "item": "medico_atribuido",
                "status": "ok",
                "evidencia": {
                    "tipo": "log",
                    "medico_id": card["medico_id"]
                }
            })
        else:
            verificacoes.append({
                "item": "medico_atribuido",
                "status": "incompleto",
                "evidencia": None,
                "acao_sugerida": "Atribuir médico ao card"
            })
        
        # 4. Verifica checklist inicial
        checklist = card.get("checklist", {})
        if checklist:
            verificacoes.append({
                "item": "checklist_configurado",
                "status": "ok",
                "evidencia": {
                    "tipo": "log",
                    "itens": len(checklist)
                }
            })
        else:
            verificacoes.append({
                "item": "checklist_configurado",
                "status": "incompleto",
                "evidencia": None,
                "acao_sugerida": "Configurar checklist do card"
            })
        
        # Registra verificação
        await self._registrar_verificacao(
            db=db,
            clinica_id=current_user.clinica_id,
            trigger=TipoTrigger.CARD_CRIADO,
            referencia_tipo="card",
            referencia_id=card_id,
            verificacoes=verificacoes
        )
        
        return {
            "trigger": TipoTrigger.CARD_CRIADO.value,
            "card_id": card_id,
            "fase": card["fase"],
            "status": self._calcular_status_geral(verificacoes),
            "verificacoes": verificacoes,
            "requer_atencao": any(v["status"] == "incompleto" for v in verificacoes)
        }

    # ==========================================
    # TRIGGER 3: MUDANÇA DE FASE
    # ==========================================
    
    async def verificar_mudanca_fase(
        self,
        card_id: str,
        fase_anterior: int,
        fase_nova: int,
        current_user: CurrentUser
    ) -> dict:
        """
        Trigger 3: Verifica se todas as tarefas da fase anterior
        foram cumpridas com evidências.
        
        Verifica cada item do checklist da fase anterior:
        - Se tipo "log": Busca na tabela de logs/mensagens
        - Se tipo "documento": Busca na tabela de evidências
        - Se tipo "confirmacao": Busca evento de confirmação
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca card
        card = await db.select_one(
            table="cards",
            filters={"id": card_id, "clinica_id": current_user.clinica_id}
        )
        
        if not card:
            return {"erro": "Card não encontrado"}
        
        checklist = card.get("checklist", {})
        verificacoes = []
        
        # Para cada item do checklist da fase anterior
        for item_key, item_data in checklist.items():
            config_evidencia = EVIDENCIAS_CHECKLIST.get(item_key, {})
            
            if not config_evidencia:
                continue
            
            # Pula itens opcionais não marcados
            if config_evidencia.get("opcional") and not item_data.get("concluido"):
                continue
            
            # Verifica se evidência existe
            evidencia = await self._buscar_evidencia(
                db=db,
                card=card,
                item_key=item_key,
                config=config_evidencia
            )
            
            if evidencia:
                verificacoes.append({
                    "item": item_key,
                    "label": item_data.get("label", item_key),
                    "tipo_evidencia": config_evidencia["tipo"].value,
                    "status": "ok",
                    "evidencia": evidencia
                })
            else:
                # Item obrigatório sem evidência
                if not config_evidencia.get("opcional"):
                    verificacoes.append({
                        "item": item_key,
                        "label": item_data.get("label", item_key),
                        "tipo_evidencia": config_evidencia["tipo"].value,
                        "status": "incompleto",
                        "evidencia": None,
                        "descricao_esperada": config_evidencia.get("descricao"),
                        "acao_sugerida": f"Anexar {config_evidencia['tipo'].value}: {item_key}"
                    })
        
        # Registra verificação
        await self._registrar_verificacao(
            db=db,
            clinica_id=current_user.clinica_id,
            trigger=TipoTrigger.MUDANCA_FASE,
            referencia_tipo="card",
            referencia_id=card_id,
            verificacoes=verificacoes,
            dados_extra={
                "fase_anterior": fase_anterior,
                "fase_nova": fase_nova
            }
        )
        
        status_geral = self._calcular_status_geral(verificacoes)
        requer_atencao = any(v["status"] == "incompleto" for v in verificacoes)
        
        # Se tem problema, cria alerta para governadora
        if requer_atencao:
            await self._criar_alerta_governanca(
                db=db,
                clinica_id=current_user.clinica_id,
                card_id=card_id,
                trigger=TipoTrigger.MUDANCA_FASE,
                verificacoes=verificacoes,
                fase_anterior=fase_anterior,
                fase_nova=fase_nova
            )
        
        return {
            "trigger": TipoTrigger.MUDANCA_FASE.value,
            "card_id": card_id,
            "fase_anterior": fase_anterior,
            "fase_nova": fase_nova,
            "status": status_geral,
            "verificacoes": verificacoes,
            "requer_atencao": requer_atencao,
            "total_itens": len(verificacoes),
            "itens_ok": len([v for v in verificacoes if v["status"] == "ok"]),
            "itens_faltando": len([v for v in verificacoes if v["status"] == "incompleto"])
        }

    # ==========================================
    # BUSCAR EVIDÊNCIA
    # ==========================================
    
    async def _buscar_evidencia(
        self,
        db,
        card: dict,
        item_key: str,
        config: dict
    ) -> Optional[dict]:
        """Busca evidência de uma tarefa na tabela apropriada."""
        
        tabela = config.get("tabela_evidencia")
        filtro_base = config.get("filtro", {})
        
        if not tabela:
            return None
        
        # Monta filtro específico por tabela
        filtro = {**filtro_base}
        
        if tabela == "mensagens":
            filtro["agendamento_id"] = card.get("agendamento_id")
        elif tabela == "evidencias":
            filtro["card_id"] = card["id"]
        elif tabela == "card_eventos":
            filtro["card_id"] = card["id"]
        
        # Busca registro
        try:
            registro = await db.select(
                table=tabela,
                filters=filtro,
                limit=1
            )
            
            if registro and len(registro) > 0:
                reg = registro[0]
                return {
                    "tipo": config["tipo"].value,
                    "tabela": tabela,
                    "registro_id": reg.get("id"),
                    "created_at": reg.get("created_at"),
                    "dados_resumo": self._resumir_evidencia(reg, tabela)
                }
        except Exception as e:
            pass
        
        return None
    
    def _resumir_evidencia(self, registro: dict, tabela: str) -> dict:
        """Cria resumo da evidência para exibição."""
        
        if tabela == "mensagens":
            return {
                "tipo_mensagem": registro.get("tipo"),
                "direcao": registro.get("direcao"),
                "preview": registro.get("conteudo", "")[:50] + "..."
            }
        elif tabela == "evidencias":
            return {
                "tipo_documento": registro.get("tipo"),
                "nome_arquivo": registro.get("nome_arquivo"),
                "url": registro.get("url")
            }
        elif tabela == "card_eventos":
            return {
                "tipo_evento": registro.get("tipo"),
                "usuario": registro.get("usuario_id")
            }
        
        return {}

    # ==========================================
    # HELPERS
    # ==========================================
    
    def _calcular_status_geral(self, verificacoes: List[dict]) -> str:
        """Calcula status geral baseado nas verificações."""
        if not verificacoes:
            return StatusVerificacao.COMPLETO.value
        
        incompletos = [v for v in verificacoes if v["status"] == "incompleto"]
        
        if not incompletos:
            return StatusVerificacao.COMPLETO.value
        
        return StatusVerificacao.INCOMPLETO.value
    
    async def _registrar_verificacao(
        self,
        db,
        clinica_id: str,
        trigger: TipoTrigger,
        referencia_tipo: str,
        referencia_id: str,
        verificacoes: List[dict],
        dados_extra: dict = None
    ):
        """Registra log da verificação."""
        
        await db.insert(
            table="verificacoes_log",
            data={
                "clinica_id": clinica_id,
                "trigger": trigger.value,
                "referencia_tipo": referencia_tipo,
                "referencia_id": referencia_id,
                "status": self._calcular_status_geral(verificacoes),
                "verificacoes": verificacoes,
                "dados_extra": dados_extra,
                "created_at": datetime.utcnow().isoformat()
            }
        )
    
    async def _criar_alerta_governanca(
        self,
        db,
        clinica_id: str,
        card_id: str,
        trigger: TipoTrigger,
        verificacoes: List[dict],
        fase_anterior: int = None,
        fase_nova: int = None
    ):
        """Cria alerta para a governadora quando há problemas."""
        
        itens_faltando = [v for v in verificacoes if v["status"] == "incompleto"]
        
        # Monta resumo
        resumo = f"Card mudou da fase {fase_anterior} para {fase_nova}, mas {len(itens_faltando)} evidência(s) não encontrada(s)"
        
        await db.insert(
            table="alertas_governanca",
            data={
                "clinica_id": clinica_id,
                "tipo": "evidencia_faltando",
                "trigger": trigger.value,
                "card_id": card_id,
                "resumo": resumo,
                "itens_faltando": itens_faltando,
                "prioridade": "alta" if len(itens_faltando) > 2 else "normal",
                "status": "pendente",
                "created_at": datetime.utcnow().isoformat()
            }
        )

    # ==========================================
    # DASHBOARD DA GOVERNADORA
    # ==========================================
    
    async def listar_alertas_pendentes(
        self,
        current_user: CurrentUser,
        limit: int = 50
    ) -> dict:
        """Lista alertas pendentes para a governadora."""
        
        db = get_authenticated_db(current_user.access_token)
        
        alertas = await db.select(
            table="alertas_governanca",
            filters={
                "clinica_id": current_user.clinica_id,
                "status": "pendente"
            },
            order_by="created_at",
            order_asc=False,
            limit=limit
        )
        
        # Agrupa por trigger
        por_trigger = {}
        for a in alertas:
            t = a.get("trigger", "outro")
            por_trigger[t] = por_trigger.get(t, 0) + 1
        
        return {
            "total": len(alertas),
            "por_trigger": por_trigger,
            "alertas": alertas
        }
    
    async def resolver_alerta(
        self,
        alerta_id: str,
        resolucao: str,
        current_user: CurrentUser,
        observacao: str = None
    ) -> dict:
        """Governadora resolve um alerta."""
        
        db = get_authenticated_db(current_user.access_token)
        
        await db.update(
            table="alertas_governanca",
            data={
                "status": "resolvido",
                "resolucao": resolucao,
                "resolvido_por": current_user.id,
                "resolvido_em": datetime.utcnow().isoformat(),
                "observacao": observacao
            },
            filters={"id": alerta_id}
        )
        
        return {"sucesso": True, "alerta_id": alerta_id}

    # ==========================================
    # MÉTRICAS DE PERFORMANCE
    # ==========================================
    
    async def calcular_taxa_validacao(
        self,
        clinica_id: str,
        current_user: CurrentUser,
        dias: int = 30
    ) -> dict:
        """
        Calcula taxa de validação necessária baseado em performance.
        
        Primeiros 30 dias: 100%
        Depois: Diminui conforme taxa de sucesso
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca data de início da clínica
        clinica = await db.select_one(
            table="clinicas",
            filters={"id": clinica_id}
        )
        
        data_inicio = datetime.fromisoformat(
            clinica.get("created_at", datetime.utcnow().isoformat()).replace("Z", "")
        )
        dias_desde_inicio = (datetime.utcnow() - data_inicio).days
        
        # Fase de implantação: 100% validação
        if dias_desde_inicio <= 30:
            return {
                "fase": "implantacao",
                "dias_desde_inicio": dias_desde_inicio,
                "dias_restantes_implantacao": 30 - dias_desde_inicio,
                "taxa_validacao": 1.0,
                "motivo": "Período de implantação (primeiros 30 dias)"
            }
        
        # Após implantação: calcula baseado em performance
        data_corte = datetime.utcnow() - timedelta(days=dias)
        
        verificacoes = await db.select(
            table="verificacoes_log",
            filters={
                "clinica_id": clinica_id,
                "created_at__gte": data_corte.isoformat()
            }
        )
        
        if not verificacoes:
            return {
                "fase": "normal",
                "taxa_validacao": 0.5,  # 50% default
                "motivo": "Sem dados suficientes, usando taxa padrão"
            }
        
        # Calcula taxa de sucesso
        total = len(verificacoes)
        completos = len([v for v in verificacoes if v["status"] == "completo"])
        taxa_sucesso = completos / total if total > 0 else 0
        
        # Taxa de validação inversamente proporcional ao sucesso
        # Sucesso 100% → Validação 5%
        # Sucesso 90% → Validação 20%
        # Sucesso 80% → Validação 40%
        # Sucesso 70% → Validação 60%
        # Sucesso < 70% → Validação 100%
        
        if taxa_sucesso >= 0.95:
            taxa_validacao = 0.05
        elif taxa_sucesso >= 0.90:
            taxa_validacao = 0.20
        elif taxa_sucesso >= 0.80:
            taxa_validacao = 0.40
        elif taxa_sucesso >= 0.70:
            taxa_validacao = 0.60
        else:
            taxa_validacao = 1.0
        
        return {
            "fase": "normal",
            "dias_desde_inicio": dias_desde_inicio,
            "periodo_analise": f"{dias} dias",
            "total_verificacoes": total,
            "verificacoes_completas": completos,
            "taxa_sucesso": round(taxa_sucesso, 3),
            "taxa_validacao": taxa_validacao,
            "motivo": f"Baseado em {total} verificações com {round(taxa_sucesso*100)}% de sucesso"
        }


# Instância global
verificacao_service = VerificacaoService()
