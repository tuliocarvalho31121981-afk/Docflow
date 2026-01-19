"""
Agenda - Service
Lógica de negócio para agendamentos.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- RLS filtra automaticamente por clinica_id
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID

import structlog

from app.core.database import get_authenticated_db, SupabaseClient
from app.core.exceptions import (
    InvalidStatusTransitionError,
    NotFoundError,
    SlotUnavailableError,
    ValidationError,
)
from app.core.security import CurrentUser
from app.core.utils import now_brasilia, today_brasilia
from app.agenda.schemas import (
    AgendamentoCreate,
    AgendamentoResponse,
    AgendamentoStatusUpdate,
    AgendamentoUpdate,
    SlotDisponivel,
)

logger = structlog.get_logger()


class AgendaService:
    """Service para operações de agenda."""

    TABLE = "agendamentos"

    # Status válidos e transições permitidas
    STATUS_TRANSITIONS = {
        "agendado": ["confirmado", "cancelado", "remarcado"],
        "confirmado": ["aguardando", "faltou", "cancelado", "remarcado"],
        "aguardando": ["em_atendimento", "faltou", "cancelado"],
        "em_atendimento": ["atendido"],
        "atendido": [],
        "faltou": [],
        "cancelado": [],
        "remarcado": [],
    }

    # ==========================================
    # LISTAGEM
    # ==========================================

    async def list(
        self,
        current_user: CurrentUser,
        data: Optional[date] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        medico_id: Optional[str] = None,
        paciente_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """
        Lista agendamentos com filtros e paginação.
        RLS garante isolamento por clínica.
        """
        logger.info(
            "Listando agendamentos",
            clinica_id=current_user.clinica_id,
            data=data,
            page=page
        )

        db = get_authenticated_db(current_user.access_token)

        # Monta filtros
        filters = {}

        if medico_id:
            filters["medico_id"] = medico_id
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if status:
            filters["status"] = status

        # OTIMIZADO: Filtros de data direto no SQL (não mais em Python)
        if data:
            filters["data"] = str(data)
        else:
            if data_inicio:
                filters["data__gte"] = str(data_inicio)
            if data_fim:
                filters["data__lte"] = str(data_fim)

        # Paginação
        return await db.paginate(
            table=self.TABLE,
            filters=filters if filters else None,
            order_by="data,hora_inicio",
            page=page,
            per_page=per_page
        )

    # ==========================================
    # MÉTRICAS
    # ==========================================

    async def get_metricas(
        self,
        current_user: CurrentUser,
        data: Optional[date] = None
    ) -> dict:
        """
        Retorna métricas da agenda para uma data.
        """
        if data is None:
            data = today_brasilia()

        logger.info(
            "Calculando métricas da agenda",
            clinica_id=current_user.clinica_id,
            data=data
        )

        db = get_authenticated_db(current_user.access_token)

        # Busca todos agendamentos do dia
        agendamentos = await db.select(
            table=self.TABLE,
            filters={"data": str(data)}
        )

        # Calcula métricas
        total = len(agendamentos)
        por_status = {}
        for ag in agendamentos:
            s = ag.get("status", "agendado")
            por_status[s] = por_status.get(s, 0) + 1

        agendados = por_status.get("agendado", 0)
        confirmados = por_status.get("confirmado", 0)
        aguardando = por_status.get("aguardando", 0)
        em_atendimento = por_status.get("em_atendimento", 0)
        atendidos = por_status.get("atendido", 0)
        faltas = por_status.get("faltou", 0)
        cancelados = por_status.get("cancelado", 0)

        # Taxas
        total_finalizados = atendidos + faltas
        taxa_confirmacao = (confirmados + aguardando + em_atendimento + atendidos) / total * 100 if total > 0 else 0
        taxa_comparecimento = atendidos / total_finalizados * 100 if total_finalizados > 0 else 0

        # Calcula slots disponíveis usando horarios_disponiveis
        # Busca horários configurados para a data (dia da semana)
        dia_semana = data.weekday()
        dia_semana_schema = (dia_semana + 1) % 7  # Ajuste para schema (0=domingo, 1=segunda...)

        horarios_template = await db.select(
            table="horarios_disponiveis",
            filters={"ativo": True, "dia_semana": dia_semana_schema}
        )

        total_slots = 0
        if horarios_template:
            # Calcula total de slots baseado nos horários configurados
            for h in horarios_template:
                hora_inicio = datetime.strptime(str(h["hora_inicio"]), "%H:%M:%S").time()
                hora_fim = datetime.strptime(str(h["hora_fim"]), "%H:%M:%S").time()
                intervalo = timedelta(minutes=h.get("intervalo_minutos", 30))

                current = datetime.combine(data, hora_inicio)
                fim = datetime.combine(data, hora_fim)
                count = 0
                while current < fim:
                    count += 1
                    current += intervalo
                total_slots += count * h.get("vagas_por_horario", 1)
        else:
            # Fallback: assume 20 slots se não houver configuração
            total_slots = 20

        horarios_ocupados = total - cancelados
        horarios_disponiveis = max(0, total_slots - horarios_ocupados)
        taxa_ocupacao = (horarios_ocupados / total_slots * 100) if total_slots > 0 else 0

        return {
            "data": str(data),
            "total_agendados": total,
            "total_confirmados": confirmados,
            "total_aguardando_confirmacao": agendados,
            "total_aguardando": aguardando,
            "total_em_atendimento": em_atendimento,
            "total_atendidos": atendidos,
            "total_faltas": faltas,
            "total_cancelados": cancelados,
            "taxa_confirmacao": round(taxa_confirmacao, 1),
            "taxa_comparecimento": round(taxa_comparecimento, 1),
            "horarios_disponiveis": horarios_disponiveis,
            "horarios_ocupados": horarios_ocupados,
            "taxa_ocupacao": round(taxa_ocupacao, 1),
            "por_status": por_status
        }

    # ==========================================
    # BLOQUEIOS
    # ==========================================

    async def list_bloqueios(
        self,
        current_user: CurrentUser,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> list[dict]:
        """
        Lista bloqueios de agenda no período.
        """
        if data_inicio is None:
            data_inicio = today_brasilia()
        if data_fim is None:
            data_fim = data_inicio + timedelta(days=30)

        logger.info(
            "Listando bloqueios",
            clinica_id=current_user.clinica_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        db = get_authenticated_db(current_user.access_token)

        bloqueios = await db.select(
            table="agenda_bloqueios",
            filters={"ativo": True},
            order_by="data"
        )

        # Filtra por período
        resultado = []
        for b in bloqueios:
            b_data = b.get("data")
            if isinstance(b_data, str):
                b_data = date.fromisoformat(b_data)

            # Bloqueio único
            if not b.get("recorrente", False):
                if data_inicio <= b_data <= data_fim:
                    resultado.append(b)
            # Bloqueio recorrente
            else:
                if b_data <= data_fim:
                    rec_fim = b.get("recorrencia_fim")
                    if rec_fim:
                        if isinstance(rec_fim, str):
                            rec_fim = date.fromisoformat(rec_fim)
                        if rec_fim >= data_inicio:
                            resultado.append(b)
                    else:
                        resultado.append(b)

        return resultado

    # ==========================================
    # SLOTS DISPONÍVEIS
    # ==========================================

    async def get_slots_disponiveis(
        self,
        current_user: CurrentUser,
        data_inicio: date,
        data_fim: Optional[date] = None,
        medico_id: Optional[str] = None,
        tipo_consulta_id: Optional[str] = None
    ) -> list[SlotDisponivel]:
        """Retorna slots disponíveis para agendamento."""
        logger.info(
            "Buscando slots disponíveis",
            clinica_id=current_user.clinica_id,
            data_inicio=data_inicio
        )

        db = get_authenticated_db(current_user.access_token)

        if data_fim is None:
            data_fim = data_inicio

        if data_inicio < today_brasilia():
            raise ValidationError("Data não pode ser no passado")

        # Busca duração do tipo de consulta
        duracao = 30
        if tipo_consulta_id:
            tipo = await db.select_one(
                table="tipos_consulta",
                filters={"id": tipo_consulta_id}
            )
            if tipo:
                duracao = tipo.get("duracao_minutos", 30)

        # Busca templates de horários
        filters = {"ativo": True}
        if medico_id:
            filters["medico_id"] = medico_id

        horarios_template = await db.select(
            table="horarios_disponiveis",
            filters=filters
        )

        if not horarios_template:
            return []

        # OTIMIZAÇÃO: Carrega TODOS os médicos de uma vez (evita N+1)
        medicos_ids = list(set(h["medico_id"] for h in horarios_template))
        medicos_cache = await self._carregar_medicos_batch(db, medicos_ids)

        # Busca agendamentos e bloqueios existentes (já otimizado)
        agendamentos = await self._get_agendamentos_periodo(db, data_inicio, data_fim, medico_id)
        bloqueios = await self._get_bloqueios_periodo(db, data_inicio, data_fim, medico_id)

        # Gera slots
        slots = []
        current_date = data_inicio

        while current_date <= data_fim:
            dia_semana = current_date.weekday()
            dia_semana_schema = (dia_semana + 1) % 7

            for horario in horarios_template:
                if horario["dia_semana"] != dia_semana_schema:
                    continue

                hora_atual = datetime.strptime(str(horario["hora_inicio"]), "%H:%M:%S").time()
                hora_fim_periodo = datetime.strptime(str(horario["hora_fim"]), "%H:%M:%S").time()
                intervalo = timedelta(minutes=horario.get("intervalo_minutos", duracao))

                med_id = horario["medico_id"]
                medico_nome = medicos_cache.get(med_id, "Médico")

                while hora_atual < hora_fim_periodo:
                    slot_fim = (datetime.combine(current_date, hora_atual) + timedelta(minutes=duracao)).time()

                    disponivel = self._is_slot_disponivel(
                        current_date, hora_atual, slot_fim,
                        med_id, agendamentos, bloqueios
                    )

                    slots.append(SlotDisponivel(
                        data=current_date,
                        hora_inicio=hora_atual,
                        hora_fim=slot_fim,
                        medico_id=med_id,
                        medico_nome=medico_nome,
                        disponivel=disponivel
                    ))

                    hora_atual = (datetime.combine(current_date, hora_atual) + intervalo).time()

            current_date += timedelta(days=1)

        return slots

    async def _carregar_medicos_batch(
        self, db: SupabaseClient, medicos_ids: list[str]
    ) -> dict[str, str]:
        """Carrega nomes de múltiplos médicos em uma única query."""
        if not medicos_ids:
            return {}

        # Busca todos de uma vez
        medicos = await db.select(
            table="usuarios",
            columns="id, nome",
            filters=None  # Sem filtro, vamos filtrar manualmente
        )

        # Filtra e monta cache
        cache = {}
        for m in medicos:
            if str(m["id"]) in medicos_ids or m["id"] in medicos_ids:
                cache[m["id"]] = m.get("nome", "Médico")
                cache[str(m["id"])] = m.get("nome", "Médico")

        return cache

    async def _get_agendamentos_periodo(
        self, db: SupabaseClient, data_inicio: date, data_fim: date, medico_id: Optional[str] = None
    ) -> list[dict]:
        """Busca agendamentos existentes no período."""
        # OTIMIZADO: Filtra datas e status no SQL
        filters = {
            "data__gte": str(data_inicio),
            "data__lte": str(data_fim),
            "status__neq": "cancelado"  # Exclui cancelados
        }
        if medico_id:
            filters["medico_id"] = medico_id

        agendamentos = await db.select(table=self.TABLE, filters=filters)

        # Filtra remarcados (neq só suporta um valor)
        return [a for a in agendamentos if a.get("status") != "remarcado"]

    async def _get_bloqueios_periodo(
        self, db: SupabaseClient, data_inicio: date, data_fim: date, medico_id: Optional[str] = None
    ) -> list[dict]:
        """Busca bloqueios de agenda no período."""
        # OTIMIZADO: Filtros básicos no SQL
        # Bloqueios recorrentes precisam de lógica Python adicional
        filters = {
            "ativo": True,
            "data__lte": str(data_fim)  # Data do bloqueio deve ser <= data_fim
        }
        if medico_id:
            filters["medico_id"] = medico_id

        bloqueios = await db.select(table="agenda_bloqueios", filters=filters)

        resultado = []
        for b in bloqueios:
            b_data = b.get("data")
            if isinstance(b_data, str):
                b_data = date.fromisoformat(b_data)

            # Bloqueio único: verifica se está no período
            if not b.get("recorrente", False):
                if data_inicio <= b_data <= data_fim:
                    resultado.append(b)
            # Bloqueio recorrente: verifica se ainda está ativo no período
            else:
                rec_fim = b.get("recorrencia_fim")
                if rec_fim:
                    if isinstance(rec_fim, str):
                        rec_fim = date.fromisoformat(rec_fim)
                    if rec_fim >= data_inicio:
                        resultado.append(b)
                else:
                    # Sem fim definido, está ativo
                    resultado.append(b)

        return resultado

    def _is_slot_disponivel(
        self, data: date, hora_inicio: time, hora_fim: time,
        medico_id: str, agendamentos: list[dict], bloqueios: list[dict]
    ) -> bool:
        """Verifica se um slot está disponível."""
        # Verifica conflito com agendamentos
        for ag in agendamentos:
            if ag["medico_id"] == medico_id:
                ag_data = ag.get("data")
                if isinstance(ag_data, str):
                    ag_data = date.fromisoformat(ag_data)

                if ag_data == data:
                    ag_hora = ag["hora_inicio"]
                    if isinstance(ag_hora, str):
                        ag_hora = datetime.strptime(ag_hora, "%H:%M:%S").time()

                    ag_fim = ag.get("hora_fim")
                    if ag_fim:
                        if isinstance(ag_fim, str):
                            ag_fim = datetime.strptime(ag_fim, "%H:%M:%S").time()
                    else:
                        ag_fim = (datetime.combine(data, ag_hora) + timedelta(minutes=30)).time()

                    # Verifica sobreposição
                    if hora_inicio < ag_fim and hora_fim > ag_hora:
                        return False

        # Verifica conflito com bloqueios
        for bl in bloqueios:
            if bl.get("medico_id") == medico_id or bl.get("medico_id") is None:
                bl_data = bl.get("data")
                if isinstance(bl_data, str):
                    bl_data = date.fromisoformat(bl_data)

                # Bloqueio recorrente - verifica dia da semana
                if bl.get("recorrente"):
                    if bl.get("dia_semana") == data.weekday():
                        bl_hora = bl.get("hora_inicio")
                        bl_fim = bl.get("hora_fim")
                        if bl_hora and bl_fim:
                            if isinstance(bl_hora, str):
                                bl_hora = datetime.strptime(bl_hora, "%H:%M:%S").time()
                            if isinstance(bl_fim, str):
                                bl_fim = datetime.strptime(bl_fim, "%H:%M:%S").time()
                            if hora_inicio < bl_fim and hora_fim > bl_hora:
                                return False
                        else:
                            return False  # Bloqueio do dia inteiro
                # Bloqueio único
                elif bl_data == data:
                    bl_hora = bl.get("hora_inicio")
                    bl_fim = bl.get("hora_fim")
                    if bl_hora and bl_fim:
                        if isinstance(bl_hora, str):
                            bl_hora = datetime.strptime(bl_hora, "%H:%M:%S").time()
                        if isinstance(bl_fim, str):
                            bl_fim = datetime.strptime(bl_fim, "%H:%M:%S").time()
                        if hora_inicio < bl_fim and hora_fim > bl_hora:
                            return False
                    else:
                        return False  # Bloqueio do dia inteiro

        return True

    # ==========================================
    # INTEGRAÇÃO COM CARDS
    # ==========================================

    async def _integrar_com_cards(
        self,
        db: SupabaseClient,
        agendamento_id: str,
        paciente_id: str,
        medico_id: str,
        data_agendamento: date,
        hora_agendamento: str,
        clinica_id: str
    ) -> Optional[str]:
        """
        Integra agendamento com Cards:
        - Se existe card ativo na Fase 0 → vincula e move para Fase 1
        - Se não existe → cria card novo na Fase 1
        """
        agora = now_brasilia()

        # Busca card ativo na Fase 0 para o paciente
        card_fase0 = await db.select_one(
            table="cards",
            filters={
                "paciente_id": paciente_id,
                "fase": 0,
                "status": "ativo",
                "agendamento_id": None  # Sem agendamento vinculado
            },
            order_by="created_at",
            order_asc=False
        )

        if card_fase0:
            # Vincula agendamento ao card existente e move para Fase 1
            card_id = card_fase0["id"]
            update_data = {
                "agendamento_id": agendamento_id,
                "medico_id": medico_id,
                "data_agendamento": str(data_agendamento),
                "hora_agendamento": hora_agendamento,
                "fase": 1,  # PRE_CONSULTA
                "coluna": "pre_consulta",
                "fase1_em": agora.isoformat(),
                "updated_at": agora.isoformat(),
                "ultima_interacao": agora.isoformat(),
                "em_reativacao": False,
            }
            await db.update(table="cards", data=update_data, filters={"id": card_id})

            # Marca checklist item "consulta_agendada" como concluído (se existir)
            await self._marcar_checklist_card(db, card_id, 0, "consulta_agendada")

            # Cria checklist da Fase 1 (se não existir)
            tipo_card = card_fase0.get("tipo_card", "primeira_consulta")
            await self._criar_checklist_card(db, card_id, clinica_id, 1, tipo_card)

            logger.info("Card Fase 0 vinculado ao agendamento", card_id=card_id, agendamento_id=agendamento_id)
            return card_id
        else:
            # Cria card novo na Fase 1
            paciente = await db.select_one(table="pacientes", filters={"id": paciente_id})
            paciente_nome = paciente.get("nome", "") if paciente else ""
            paciente_telefone = paciente.get("telefone", "") if paciente else ""

            card_data = {
                "clinica_id": clinica_id,
                "agendamento_id": agendamento_id,
                "paciente_id": paciente_id,
                "medico_id": medico_id,
                "paciente_nome": paciente_nome,
                "paciente_telefone": paciente_telefone,
                "tipo_card": "primeira_consulta",
                "fase": 1,  # PRE_CONSULTA
                "coluna": "pre_consulta",
                "status": "ativo",
                "prioridade": "normal",
                "origem": "manual",
                "data_agendamento": str(data_agendamento),
                "hora_agendamento": hora_agendamento,
                "ultima_interacao": agora.isoformat(),
                "em_reativacao": False,
                "fase1_em": agora.isoformat(),
                "created_at": agora.isoformat(),
                "updated_at": agora.isoformat(),
            }

            card = await db.insert(table="cards", data=card_data)
            card_id = card["id"]

            # Cria checklist da Fase 1
            await self._criar_checklist_card(db, card_id, clinica_id, 1, "primeira_consulta")

            logger.info("Card criado para agendamento", card_id=card_id, agendamento_id=agendamento_id)
            return card_id

    async def _marcar_checklist_card(
        self,
        db: SupabaseClient,
        card_id: str,
        fase: int,
        item_key: str
    ) -> None:
        """Marca item do checklist como concluído."""
        try:
            # Busca item do checklist (usa item_key como no CardService)
            item = await db.select_one(
                table="cards_checklist",
                filters={
                    "card_id": card_id,
                    "fase": fase,
                    "item_key": item_key
                }
            )
            if item and not item.get("concluido"):
                await db.update(
                    table="cards_checklist",
                    data={
                        "concluido": True,
                        "concluido_em": now_brasilia().isoformat(),
                        "concluido_por_sistema": True
                    },
                    filters={"id": item["id"]}
                )
        except Exception as e:
            logger.warning("Erro ao marcar checklist", card_id=card_id, item_key=item_key, erro=str(e))

    async def _criar_checklist_card(
        self,
        db: SupabaseClient,
        card_id: str,
        clinica_id: str,
        fase: int,
        tipo_card: str
    ) -> None:
        """Cria checklist para o card se não existir."""
        try:
            # Verifica se já existe checklist para essa fase
            existente = await db.select_one(
                table="cards_checklist",
                filters={"card_id": card_id, "fase": fase}
            )
            if existente:
                return  # Já existe checklist

            # Busca template do checklist
            template = await db.select(
                table="checklist_templates",
                filters={"fase": fase, "tipo_card": tipo_card, "ativo": True},
                order_by="posicao"
            )

            if not template:
                return  # Sem template, não cria checklist

            # Cria itens do checklist
            for item in template:
                await db.insert(table="cards_checklist", data={
                    "card_id": card_id,
                    "fase": fase,
                    "item_key": item.get("item_key", ""),
                    "descricao": item.get("descricao", ""),
                    "tipo": item.get("tipo", "check"),
                    "obrigatorio": item.get("obrigatorio", False),
                    "ordem": item.get("ordem", item.get("posicao", 0)),
                    "concluido": False,
                    "created_at": now_brasilia().isoformat()
                })
        except Exception as e:
            logger.warning("Erro ao criar checklist", card_id=card_id, fase=fase, erro=str(e))

    async def _atualizar_card_por_status(
        self,
        db: SupabaseClient,
        agendamento_id: str,
        status: str
    ) -> None:
        """Atualiza card quando status do agendamento muda."""
        try:
            # Busca card vinculado
            card = await db.select_one(
                table="cards",
                filters={"agendamento_id": agendamento_id}
            )
            if not card:
                return

            card_id = card["id"]
            agora = now_brasilia()
            update_data = {"updated_at": agora.isoformat(), "ultima_interacao": agora.isoformat()}

            # Mapeamento de status do agendamento para ações no card
            if status == "confirmado":
                # Marca checklist "confirmacao" como concluído
                await self._marcar_checklist_card(db, card_id, 1, "confirmacao")
            elif status == "aguardando":
                # Move card para Fase 2 se ainda estiver na Fase 1
                if card.get("fase") == 1:
                    update_data.update({
                        "fase": 2,
                        "coluna": "aguardando_checkin",
                        "fase2_em": agora.isoformat()
                    })
                    await self._criar_checklist_card(db, card_id, card.get("clinica_id"), 2, card.get("tipo_card", "primeira_consulta"))
                # Marca checklist "checkin" como concluído
                await self._marcar_checklist_card(db, card_id, 2, "checkin")
            elif status == "em_atendimento":
                # Atualiza coluna
                if card.get("fase") == 2:
                    update_data["coluna"] = "em_atendimento"
                # Marca checklist "em_atendimento" como concluído
                await self._marcar_checklist_card(db, card_id, 2, "em_atendimento")
            elif status == "atendido":
                # Move card para Fase 3
                update_data.update({
                    "fase": 3,
                    "coluna": "pendente_documentos",
                    "fase3_em": agora.isoformat()
                })
                await self._criar_checklist_card(db, card_id, card.get("clinica_id"), 3, card.get("tipo_card", "primeira_consulta"))
            elif status in ("cancelado", "faltou"):
                # Move card de volta para Fase 0 (reativação)
                update_data.update({
                    "fase": 0,
                    "coluna": "pre_agendamento",
                    "agendamento_id": None,
                    "data_agendamento": None,
                    "hora_agendamento": None,
                    "em_reativacao": True,
                    "status": "ativo" if status == "cancelado" else "no_show"
                })

            if len(update_data) > 2:  # Mais que updated_at e ultima_interacao
                await db.update(table="cards", data=update_data, filters={"id": card_id})
                logger.info("Card atualizado por mudança de status", card_id=card_id, status=status)
        except Exception as e:
            logger.warning("Erro ao atualizar card por status", agendamento_id=agendamento_id, status=status, erro=str(e))

    # ==========================================
    # CRUD
    # ==========================================

    async def get(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Busca agendamento por ID."""
        db = get_authenticated_db(current_user.access_token)

        ag = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )

        if not ag:
            raise NotFoundError("Agendamento", id)

        # Busca dados relacionados
        paciente = await db.select_one(table="pacientes", filters={"id": ag["paciente_id"]})
        medico = await db.select_one(table="usuarios", filters={"id": ag["medico_id"]})
        tipo = await db.select_one(table="tipos_consulta", filters={"id": ag["tipo_consulta_id"]})

        convenio = None
        if ag.get("convenio_id"):
            convenio = await db.select_one(table="convenios", filters={"id": ag["convenio_id"]})

        # Busca card vinculado (via card_id no agendamento ou agendamento_id no card)
        card = None
        if ag.get("card_id"):
            card = await db.select_one(
                table="cards",
                filters={"id": ag["card_id"]}
            )
        if not card:
            card = await db.select_one(
                table="cards",
                filters={"agendamento_id": id}
            )

        return AgendamentoResponse(
            **ag,
            paciente_nome=paciente.get("nome", "") if paciente else "",
            paciente_telefone=paciente.get("telefone", "") if paciente else "",
            medico_nome=medico.get("nome", "") if medico else "",
            tipo_consulta_nome=tipo.get("nome", "") if tipo else "",
            tipo_consulta_cor=tipo.get("cor", "#3B82F6") if tipo else "#3B82F6",
            duracao_minutos=tipo.get("duracao_minutos", 30) if tipo else 30,
            convenio_nome=convenio.get("nome") if convenio else None,
            card_id=card["id"] if card else None
        )

    async def create(
        self,
        data: AgendamentoCreate,
        current_user: CurrentUser
    ) -> AgendamentoResponse:
        """Cria novo agendamento."""
        logger.info(
            "Criando agendamento",
            paciente_id=str(data.paciente_id),
            data=data.data,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        # Validações
        paciente = await db.select_one(
            table="pacientes",
            filters={"id": str(data.paciente_id)}
        )
        if not paciente:
            raise NotFoundError("Paciente", str(data.paciente_id))

        medico = await db.select_one(
            table="usuarios",
            filters={"id": str(data.medico_id)}
        )
        if not medico:
            raise NotFoundError("Médico", str(data.medico_id))

        tipo = await db.select_one(
            table="tipos_consulta",
            filters={"id": str(data.tipo_consulta_id)}
        )
        if not tipo:
            raise NotFoundError("Tipo de consulta", str(data.tipo_consulta_id))

        # Verifica disponibilidade
        duracao = tipo.get("duracao_minutos", 30)
        hora_fim = (datetime.combine(data.data, data.hora_inicio) + timedelta(minutes=duracao)).time()

        agendamentos = await self._get_agendamentos_periodo(db, data.data, data.data, str(data.medico_id))
        bloqueios = await self._get_bloqueios_periodo(db, data.data, data.data, str(data.medico_id))

        if not self._is_slot_disponivel(data.data, data.hora_inicio, hora_fim, str(data.medico_id), agendamentos, bloqueios):
            raise SlotUnavailableError()

        # Verifica primeira vez
        consultas_anteriores = await db.count(
            table=self.TABLE,
            filters={"paciente_id": str(data.paciente_id), "status": "atendido"}
        )

        # Prepara dados
        ag_data = {
            "clinica_id": current_user.clinica_id,
            "paciente_id": str(data.paciente_id),
            "medico_id": str(data.medico_id),
            "tipo_consulta_id": str(data.tipo_consulta_id),
            "data": str(data.data),
            "hora_inicio": str(data.hora_inicio),
            "hora_fim": str(hora_fim),
            "status": "agendado",
            "primeira_vez": consultas_anteriores == 0,
            "observacoes": data.observacoes,
        }

        # Retorno de outro agendamento
        if data.retorno_de:
            ag_data["retorno_de"] = str(data.retorno_de)

        # Convênio
        if data.convenio_id:
            ag_data["convenio_id"] = str(data.convenio_id)
        if data.numero_guia:
            ag_data["numero_guia"] = data.numero_guia
        if data.valor is not None:
            ag_data["valor"] = data.valor

        # Insere
        agendamento = await db.insert(table=self.TABLE, data=ag_data)
        logger.info("Agendamento criado", id=agendamento["id"])

        # Integração com Cards
        card_id = await self._integrar_com_cards(
            db, agendamento["id"], str(data.paciente_id),
            str(data.medico_id), data.data, str(data.hora_inicio),
            current_user.clinica_id
        )
        if card_id:
            # Atualiza o agendamento com card_id
            await db.update(table=self.TABLE, data={"card_id": card_id}, filters={"id": agendamento["id"]})

        return await self.get(agendamento["id"], current_user)

    async def update(
        self,
        id: str,
        data: AgendamentoUpdate,
        current_user: CurrentUser
    ) -> AgendamentoResponse:
        """Atualiza agendamento."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Agendamento", id)

        if existing["status"] in ("atendido", "cancelado", "faltou"):
            raise ValidationError(f"Não é possível alterar agendamento com status '{existing['status']}'")

        update_data = {k: str(v) if isinstance(v, UUID) else v for k, v in data.model_dump(exclude_none=True).items()}

        if update_data:
            await db.update(table=self.TABLE, data=update_data, filters={"id": id})

        return await self.get(id, current_user)

    async def update_status(
        self,
        id: str,
        data: AgendamentoStatusUpdate,
        current_user: CurrentUser
    ) -> AgendamentoResponse:
        """Atualiza status do agendamento."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Agendamento", id)

        current_status = existing["status"]
        new_status = data.status

        # Valida transição
        allowed = self.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(current_status, new_status)

        update_data = {"status": new_status}
        if data.motivo_cancelamento:
            update_data["motivo_cancelamento"] = data.motivo_cancelamento

        await db.update(table=self.TABLE, data=update_data, filters={"id": id})
        logger.info("Status atualizado", id=id, de=current_status, para=new_status)

        # Atualiza card vinculado quando status muda
        await self._atualizar_card_por_status(db, id, new_status)

        return await self.get(id, current_user)

    # ==========================================
    # ATALHOS
    # ==========================================

    async def confirmar(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Confirma agendamento (atalho)."""
        return await self.update_status(id, AgendamentoStatusUpdate(status="confirmado"), current_user)

    async def cancelar(self, id: str, current_user: CurrentUser, motivo: Optional[str] = None) -> AgendamentoResponse:
        """Cancela agendamento (atalho)."""
        return await self.update_status(
            id,
            AgendamentoStatusUpdate(status="cancelado", motivo_cancelamento=motivo),
            current_user
        )

    async def registrar_chegada(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Registra chegada do paciente."""
        return await self.update_status(id, AgendamentoStatusUpdate(status="aguardando"), current_user)

    async def iniciar_atendimento(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Inicia atendimento."""
        return await self.update_status(id, AgendamentoStatusUpdate(status="em_atendimento"), current_user)

    async def finalizar_atendimento(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Finaliza atendimento."""
        return await self.update_status(id, AgendamentoStatusUpdate(status="atendido"), current_user)

    async def marcar_falta(self, id: str, current_user: CurrentUser) -> AgendamentoResponse:
        """Marca falta."""
        return await self.update_status(id, AgendamentoStatusUpdate(status="faltou"), current_user)


# Singleton
agenda_service = AgendaService()
