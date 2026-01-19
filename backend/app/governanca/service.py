# -*- coding: utf-8 -*-
"""
Governança - Service
Sistema de supervisão integrado com Kanban e Evidências.

MODELO:
=======
1. Sistema EXECUTA primeiro
2. Governadora VALIDA depois
3. Se erro → Governadora CORRIGE
4. Trust score APRENDE

TRIGGERS:
=========
1. Mensagem WhatsApp recebida → Verifica interpretação e ação
2. Card criado → Verifica cumprimento de tarefas
3. Mudança de fase → Verifica evidências da fase anterior

VERIFICAÇÃO:
============
Cada tarefa do checklist tem um TIPO DE EVIDÊNCIA esperado:
- "log": Apenas registro textual (automático)
- "documento": Requer arquivo (PDF, imagem, etc)
- "confirmacao": Requer resposta do paciente
- "assinatura": Requer aprovação de profissional

PERÍODO DE IMPLANTAÇÃO:
=======================
- Primeiros 30 dias: 100% de validação
- Após 30 dias: Trust score reduz exigência conforme performance
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from app.core.database import get_authenticated_db
from app.core.security import CurrentUser
from app.core.exceptions import NotFoundError, ValidationError


class TriggerType(str, Enum):
    MENSAGEM_WHATSAPP = "mensagem_whatsapp"
    CARD_CRIADO = "card_criado"
    MUDANCA_FASE = "mudanca_fase"


class TipoEvidencia(str, Enum):
    LOG = "log"
    DOCUMENTO = "documento"
    CONFIRMACAO = "confirmacao"
    ASSINATURA = "assinatura"


class StatusValidacao(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    CORRIGIDO = "corrigido"
    REJEITADO = "rejeitado"


DIAS_IMPLANTACAO = 30
AJUSTE_APROVADO = 2
AJUSTE_CORRIGIDO = -5
AJUSTE_REJEITADO = -15

# Evidências esperadas por tarefa
EVIDENCIAS_ESPERADAS = {
    # FASE 0
    "confirmacao_enviada": {"tipo": TipoEvidencia.LOG, "campos": ["message_id", "enviado_em"]},
    "confirmado": {"tipo": TipoEvidencia.CONFIRMACAO, "campos": ["message_id", "resposta", "recebido_em"]},
    # FASE 1
    "anamnese_enviada": {"tipo": TipoEvidencia.LOG, "campos": ["message_id", "link"]},
    "anamnese_preenchida": {"tipo": TipoEvidencia.DOCUMENTO, "campos": ["anamnese_id", "preenchido_em"]},
    "exames_recebidos": {"tipo": TipoEvidencia.DOCUMENTO, "campos": ["evidencia_id", "tipo_exame"]},
    # FASE 2
    "checkin_enviado": {"tipo": TipoEvidencia.LOG, "campos": ["message_id"]},
    "checkin_confirmado": {"tipo": TipoEvidencia.CONFIRMACAO, "campos": ["resposta", "confirmado_em"]},
    "consulta_iniciada": {"tipo": TipoEvidencia.LOG, "campos": ["iniciado_em", "medico_id"]},
    "consulta_finalizada": {"tipo": TipoEvidencia.LOG, "campos": ["finalizado_em", "duracao"]},
    "audio_gravado": {"tipo": TipoEvidencia.DOCUMENTO, "campos": ["audio_id", "duracao"]},
    # FASE 3
    "soap_gerado": {"tipo": TipoEvidencia.DOCUMENTO, "campos": ["soap_id", "confianca_ia"]},
    "soap_aprovado": {"tipo": TipoEvidencia.ASSINATURA, "campos": ["aprovado_em", "medico_id"]},
    "nps_enviado": {"tipo": TipoEvidencia.LOG, "campos": ["message_id"]},
    "nps_respondido": {"tipo": TipoEvidencia.CONFIRMACAO, "campos": ["nota", "respondido_em"]},
}


class GovernancaService:
    """Serviço de governança integrado com Kanban e Evidências."""

    # ==========================================
    # TRIGGER 1: MENSAGEM WHATSAPP
    # ==========================================
    async def trigger_mensagem_whatsapp(
        self,
        clinica_id: str,
        telefone: str,
        mensagem: str,
        interpretacao: dict,
        acao_tomada: dict,
        current_user: CurrentUser
    ) -> dict:
        """
        Chegou mensagem → Sistema interpretou → Criou/atualizou algo
        Governança verifica se interpretou certo
        """
        db = get_authenticated_db(current_user.access_token)
        
        evidencia = {
            "tipo": "mensagem_whatsapp",
            "dados": {
                "telefone": telefone,
                "mensagem": mensagem[:200],
                "interpretacao": interpretacao,
                "acao": acao_tomada,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        requer = await self._requer_validacao(clinica_id, "whatsapp", db)
        
        validacao_id = None
        if requer:
            validacao_id = await self._criar_validacao(
                db, clinica_id, TriggerType.MENSAGEM_WHATSAPP,
                resumo=f"WhatsApp: \"{mensagem[:40]}...\" → {interpretacao.get('intencao', '?')}",
                evidencias=[evidencia],
                dados={
                    "mensagem_original": mensagem,
                    "interpretacao_sistema": interpretacao,
                    "acao_tomada": acao_tomada
                },
                perguntas=[
                    "A mensagem foi interpretada corretamente?",
                    "A ação tomada foi apropriada?"
                ]
            )
        
        return {"requer_validacao": requer, "validacao_id": validacao_id}

    # ==========================================
    # TRIGGER 2: CARD CRIADO
    # ==========================================
    async def trigger_card_criado(
        self,
        clinica_id: str,
        card_id: str,
        agendamento: dict,
        paciente: dict,
        current_user: CurrentUser
    ) -> dict:
        """
        Card criado → Checklist carregado
        Governança verifica dados e tarefas
        """
        db = get_authenticated_db(current_user.access_token)
        
        evidencias = [
            {"tipo": "card", "dados": {"card_id": card_id}},
            {"tipo": "agendamento", "dados": agendamento},
            {"tipo": "paciente", "dados": {"nome": paciente.get("nome"), "telefone": paciente.get("telefone")}}
        ]
        
        requer = await self._requer_validacao(clinica_id, "card_criado", db)
        
        validacao_id = None
        if requer:
            validacao_id = await self._criar_validacao(
                db, clinica_id, TriggerType.CARD_CRIADO,
                resumo=f"Card: {paciente.get('nome', '?')} - {agendamento.get('data', '?')} {agendamento.get('hora_inicio', '?')}",
                evidencias=evidencias,
                dados={"agendamento": agendamento, "paciente_resumo": paciente},
                perguntas=[
                    "Os dados do agendamento estão corretos?",
                    "O paciente está cadastrado corretamente?"
                ],
                referencia_tipo="card",
                referencia_id=card_id
            )
        
        return {"requer_validacao": requer, "validacao_id": validacao_id}

    # ==========================================
    # TRIGGER 3: MUDANÇA DE FASE
    # ==========================================
    async def trigger_mudanca_fase(
        self,
        clinica_id: str,
        card_id: str,
        fase_anterior: int,
        fase_nova: int,
        checklist_anterior: dict,
        current_user: CurrentUser
    ) -> dict:
        """
        Fase 0 → Fase 1: Verifica evidências da fase 0
        Governança confere se todas as tarefas foram cumpridas
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca evidências registradas para este card/fase
        evidencias_db = await db.select(
            table="evidencias",
            filters={"card_id": card_id, "fase": fase_anterior}
        )
        
        # Verifica cada tarefa obrigatória
        verificacao = []
        problemas = []
        
        for tarefa_key, tarefa in checklist_anterior.items():
            if not tarefa.get("obrigatorio"):
                continue
            
            config = EVIDENCIAS_ESPERADAS.get(tarefa_key, {})
            tipo_esperado = config.get("tipo", TipoEvidencia.LOG)
            campos_esperados = config.get("campos", [])
            
            # Busca evidência desta tarefa
            ev = next((e for e in evidencias_db if e.get("tarefa_key") == tarefa_key), None)
            
            status = {
                "tarefa": tarefa_key,
                "label": tarefa.get("label", tarefa_key),
                "tipo_esperado": tipo_esperado.value,
                "encontrada": ev is not None,
                "campos_esperados": campos_esperados,
                "campos_presentes": list(ev.get("dados", {}).keys()) if ev else []
            }
            
            if not ev:
                problemas.append(f"{tarefa_key}: sem evidência")
            else:
                faltando = [c for c in campos_esperados if c not in ev.get("dados", {})]
                if faltando:
                    problemas.append(f"{tarefa_key}: campos faltando {faltando}")
                    status["campos_faltando"] = faltando
            
            verificacao.append(status)
        
        # Monta evidências da validação
        evidencias = [
            {"tipo": "transicao", "dados": {"de": fase_anterior, "para": fase_nova}},
            {"tipo": "verificacao", "dados": verificacao}
        ]
        for ev in evidencias_db:
            evidencias.append({"tipo": f"evidencia_{ev.get('tarefa_key')}", "dados": ev})
        
        # Se há problemas, SEMPRE requer validação
        requer = True if problemas else await self._requer_validacao(clinica_id, f"fase_{fase_anterior}_para_{fase_nova}", db)
        
        validacao_id = None
        if requer:
            validacao_id = await self._criar_validacao(
                db, clinica_id, TriggerType.MUDANCA_FASE,
                resumo=f"Fase {fase_anterior} → {fase_nova}" + (f" ⚠️ {len(problemas)} problemas" if problemas else " ✓"),
                evidencias=evidencias,
                dados={
                    "fase_anterior": fase_anterior,
                    "fase_nova": fase_nova,
                    "verificacao": verificacao,
                    "problemas": problemas
                },
                perguntas=[
                    "Todas as tarefas obrigatórias foram cumpridas?",
                    "As evidências estão completas?",
                    "O card pode avançar?"
                ],
                referencia_tipo="card",
                referencia_id=card_id,
                prioridade="alta" if problemas else "normal"
            )
        
        return {
            "requer_validacao": requer,
            "validacao_id": validacao_id,
            "problemas": problemas,
            "verificacao": verificacao
        }

    # ==========================================
    # REGISTRAR EVIDÊNCIA
    # ==========================================
    async def registrar_evidencia(
        self,
        card_id: str,
        tarefa_key: str,
        fase: int,
        dados: dict,
        current_user: CurrentUser,
        arquivo_url: Optional[str] = None
    ) -> dict:
        """Registra prova de tarefa cumprida."""
        db = get_authenticated_db(current_user.access_token)
        
        config = EVIDENCIAS_ESPERADAS.get(tarefa_key, {})
        tipo = config.get("tipo", TipoEvidencia.LOG)
        campos_esperados = config.get("campos", [])
        campos_faltando = [c for c in campos_esperados if c not in dados]
        
        evidencia = {
            "clinica_id": current_user.clinica_id,
            "card_id": card_id,
            "tarefa_key": tarefa_key,
            "fase": fase,
            "tipo": tipo.value,
            "dados": dados,
            "arquivo_url": arquivo_url,
            "completa": len(campos_faltando) == 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        resultado = await db.insert(table="evidencias", data=evidencia)
        
        return {
            "evidencia_id": resultado["id"],
            "completa": len(campos_faltando) == 0,
            "campos_faltando": campos_faltando
        }

    # ==========================================
    # VALIDAÇÃO
    # ==========================================
    async def listar_pendentes(self, current_user: CurrentUser, trigger: Optional[TriggerType] = None) -> dict:
        db = get_authenticated_db(current_user.access_token)
        
        filters = {"clinica_id": current_user.clinica_id, "status": StatusValidacao.PENDENTE.value}
        if trigger:
            filters["trigger_type"] = trigger.value
        
        validacoes = await db.select(table="validacoes_governanca", filters=filters, order_by="created_at")
        
        por_trigger = {}
        for v in validacoes:
            t = v.get("trigger_type", "outro")
            por_trigger[t] = por_trigger.get(t, 0) + 1
        
        return {
            "total": len(validacoes),
            "com_problemas": len([v for v in validacoes if v.get("dados", {}).get("problemas")]),
            "por_trigger": por_trigger,
            "itens": validacoes
        }

    async def processar_validacao(
        self,
        validacao_id: str,
        resultado: StatusValidacao,
        current_user: CurrentUser,
        correcoes: Optional[dict] = None,
        observacao: Optional[str] = None
    ) -> dict:
        db = get_authenticated_db(current_user.access_token)
        
        validacao = await db.select_one(
            table="validacoes_governanca",
            filters={"id": validacao_id, "clinica_id": current_user.clinica_id}
        )
        
        if not validacao:
            raise NotFoundError("Validação não encontrada")
        
        if validacao["status"] != StatusValidacao.PENDENTE.value:
            raise ValidationError("Já processada")
        
        await db.update(
            table="validacoes_governanca",
            data={
                "status": resultado.value,
                "validado_por": current_user.id,
                "validado_em": datetime.utcnow().isoformat(),
                "observacao": observacao,
                "correcoes": correcoes
            },
            filters={"id": validacao_id}
        )
        
        # Atualiza trust
        trust_key = validacao.get("trigger_type", "geral")
        novo_trust = await self._atualizar_trust(validacao["clinica_id"], trust_key, resultado, db)
        
        # Aplica correções
        if correcoes and validacao.get("referencia_tipo") and validacao.get("referencia_id"):
            await db.update(
                table=validacao["referencia_tipo"] + "s",
                data=correcoes,
                filters={"id": validacao["referencia_id"]}
            )
        
        return {"resultado": resultado.value, "trust_novo": novo_trust}

    # ==========================================
    # DASHBOARD
    # ==========================================
    async def get_dashboard(self, current_user: CurrentUser) -> dict:
        db = get_authenticated_db(current_user.access_token)
        clinica_id = current_user.clinica_id
        
        em_implantacao = await self._em_implantacao(clinica_id, db)
        dias_restantes = await self._dias_restantes(clinica_id, db)
        pendentes = await self.listar_pendentes(current_user)
        
        # Métricas 30 dias
        data_inicio = datetime.utcnow() - timedelta(days=30)
        validacoes = await db.select(
            table="validacoes_governanca",
            filters={"clinica_id": clinica_id, "created_at__gte": data_inicio.isoformat()}
        )
        
        aprovadas = len([v for v in validacoes if v["status"] == "aprovado"])
        corrigidas = len([v for v in validacoes if v["status"] == "corrigido"])
        rejeitadas = len([v for v in validacoes if v["status"] == "rejeitado"])
        total_processadas = aprovadas + corrigidas + rejeitadas
        
        return {
            "implantacao": {
                "ativa": em_implantacao,
                "dias_restantes": dias_restantes,
                "taxa_validacao": "100%" if em_implantacao else "variável"
            },
            "pendentes": pendentes,
            "performance_30d": {
                "total": len(validacoes),
                "aprovadas": aprovadas,
                "corrigidas": corrigidas,
                "rejeitadas": rejeitadas,
                "taxa_acerto": round(aprovadas / total_processadas, 3) if total_processadas > 0 else 0
            }
        }

    # ==========================================
    # HELPERS
    # ==========================================
    async def _requer_validacao(self, clinica_id: str, chave: str, db) -> bool:
        """Verifica se requer validação baseado em implantação + trust."""
        if await self._em_implantacao(clinica_id, db):
            return True  # 100% nos primeiros 30 dias
        
        trust = await self._get_trust(clinica_id, chave, db)
        return trust < 90  # Só dispensa se trust > 90%

    async def _em_implantacao(self, clinica_id: str, db) -> bool:
        clinica = await db.select_one(table="clinicas", filters={"id": clinica_id})
        if not clinica or not clinica.get("data_inicio_sistema"):
            return True
        
        inicio = clinica["data_inicio_sistema"]
        if isinstance(inicio, str):
            inicio = datetime.fromisoformat(inicio.replace("Z", ""))
        
        return (datetime.utcnow() - inicio).days < DIAS_IMPLANTACAO

    async def _dias_restantes(self, clinica_id: str, db) -> int:
        clinica = await db.select_one(table="clinicas", filters={"id": clinica_id})
        if not clinica or not clinica.get("data_inicio_sistema"):
            return DIAS_IMPLANTACAO
        
        inicio = clinica["data_inicio_sistema"]
        if isinstance(inicio, str):
            inicio = datetime.fromisoformat(inicio.replace("Z", ""))
        
        return max(0, DIAS_IMPLANTACAO - (datetime.utcnow() - inicio).days)

    async def _get_trust(self, clinica_id: str, chave: str, db) -> float:
        registro = await db.select_one(
            table="trust_scores",
            filters={"clinica_id": clinica_id, "chave": chave}
        )
        return registro["valor"] if registro else 50.0

    async def _atualizar_trust(self, clinica_id: str, chave: str, resultado: StatusValidacao, db) -> float:
        registro = await db.select_one(
            table="trust_scores",
            filters={"clinica_id": clinica_id, "chave": chave}
        )
        
        valor = registro["valor"] if registro else 50.0
        total = registro["total"] if registro else 0
        
        ajuste = AJUSTE_APROVADO if resultado == StatusValidacao.APROVADO else (
            AJUSTE_CORRIGIDO if resultado == StatusValidacao.CORRIGIDO else AJUSTE_REJEITADO
        )
        
        novo = max(0, min(100, valor + ajuste))
        
        if registro:
            await db.update(table="trust_scores", data={"valor": novo, "total": total + 1}, filters={"id": registro["id"]})
        else:
            await db.insert(table="trust_scores", data={"clinica_id": clinica_id, "chave": chave, "valor": novo, "total": 1})
        
        return novo

    async def _criar_validacao(
        self, db, clinica_id: str, trigger: TriggerType, resumo: str,
        evidencias: list, dados: dict, perguntas: list,
        referencia_tipo: str = None, referencia_id: str = None, prioridade: str = "normal"
    ) -> str:
        resultado = await db.insert(
            table="validacoes_governanca",
            data={
                "clinica_id": clinica_id,
                "trigger_type": trigger.value,
                "resumo": resumo,
                "evidencias": evidencias,
                "dados": dados,
                "perguntas": perguntas,
                "referencia_tipo": referencia_tipo,
                "referencia_id": referencia_id,
                "prioridade": prioridade,
                "status": StatusValidacao.PENDENTE.value,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        return resultado["id"]


governanca_service = GovernancaService()
