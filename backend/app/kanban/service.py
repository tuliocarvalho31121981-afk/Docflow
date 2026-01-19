# -*- coding: utf-8 -*-
"""
Kanban - Service
Gerenciamento automático de cards com transições baseadas em checklist.

LÓGICA PRINCIPAL:
- Cada fase tem um checklist de itens obrigatórios e opcionais
- Quando TODOS os itens obrigatórios de uma fase são completados,
  o card move automaticamente para a próxima fase
- A nova fase recebe seu próprio checklist zerado
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import IntEnum

from app.core.database import get_authenticated_db
from app.core.security import CurrentUser
from app.core.exceptions import NotFoundError, ValidationError


class FaseKanban(IntEnum):
    """Fases do Kanban."""
    AGENDADO = 0
    PRE_CONSULTA = 1
    DIA_CONSULTA = 2
    POS_CONSULTA = 3
    FINALIZADO = 4


# ============================================
# DEFINIÇÃO DOS CHECKLISTS POR FASE
# ============================================
CHECKLIST_POR_FASE = {
    FaseKanban.AGENDADO: {
        "obrigatorios": [
            {"key": "confirmacao_enviada", "label": "Confirmação enviada", "auto": True},
            {"key": "confirmado", "label": "Paciente confirmou", "auto": True},
        ],
        "opcionais": []
    },
    FaseKanban.PRE_CONSULTA: {
        "obrigatorios": [
            {"key": "anamnese_enviada", "label": "Anamnese enviada", "auto": True},
            {"key": "anamnese_preenchida", "label": "Anamnese preenchida", "auto": True},
        ],
        "opcionais": [
            {"key": "exames_solicitados", "label": "Exames solicitados", "auto": False},
            {"key": "exames_recebidos", "label": "Exames recebidos", "auto": True},
            {"key": "documentos_enviados", "label": "Documentos enviados", "auto": True},
        ]
    },
    FaseKanban.DIA_CONSULTA: {
        "obrigatorios": [
            {"key": "checkin_enviado", "label": "Check-in enviado", "auto": True},
            {"key": "checkin_confirmado", "label": "Check-in confirmado", "auto": True},
            {"key": "consulta_iniciada", "label": "Consulta iniciada", "auto": False},
            {"key": "consulta_finalizada", "label": "Consulta finalizada", "auto": False},
        ],
        "opcionais": [
            {"key": "audio_gravado", "label": "Áudio gravado", "auto": True},
        ]
    },
    FaseKanban.POS_CONSULTA: {
        "obrigatorios": [
            {"key": "soap_gerado", "label": "SOAP gerado", "auto": True},
            {"key": "soap_aprovado", "label": "SOAP aprovado", "auto": False},
        ],
        "opcionais": [
            {"key": "receita_emitida", "label": "Receita emitida", "auto": False},
            {"key": "atestado_emitido", "label": "Atestado emitido", "auto": False},
            {"key": "retorno_agendado", "label": "Retorno agendado", "auto": True},
            {"key": "nps_enviado", "label": "NPS enviado", "auto": True},
            {"key": "nps_respondido", "label": "NPS respondido", "auto": True},
        ]
    },
    FaseKanban.FINALIZADO: {
        "obrigatorios": [],
        "opcionais": []
    }
}


# ============================================
# SUBFASES (status dentro de cada fase)
# ============================================
SUBFASES_POR_FASE = {
    FaseKanban.AGENDADO: ["aguardando_confirmacao", "confirmado"],
    FaseKanban.PRE_CONSULTA: ["pendente", "em_andamento", "pronto"],
    FaseKanban.DIA_CONSULTA: ["aguardando_checkin", "em_espera", "em_atendimento", "finalizado"],
    FaseKanban.POS_CONSULTA: ["aguardando_soap", "soap_pendente", "concluido"],
    FaseKanban.FINALIZADO: ["arquivado"],
}


class KanbanService:
    """Serviço de gerenciamento de Kanban com automação."""

    async def get_card(
        self,
        card_id: str,
        current_user: CurrentUser
    ) -> dict:
        """Busca card por ID."""
        db = get_authenticated_db(current_user.access_token)
        
        result = await db.select_one(
            table="cards",
            filters={
                "id": card_id,
                "clinica_id": current_user.clinica_id
            }
        )

        if not result:
            raise NotFoundError("Card não encontrado")

        return result

    async def get_card_by_agendamento(
        self,
        agendamento_id: str,
        current_user: CurrentUser
    ) -> dict:
        """Busca card por agendamento."""
        db = get_authenticated_db(current_user.access_token)
        
        result = await db.select_one(
            table="cards",
            filters={
                "agendamento_id": agendamento_id,
                "clinica_id": current_user.clinica_id
            }
        )

        if not result:
            raise NotFoundError("Card não encontrado para este agendamento")

        return result

    async def criar_card(
        self,
        agendamento_id: str,
        current_user: CurrentUser
    ) -> dict:
        """
        Cria novo card para um agendamento.
        Inicializa na fase 0 (AGENDADO) com checklist zerado.
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca dados do agendamento
        agendamento = await db.select_one(
            table="agendamentos",
            filters={"id": agendamento_id}
        )

        if not agendamento:
            raise NotFoundError("Agendamento não encontrado")
        
        # Monta checklist inicial
        checklist = self._criar_checklist_fase(FaseKanban.AGENDADO)
        
        card_data = {
            "clinica_id": current_user.clinica_id,
            "agendamento_id": agendamento_id,
            "paciente_id": agendamento["paciente_id"],
            "medico_id": agendamento["medico_id"],
            "fase": FaseKanban.AGENDADO,
            "subfase": "aguardando_confirmacao",
            "checklist": checklist,
            "status": "ativo",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        result = await db.insert(table="cards", data=card_data)
        return result

    async def atualizar_checklist_item(
        self,
        card_id: str,
        item_key: str,
        concluido: bool,
        current_user: CurrentUser,
        automatico: bool = False,
        origem: Optional[str] = None
    ) -> dict:
        """
        Atualiza um item do checklist.
        Se todos os obrigatórios forem concluídos, move para próxima fase.
        
        Args:
            card_id: ID do card
            item_key: Chave do item (ex: "confirmado", "anamnese_preenchida")
            concluido: Se o item está concluído
            current_user: Usuário atual
            automatico: Se foi marcado automaticamente pelo sistema
            origem: Origem da atualização (ex: "whatsapp", "manual")
        
        Returns:
            Card atualizado (pode ter mudado de fase)
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca card atual
        card = await self.get_card(card_id, current_user)
        fase_atual = FaseKanban(card["fase"])
        checklist = card.get("checklist", {})
        
        # Atualiza item no checklist
        if item_key not in checklist:
            # Item não existe no checklist atual - pode ser de outra fase
            raise ValidationError(f"Item '{item_key}' não existe no checklist da fase atual")
        
        checklist[item_key] = {
            "concluido": concluido,
            "concluido_em": datetime.utcnow().isoformat() if concluido else None,
            "concluido_por": current_user.id if not automatico else "sistema",
            "automatico": automatico,
            "origem": origem
        }
        
        # Atualiza card com novo checklist
        update_data = {
            "checklist": checklist,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Verifica se deve mover de fase
        proxima_fase = self._verificar_transicao_fase(fase_atual, checklist)
        
        if proxima_fase is not None:
            update_data["fase"] = proxima_fase
            update_data["subfase"] = SUBFASES_POR_FASE[FaseKanban(proxima_fase)][0]
            update_data["checklist"] = self._criar_checklist_fase(FaseKanban(proxima_fase))
            update_data["historico_fases"] = card.get("historico_fases", []) + [{
                "fase_anterior": fase_atual,
                "fase_nova": proxima_fase,
                "transicao_em": datetime.utcnow().isoformat(),
                "automatico": True,
                "motivo": "Checklist completo"
            }]
        
        # Atualiza no banco
        result = await db.update(
            table="cards",
            data=update_data,
            filters={"id": card_id}
        )
        
        # Se mudou de fase, dispara eventos
        if proxima_fase is not None:
            await self._on_mudanca_fase(
                card_id=card_id,
                fase_anterior=fase_atual,
                fase_nova=FaseKanban(proxima_fase),
                current_user=current_user
            )
        
        return result

    async def mover_card(
        self,
        card_id: str,
        fase: int,
        current_user: CurrentUser,
        subfase: Optional[str] = None,
        automatico: bool = False,
        motivo: Optional[str] = None
    ) -> dict:
        """
        Move card para outra fase manualmente.
        Usado quando o usuário quer forçar uma transição.
        """
        db = get_authenticated_db(current_user.access_token)
        
        card = await self.get_card(card_id, current_user)
        fase_anterior = card["fase"]
        
        # Valida fase
        if fase not in [f.value for f in FaseKanban]:
            raise ValidationError(f"Fase inválida: {fase}")
        
        # Valida subfase
        subfases_validas = SUBFASES_POR_FASE.get(FaseKanban(fase), [])
        if subfase and subfase not in subfases_validas:
            raise ValidationError(f"Subfase inválida: {subfase}")
        
        update_data = {
            "fase": fase,
            "subfase": subfase or subfases_validas[0] if subfases_validas else None,
            "checklist": self._criar_checklist_fase(FaseKanban(fase)),
            "updated_at": datetime.utcnow().isoformat(),
            "historico_fases": card.get("historico_fases", []) + [{
                "fase_anterior": fase_anterior,
                "fase_nova": fase,
                "transicao_em": datetime.utcnow().isoformat(),
                "automatico": automatico,
                "motivo": motivo,
                "usuario_id": current_user.id if not automatico else None
            }]
        }
        
        result = await db.update(table="cards", data=update_data, filters={"id": card_id})
        
        # Dispara eventos
        await self._on_mudanca_fase(
            card_id=card_id,
            fase_anterior=FaseKanban(fase_anterior),
            fase_nova=FaseKanban(fase),
            current_user=current_user
        )
        
        return result

    async def atualizar_subfase(
        self,
        card_id: str,
        subfase: str,
        current_user: CurrentUser
    ) -> dict:
        """Atualiza subfase do card (sem mudar a fase principal)."""
        db = get_authenticated_db(current_user.access_token)
        
        card = await self.get_card(card_id, current_user)
        fase_atual = FaseKanban(card["fase"])
        
        # Valida subfase
        subfases_validas = SUBFASES_POR_FASE.get(fase_atual, [])
        if subfase not in subfases_validas:
            raise ValidationError(
                f"Subfase '{subfase}' inválida para fase {fase_atual.name}. "
                f"Válidas: {subfases_validas}"
            )
        
        result = await db.update(
            table="cards",
            data={
                "subfase": subfase,
                "updated_at": datetime.utcnow().isoformat()
            },
            filters={"id": card_id}
        )
        
        return result

    async def listar_cards_kanban(
        self,
        current_user: CurrentUser,
        fase: Optional[int] = None,
        data: Optional[str] = None,
        medico_id: Optional[str] = None
    ) -> dict:
        """
        Lista cards agrupados por fase para exibição no Kanban.
        
        Returns:
            {
                "fases": {
                    0: {"nome": "Agendado", "cards": [...]},
                    1: {"nome": "Pré-Consulta", "cards": [...]},
                    ...
                },
                "totais": {"0": 5, "1": 3, ...}
            }
        """
        db = get_authenticated_db(current_user.access_token)
        
        filters = {"clinica_id": current_user.clinica_id, "status": "ativo"}
        
        if fase is not None:
            filters["fase"] = fase
        if medico_id:
            filters["medico_id"] = medico_id
        
        # Busca todos os cards
        cards = await db.select(
            table="cards",
            filters=filters,
            order_by="updated_at",
            order_asc=False
        )
        
        # Se filtro por data, filtra pelo agendamento
        if data:
            agendamento_ids = [c["agendamento_id"] for c in cards]
            agendamentos = await db.select(
                table="agendamentos",
                filters={"id__in": agendamento_ids, "data": data}
            )
            agendamento_ids_filtrados = {a["id"] for a in agendamentos}
            cards = [c for c in cards if c["agendamento_id"] in agendamento_ids_filtrados]
        
        # Agrupa por fase
        fases_result = {}
        totais = {}
        
        for f in FaseKanban:
            if f == FaseKanban.FINALIZADO:
                continue  # Não mostra finalizados no Kanban principal
            
            cards_fase = [c for c in cards if c["fase"] == f.value]
            fases_result[f.value] = {
                "nome": self._get_nome_fase(f),
                "subfases": SUBFASES_POR_FASE.get(f, []),
                "cards": cards_fase
            }
            totais[str(f.value)] = len(cards_fase)
        
        return {
            "fases": fases_result,
            "totais": totais
        }

    def _criar_checklist_fase(self, fase: FaseKanban) -> dict:
        """Cria checklist zerado para uma fase."""
        config = CHECKLIST_POR_FASE.get(fase, {"obrigatorios": [], "opcionais": []})
        
        checklist = {}
        
        for item in config["obrigatorios"]:
            checklist[item["key"]] = {
                "label": item["label"],
                "obrigatorio": True,
                "auto": item.get("auto", False),
                "concluido": False,
                "concluido_em": None,
                "concluido_por": None
            }
        
        for item in config["opcionais"]:
            checklist[item["key"]] = {
                "label": item["label"],
                "obrigatorio": False,
                "auto": item.get("auto", False),
                "concluido": False,
                "concluido_em": None,
                "concluido_por": None
            }
        
        return checklist

    def _verificar_transicao_fase(
        self,
        fase_atual: FaseKanban,
        checklist: dict
    ) -> Optional[int]:
        """
        Verifica se todos os itens obrigatórios estão completos.
        Se sim, retorna a próxima fase.
        """
        config = CHECKLIST_POR_FASE.get(fase_atual, {"obrigatorios": []})
        
        # Verifica se todos os obrigatórios estão concluídos
        for item in config["obrigatorios"]:
            item_key = item["key"]
            item_data = checklist.get(item_key, {})
            
            if isinstance(item_data, dict):
                concluido = item_data.get("concluido", False)
            else:
                concluido = bool(item_data)
            
            if not concluido:
                return None  # Ainda tem pendência
        
        # Todos concluídos - retorna próxima fase
        proxima = fase_atual.value + 1
        
        if proxima <= FaseKanban.FINALIZADO.value:
            return proxima
        
        return None

    def _get_nome_fase(self, fase: FaseKanban) -> str:
        """Retorna nome amigável da fase."""
        nomes = {
            FaseKanban.AGENDADO: "Agendado",
            FaseKanban.PRE_CONSULTA: "Pré-Consulta",
            FaseKanban.DIA_CONSULTA: "Dia da Consulta",
            FaseKanban.POS_CONSULTA: "Pós-Consulta",
            FaseKanban.FINALIZADO: "Finalizado"
        }
        return nomes.get(fase, f"Fase {fase.value}")

    async def _on_mudanca_fase(
        self,
        card_id: str,
        fase_anterior: FaseKanban,
        fase_nova: FaseKanban,
        current_user: CurrentUser
    ):
        """
        Callback executado quando card muda de fase.
        Dispara eventos/notificações necessários.
        """
        db = get_authenticated_db(current_user.access_token)
        
        # Busca card com dados relacionados
        card = await self.get_card(card_id, current_user)
        
        # Log da transição
        await db.insert(
            table="card_eventos",
            data={
                "card_id": card_id,
                "tipo": "mudanca_fase",
                "fase_anterior": fase_anterior.value,
                "fase_nova": fase_nova.value,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # Ações específicas por transição
        if fase_nova == FaseKanban.PRE_CONSULTA:
            # Disparar workflow de anamnese
            pass
        
        elif fase_nova == FaseKanban.DIA_CONSULTA:
            # Card entrou no dia da consulta
            pass
        
        elif fase_nova == FaseKanban.POS_CONSULTA:
            # Consulta finalizada, disparar SOAP
            pass
        
        elif fase_nova == FaseKanban.FINALIZADO:
            # Arquivar card
            await db.update(
                table="cards",
                data={
                    "status": "arquivado",
                    "arquivado_em": datetime.utcnow().isoformat()
                },
                filters={"id": card_id}
            )


# Instância global
kanban_service = KanbanService()
