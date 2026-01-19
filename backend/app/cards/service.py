"""
Cards - Service
Lógica de negócio para cards do Kanban.

ESTRUTURA:
- 4 Fases = 4 Colunas
- Checklist por fase (carregado de checklist_templates)
- Movimento automático quando checklist completo
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

import structlog

from app.core.database import get_authenticated_db, SupabaseClient
from app.core.exceptions import NotFoundError
from app.core.security import CurrentUser
from app.cards.schemas import (
    CardCreate,
    CardCreateRetorno,
    CardFase,
    CardKanban,
    CardListItem,
    CardMoverFase,
    CardResponse,
    CardStatus,
    CardTipo,
    CardUpdate,
    CardVincularAgendamento,
    ChecklistItem,
    ChecklistResumo,
    CardDocumentoCreate,
    FASES,
)

logger = structlog.get_logger()


def now_brasilia() -> datetime:
    """Retorna datetime atual no fuso de Brasília."""
    from datetime import timezone
    return datetime.now(timezone.utc)


def today_brasilia() -> date:
    """Retorna data atual no fuso de Brasília."""
    return now_brasilia().date()


class CardService:
    """Service para operações de cards."""

    TABLE = "cards"
    TABLE_CHECKLIST = "cards_checklist"
    TABLE_HISTORICO = "cards_historico"
    TABLE_TEMPLATES = "checklist_templates"

    # ==========================================
    # KANBAN - Visualização
    # ==========================================

    async def get_kanban(
        self,
        current_user: CurrentUser,
        fase: int,
        data: Optional[date] = None,
        medico_id: Optional[str] = None
    ) -> CardKanban:
        """Retorna cards de uma fase para o Kanban."""
        db = get_authenticated_db(current_user.access_token)

        # Monta filtros
        filters = {"fase": fase, "status": "ativo"}
        if medico_id:
            filters["medico_id"] = medico_id
        if data and fase == 2:  # Fase 2 filtra por data
            filters["data_agendamento"] = str(data)

        # Busca cards
        result = await db.select(
            table=self.TABLE,
            filters=filters,
            order_by="ultima_interacao" if fase == 0 else "hora_agendamento",
            order_asc=True if fase == 2 else False
        )

        cards = []
        em_reativacao = 0
        aguardando_confirmacao = 0

        for row in result or []:
            # Busca resumo do checklist
            checklist = await self._get_checklist_resumo(db, row["id"], fase)

            card = CardListItem(
                id=row["id"],
                paciente_nome=row.get("paciente_nome"),
                paciente_telefone=row.get("paciente_telefone"),
                tipo_card=row.get("tipo_card", "primeira_consulta"),
                fase=row.get("fase", 0),
                status=row.get("status", "ativo"),
                prioridade=row.get("prioridade", "normal"),
                cor_alerta=row.get("cor_alerta"),
                data_agendamento=row.get("data_agendamento"),
                hora_agendamento=row.get("hora_agendamento"),
                medico_id=row.get("medico_id"),
                intencao_inicial=row.get("intencao_inicial"),
                em_reativacao=row.get("em_reativacao", False),
                tentativa_reativacao=row.get("tentativa_reativacao", 0),
                ultima_interacao=row.get("ultima_interacao"),
                checklist_total=checklist.total,
                checklist_concluidos=checklist.concluidos,
                checklist_pode_avancar=checklist.pode_avancar,
            )
            cards.append(card)

            # Contadores
            if row.get("em_reativacao"):
                em_reativacao += 1

        fase_info = FASES.get(fase, {"nome": f"Fase {fase}"})

        return CardKanban(
            fase=fase,
            fase_nome=fase_info["nome"],
            cards=cards,
            total=len(cards),
            em_reativacao=em_reativacao,
            aguardando_confirmacao=aguardando_confirmacao,
        )

    async def get_kanban_completo(
        self,
        current_user: CurrentUser,
        data: Optional[date] = None,
        medico_id: Optional[str] = None
    ) -> list[CardKanban]:
        """Retorna todas as 4 fases do Kanban."""
        resultado = []
        for fase in range(4):
            kanban = await self.get_kanban(current_user, fase, data, medico_id)
            resultado.append(kanban)
        return resultado

    # ==========================================
    # CRUD
    # ==========================================

    async def get(self, id: str, current_user: CurrentUser) -> CardResponse:
        """Busca card por ID."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": id})
        if not card:
            raise NotFoundError("Card", id)

        # Busca checklist
        checklist = await self._get_checklist_resumo(db, id, card.get("fase", 0))

        # Remove checklist do dict se existir para evitar conflito
        card_data = {k: v for k, v in card.items() if k != 'checklist'}
        return CardResponse(**card_data, checklist=checklist)

    async def get_by_paciente(
        self,
        paciente_id: str,
        current_user: CurrentUser,
        apenas_ativo: bool = True
    ) -> Optional[CardResponse]:
        """Busca card ativo do paciente."""
        db = get_authenticated_db(current_user.access_token)

        filters = {"paciente_id": paciente_id}
        if apenas_ativo:
            filters["status"] = "ativo"

        card = await db.select_one(
            table=self.TABLE,
            filters=filters,
            order_by="created_at",
            order_asc=False
        )

        if not card:
            return None

        checklist = await self._get_checklist_resumo(db, card["id"], card.get("fase", 0))
        # Remove checklist do dict se existir para evitar conflito
        card_data = {k: v for k, v in card.items() if k != 'checklist'}
        return CardResponse(**card_data, checklist=checklist)

    async def create(
        self,
        data: CardCreate,
        current_user: CurrentUser
    ) -> CardResponse:
        """Cria card novo (Fase 0)."""
        db = get_authenticated_db(current_user.access_token)

        # Verifica se já existe card ativo para o telefone
        existente = await db.select_one(
            table=self.TABLE,
            filters={
                "paciente_telefone": data.paciente_telefone,
                "status": "ativo"
            }
        )

        if existente:
            # Atualiza última interação e retorna
            await db.update(
                table=self.TABLE,
                data={"ultima_interacao": now_brasilia().isoformat()},
                filters={"id": existente["id"]}
            )
            checklist = await self._get_checklist_resumo(db, existente["id"], 0)
            return CardResponse(**existente, checklist=checklist)

        # Cria card
        agora = now_brasilia()
        card_data = {
            "clinica_id": current_user.clinica_id,
            "paciente_id": str(data.paciente_id) if data.paciente_id else None,
            "paciente_nome": data.paciente_nome,
            "paciente_telefone": data.paciente_telefone,
            "tipo_card": data.tipo_card.value,
            "fase": CardFase.PRE_AGENDAMENTO.value,
            "status": CardStatus.ATIVO.value,
            "prioridade": "normal",
            "origem": data.origem,
            "intencao_inicial": data.intencao_inicial.value if data.intencao_inicial else None,
            "ultima_interacao": agora.isoformat(),
            "em_reativacao": False,
            "tentativa_reativacao": 0,
            "fase0_em": agora.isoformat(),
            "created_at": agora.isoformat(),
            "updated_at": agora.isoformat(),
        }

        card = await db.insert(self.TABLE, card_data)

        # Cria checklist da Fase 0
        await self._criar_checklist(db, card["id"], current_user.clinica_id, 0, data.tipo_card.value)

        # Registra histórico
        await self._registrar_historico(
            db, card["id"], "criacao",
            f"Card criado via {data.origem}",
            dados_novos={"fase": 0, "tipo": data.tipo_card.value},
            automatico=True
        )

        logger.info("Card criado", id=card["id"])

        checklist = await self._get_checklist_resumo(db, card["id"], 0)
        # Remove checklist do dict se existir para evitar conflito
        card_data = {k: v for k, v in card.items() if k != 'checklist'}
        return CardResponse(**card_data, checklist=checklist)

    async def create_retorno(
        self,
        data: CardCreateRetorno,
        current_user: CurrentUser
    ) -> CardResponse:
        """Cria card de retorno (derivado)."""
        db = get_authenticated_db(current_user.access_token)

        # Busca card origem
        card_origem = await db.select_one(
            table=self.TABLE,
            filters={"id": str(data.card_origem_id)}
        )
        if not card_origem:
            raise NotFoundError("Card origem", str(data.card_origem_id))

        # Busca paciente
        paciente = await db.select_one(
            table="pacientes",
            filters={"id": str(data.paciente_id)}
        )

        agora = now_brasilia()
        card_data = {
            "clinica_id": current_user.clinica_id,
            "paciente_id": str(data.paciente_id),
            "paciente_nome": paciente.get("nome") if paciente else card_origem.get("paciente_nome"),
            "paciente_telefone": paciente.get("celular") if paciente else card_origem.get("paciente_telefone"),
            "tipo_card": CardTipo.RETORNO.value,
            "fase": CardFase.PRE_AGENDAMENTO.value,
            "status": CardStatus.ATIVO.value,
            "prioridade": "normal",
            "origem": "retorno",
            "is_derivado": True,
            "card_origem_id": str(data.card_origem_id),
            "ultima_interacao": agora.isoformat(),
            "fase0_em": agora.isoformat(),
            "created_at": agora.isoformat(),
            "updated_at": agora.isoformat(),
        }

        card = await db.insert(self.TABLE, card_data)

        # Atualiza card origem com referência ao derivado
        await db.update(
            table=self.TABLE,
            data={"card_derivado_id": card["id"]},
            filters={"id": str(data.card_origem_id)}
        )

        # Cria checklist de retorno
        await self._criar_checklist(db, card["id"], current_user.clinica_id, 0, CardTipo.RETORNO.value)

        logger.info("Card retorno criado", id=card["id"], origem=str(data.card_origem_id))

        checklist = await self._get_checklist_resumo(db, card["id"], 0)
        # Remove checklist do dict se existir para evitar conflito
        card_data = {k: v for k, v in card.items() if k != 'checklist'}
        return CardResponse(**card_data, checklist=checklist)

    async def update(
        self,
        id: str,
        data: CardUpdate,
        current_user: CurrentUser
    ) -> CardResponse:
        """Atualiza dados do card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": id})
        if not card:
            raise NotFoundError("Card", id)

        update_data = {}
        if data.prioridade:
            update_data["prioridade"] = data.prioridade.value
        if data.cor_alerta is not None:
            update_data["cor_alerta"] = data.cor_alerta
        if data.observacoes is not None:
            update_data["observacoes"] = data.observacoes
        if data.intencao_inicial:
            update_data["intencao_inicial"] = data.intencao_inicial.value
        if data.motivo_saida:
            update_data["motivo_saida"] = data.motivo_saida.value

        if update_data:
            update_data["updated_at"] = now_brasilia().isoformat()
            await db.update(table=self.TABLE, data=update_data, filters={"id": id})

        return await self.get(id, current_user)

    # ==========================================
    # MOVIMENTAÇÃO ENTRE FASES
    # ==========================================

    async def mover_fase(
        self,
        id: str,
        data: CardMoverFase,
        current_user: CurrentUser
    ) -> CardResponse:
        """Move card para outra fase."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": id})
        if not card:
            raise NotFoundError("Card", id)

        fase_atual = card.get("fase", 0)
        nova_fase = data.nova_fase.value

        # Valida se pode mover (checklist obrigatório completo)
        if nova_fase > fase_atual:
            checklist = await self._get_checklist_resumo(db, id, fase_atual)
            if not checklist.pode_avancar:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Não é possível avançar. Há {checklist.obrigatorios_pendentes} itens obrigatórios pendentes."
                )

        # Atualiza card
        agora = now_brasilia()
        update_data = {
            "fase": nova_fase,
            "updated_at": agora.isoformat(),
            "ultima_interacao": agora.isoformat(),
            f"fase{nova_fase}_em": agora.isoformat(),
        }

        # Se voltou para Fase 0, marca como reativação
        if nova_fase == 0 and fase_atual > 0:
            update_data["em_reativacao"] = True
            tentativa = card.get("tentativa_reativacao", 0) + 1
            update_data["tentativa_reativacao"] = tentativa

        # Se concluiu (saiu da Fase 3)
        if fase_atual == 3 and nova_fase == 3:
            update_data["status"] = CardStatus.CONCLUIDO.value
            update_data["concluido_em"] = agora.isoformat()

        await db.update(table=self.TABLE, data=update_data, filters={"id": id})

        # Cria checklist da nova fase (se avançou)
        if nova_fase > fase_atual:
            tipo_card = card.get("tipo_card", "primeira_consulta")
            await self._criar_checklist(db, id, current_user.clinica_id, nova_fase, tipo_card)

        # Registra histórico
        await self._registrar_historico(
            db, id, "movimentacao",
            f"Card movido da Fase {fase_atual} para Fase {nova_fase}",
            dados_anteriores={"fase": fase_atual},
            dados_novos={"fase": nova_fase},
            user_id=current_user.id
        )

        logger.info("Card movido", id=id, fase_anterior=fase_atual, nova_fase=nova_fase)
        return await self.get(id, current_user)

    async def vincular_agendamento(
        self,
        id: str,
        data: CardVincularAgendamento,
        current_user: CurrentUser
    ) -> CardResponse:
        """Vincula agendamento ao card e move para Fase 1."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": id})
        if not card:
            raise NotFoundError("Card", id)

        agora = now_brasilia()
        update_data = {
            "agendamento_id": str(data.agendamento_id),
            "medico_id": str(data.medico_id),
            "data_agendamento": str(data.data_agendamento),
            "hora_agendamento": data.hora_agendamento,
            "fase": CardFase.PRE_CONSULTA.value,
            "fase1_em": agora.isoformat(),
            "updated_at": agora.isoformat(),
            "ultima_interacao": agora.isoformat(),
            "em_reativacao": False,
        }

        await db.update(table=self.TABLE, data=update_data, filters={"id": id})

        # Marca item "consulta_agendada" como concluído
        await self._marcar_checklist_item(db, id, 0, "consulta_agendada", "sistema")

        # Cria checklist da Fase 1
        tipo_card = card.get("tipo_card", "primeira_consulta")
        await self._criar_checklist(db, id, current_user.clinica_id, 1, tipo_card)

        # Registra histórico
        await self._registrar_historico(
            db, id, "agendamento",
            f"Consulta agendada para {data.data_agendamento} às {data.hora_agendamento}",
            dados_novos={"agendamento_id": str(data.agendamento_id)},
            automatico=True
        )

        logger.info("Agendamento vinculado", card_id=id, agendamento_id=str(data.agendamento_id))
        return await self.get(id, current_user)

    # ==========================================
    # CHECKLIST
    # ==========================================

    async def get_checklist(
        self,
        card_id: str,
        current_user: CurrentUser,
        fase: Optional[int] = None
    ) -> list[ChecklistItem]:
        """Retorna checklist do card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        filters = {"card_id": card_id}
        if fase is not None:
            filters["fase"] = fase

        items = await db.select(
            table=self.TABLE_CHECKLIST,
            filters=filters,
            order_by="fase,ordem"
        )

        return [ChecklistItem(**item) for item in items or []]

    async def marcar_checklist(
        self,
        card_id: str,
        item_id: str,
        concluido: bool,
        current_user: CurrentUser
    ) -> ChecklistItem:
        """Marca/desmarca item do checklist."""
        db = get_authenticated_db(current_user.access_token)

        # Verifica card
        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        # Verifica item
        item = await db.select_one(
            table=self.TABLE_CHECKLIST,
            filters={"id": item_id, "card_id": card_id}
        )
        if not item:
            raise NotFoundError("Item do checklist", item_id)

        # Atualiza
        agora = now_brasilia()
        update_data = {
            "concluido": concluido,
            "concluido_em": agora.isoformat() if concluido else None,
            "concluido_por": current_user.id if concluido else None,
        }

        await db.update(
            table=self.TABLE_CHECKLIST,
            data=update_data,
            filters={"id": item_id}
        )

        # Atualiza última interação do card
        await db.update(
            table=self.TABLE,
            data={"ultima_interacao": agora.isoformat()},
            filters={"id": card_id}
        )

        updated = await db.select_one(
            table=self.TABLE_CHECKLIST,
            filters={"id": item_id}
        )
        return ChecklistItem(**updated)

    async def _criar_checklist(
        self,
        db: SupabaseClient,
        card_id: str,
        clinica_id: str,
        fase: int,
        tipo_card: str
    ):
        """Cria checklist para o card baseado nos templates."""
        # Busca templates (prioriza da clínica, depois global)
        templates = await db.select(
            table=self.TABLE_TEMPLATES,
            filters={"fase": fase, "tipo_card": tipo_card, "ativo": True},
            order_by="ordem"
        )

        # Filtra: se tem da clínica usa, senão usa global
        templates_clinica = [t for t in templates or [] if t.get("clinica_id") == clinica_id]
        templates_global = [t for t in templates or [] if t.get("clinica_id") is None]

        templates_usar = templates_clinica if templates_clinica else templates_global

        for t in templates_usar:
            # Verifica se já existe
            existente = await db.select_one(
                table=self.TABLE_CHECKLIST,
                filters={"card_id": card_id, "fase": fase, "item_key": t["item_key"]}
            )

            if not existente:
                await db.insert(self.TABLE_CHECKLIST, {
                    "card_id": card_id,
                    "fase": fase,
                    "item_key": t["item_key"],
                    "descricao": t["descricao"],
                    "obrigatorio": t["obrigatorio"],
                    "ordem": t["ordem"],
                })

    async def _get_checklist_resumo(
        self,
        db: SupabaseClient,
        card_id: str,
        fase: int
    ) -> ChecklistResumo:
        """Retorna resumo do checklist de uma fase."""
        items = await db.select(
            table=self.TABLE_CHECKLIST,
            filters={"card_id": card_id, "fase": fase}
        )

        total = len(items or [])
        concluidos = sum(1 for i in items or [] if i.get("concluido"))
        obrigatorios_pendentes = sum(
            1 for i in items or []
            if i.get("obrigatorio") and not i.get("concluido")
        )

        return ChecklistResumo(
            total=total,
            concluidos=concluidos,
            obrigatorios_pendentes=obrigatorios_pendentes,
        )

    async def _marcar_checklist_item(
        self,
        db: SupabaseClient,
        card_id: str,
        fase: int,
        item_key: str,
        concluido_por: str
    ):
        """Marca item específico do checklist como concluído."""
        item = await db.select_one(
            table=self.TABLE_CHECKLIST,
            filters={"card_id": card_id, "fase": fase, "item_key": item_key}
        )

        if item:
            await db.update(
                table=self.TABLE_CHECKLIST,
                data={
                    "concluido": True,
                    "concluido_em": now_brasilia().isoformat(),
                    "concluido_por": concluido_por,
                },
                filters={"id": item["id"]}
            )

    # ==========================================
    # HISTÓRICO
    # ==========================================

    async def get_historico(
        self,
        card_id: str,
        current_user: CurrentUser
    ) -> list[dict]:
        """Retorna histórico do card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        return await db.select(
            table=self.TABLE_HISTORICO,
            filters={"card_id": card_id},
            order_by="created_at",
            order_asc=False
        ) or []

    async def _registrar_historico(
        self,
        db: SupabaseClient,
        card_id: str,
        tipo: str,
        descricao: str,
        dados_anteriores: Optional[dict] = None,
        dados_novos: Optional[dict] = None,
        user_id: Optional[str] = None,
        automatico: bool = False
    ):
        """Registra evento no histórico."""
        await db.insert(self.TABLE_HISTORICO, {
            "card_id": card_id,
            "tipo": tipo,
            "descricao": descricao,
            "dados_anteriores": dados_anteriores,
            "dados_novos": dados_novos,
            "user_id": user_id,
            "automatico": automatico,
        })

    # ==========================================
    # DOCUMENTOS
    # ==========================================

    async def get_documentos(
        self,
        card_id: str,
        current_user: CurrentUser
    ) -> list[dict]:
        """Retorna documentos do card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        return await db.select(
            table="cards_documentos",
            filters={"card_id": card_id},
            order_by="created_at",
            order_asc=False
        ) or []

    async def add_documento(
        self,
        card_id: str,
        data: CardDocumentoCreate,
        current_user: CurrentUser
    ) -> dict:
        """Adiciona documento ao card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        doc = await db.insert("cards_documentos", {
            "card_id": card_id,
            **data.model_dump(exclude_none=True),
            "uploaded_by_user": current_user.id,
        })

        return doc

    # ==========================================
    # MENSAGENS
    # ==========================================

    async def get_mensagens(
        self,
        card_id: str,
        current_user: CurrentUser
    ) -> list[dict]:
        """Retorna mensagens do card."""
        db = get_authenticated_db(current_user.access_token)

        card = await db.select_one(table=self.TABLE, filters={"id": card_id})
        if not card:
            raise NotFoundError("Card", card_id)

        return await db.select(
            table="cards_mensagens",
            filters={"card_id": card_id},
            order_by="created_at",
            order_asc=False
        ) or []


# Singleton
card_service = CardService()
