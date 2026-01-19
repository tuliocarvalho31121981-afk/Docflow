"""
Prontuário - Service
Lógica de negócio para consultas, SOAP, receitas, atestados, exames e encaminhamentos.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- RLS filtra automaticamente por clinica_id
- Prontuário tem RLS adicional: só médicos podem ver
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

import structlog

from app.core.database import get_authenticated_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import CurrentUser
from app.prontuario.schemas import (
    # Consultas
    ConsultaCreate,
    ConsultaUpdate,
    ConsultaResponse,
    ConsultaFinalizar,
    # Transcrições
    TranscricaoCreate,
    TranscricaoUpdate,
    TranscricaoResponse,
    # SOAP
    ProntuarioSOAPCreate,
    ProntuarioSOAPUpdate,
    ProntuarioSOAPResponse,
    # Receitas
    ReceitaCreate,
    ReceitaUpdate,
    ReceitaResponse,
    # Atestados
    AtestadoCreate,
    AtestadoUpdate,
    AtestadoResponse,
    # Exames
    ExameSolicitadoCreate,
    ExameSolicitadoUpdate,
    ExameSolicitadoResponse,
    # Encaminhamentos
    EncaminhamentoCreate,
    EncaminhamentoUpdate,
    EncaminhamentoResponse,
    # Briefing
    BriefingPaciente,
)

logger = structlog.get_logger()


class ProntuarioService:
    """Service para operações de prontuário médico."""

    # ========================================================================
    # CONSULTAS
    # ========================================================================

    async def list_consultas(
        self,
        current_user: CurrentUser,
        paciente_id: Optional[str] = None,
        medico_id: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Lista consultas com filtros."""
        logger.info("Listando consultas", user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if medico_id:
            filters["medico_id"] = medico_id
        if status:
            filters["status"] = status

        return await db.paginate(
            table="consultas",
            filters=filters if filters else None,
            order_by="data",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get_consulta(
        self,
        id: str,
        current_user: CurrentUser
    ) -> ConsultaResponse:
        """Busca consulta por ID."""
        logger.info("Buscando consulta", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        consulta = await db.select_one(
            table="consultas",
            filters={"id": id}
        )

        if not consulta:
            raise NotFoundError("Consulta", id)

        return ConsultaResponse(**consulta)

    async def create_consulta(
        self,
        data: ConsultaCreate,
        current_user: CurrentUser
    ) -> ConsultaResponse:
        """Cria nova consulta."""
        logger.info(
            "Criando consulta",
            paciente_id=str(data.paciente_id),
            medico_id=str(data.medico_id),
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        consulta_data = data.model_dump(exclude_none=True, mode='json')
        consulta_data["clinica_id"] = current_user.clinica_id
        consulta_data["status"] = "em_andamento"

        consulta = await db.insert(
            table="consultas",
            data=consulta_data
        )

        logger.info("Consulta criada", id=consulta["id"])
        return await self.get_consulta(consulta["id"], current_user)

    async def iniciar_consulta(
        self,
        agendamento_id: str,
        current_user: CurrentUser
    ) -> ConsultaResponse:
        """
        Inicia consulta a partir de um agendamento.
        Cria registro na tabela consultas e atualiza status do agendamento.
        """
        logger.info(
            "Iniciando consulta",
            agendamento_id=agendamento_id,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        # Busca agendamento
        agendamento = await db.select_one(
            table="agendamentos",
            filters={"id": agendamento_id}
        )

        if not agendamento:
            raise NotFoundError("Agendamento", agendamento_id)

        # Verifica se já existe consulta para este agendamento
        existing = await db.select_one(
            table="consultas",
            filters={"agendamento_id": agendamento_id}
        )

        if existing:
            # Retorna a consulta existente
            return await self.get_consulta(existing["id"], current_user)

        # Cria consulta
        consulta_data = {
            "clinica_id": current_user.clinica_id,
            "agendamento_id": agendamento_id,
            "paciente_id": agendamento["paciente_id"],
            "medico_id": agendamento["medico_id"],
            "data": agendamento["data"],
            "hora_inicio": datetime.now().strftime("%H:%M:%S"),
            "status": "em_andamento"
        }

        consulta = await db.insert(
            table="consultas",
            data=consulta_data
        )

        # Atualiza status do agendamento
        await db.update(
            table="agendamentos",
            data={"status": "em_atendimento"},
            filters={"id": agendamento_id}
        )

        logger.info("Consulta iniciada", id=consulta["id"])
        return await self.get_consulta(consulta["id"], current_user)

    async def update_consulta(
        self,
        id: str,
        data: ConsultaUpdate,
        current_user: CurrentUser
    ) -> ConsultaResponse:
        """Atualiza consulta."""
        logger.info("Atualizando consulta", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="consultas",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Consulta", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        if not update_data:
            return await self.get_consulta(id, current_user)

        await db.update(
            table="consultas",
            data=update_data,
            filters={"id": id}
        )

        logger.info("Consulta atualizada", id=id)
        return await self.get_consulta(id, current_user)

    async def finalizar_consulta(
        self,
        id: str,
        data: Optional[ConsultaFinalizar],
        current_user: CurrentUser
    ) -> ConsultaResponse:
        """Finaliza consulta."""
        logger.info("Finalizando consulta", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        consulta = await db.select_one(
            table="consultas",
            filters={"id": id}
        )

        if not consulta:
            raise NotFoundError("Consulta", id)

        update_data = {
            "status": "finalizada",
            "hora_fim": datetime.now().strftime("%H:%M:%S")
        }

        await db.update(
            table="consultas",
            data=update_data,
            filters={"id": id}
        )

        # Atualiza agendamento se existir
        if consulta.get("agendamento_id"):
            await db.update(
                table="agendamentos",
                data={"status": "atendido"},
                filters={"id": consulta["agendamento_id"]}
            )

        logger.info("Consulta finalizada", id=id)
        return await self.get_consulta(id, current_user)

    # ========================================================================
    # TRANSCRIÇÕES
    # ========================================================================

    async def get_transcricao(
        self,
        consulta_id: str,
        current_user: CurrentUser
    ) -> Optional[TranscricaoResponse]:
        """Busca transcrição de uma consulta."""
        db = get_authenticated_db(current_user.access_token)

        transcricao = await db.select_one(
            table="transcricoes",
            filters={"consulta_id": consulta_id}
        )

        if not transcricao:
            return None

        return TranscricaoResponse(**transcricao)

    async def create_transcricao(
        self,
        data: TranscricaoCreate,
        current_user: CurrentUser
    ) -> TranscricaoResponse:
        """Cria transcrição."""
        logger.info("Criando transcrição", consulta_id=str(data.consulta_id))

        db = get_authenticated_db(current_user.access_token)

        transcricao_data = data.model_dump(exclude_none=True, mode='json')
        transcricao_data["status"] = "processando"
        transcricao_data["iniciada_em"] = datetime.now().isoformat()

        transcricao = await db.insert(
            table="transcricoes",
            data=transcricao_data
        )

        return TranscricaoResponse(**transcricao)

    async def update_transcricao(
        self,
        id: str,
        data: TranscricaoUpdate,
        current_user: CurrentUser
    ) -> TranscricaoResponse:
        """Atualiza transcrição."""
        db = get_authenticated_db(current_user.access_token)

        update_data = data.model_dump(exclude_none=True, mode='json')

        if data.status == "concluida":
            update_data["concluida_em"] = datetime.now().isoformat()

        await db.update(
            table="transcricoes",
            data=update_data,
            filters={"id": id}
        )

        transcricao = await db.select_one(
            table="transcricoes",
            filters={"id": id}
        )

        return TranscricaoResponse(**transcricao)

    # ========================================================================
    # PRONTUÁRIO SOAP
    # ========================================================================

    async def get_soap(
        self,
        consulta_id: str,
        current_user: CurrentUser
    ) -> Optional[ProntuarioSOAPResponse]:
        """Busca SOAP de uma consulta."""
        db = get_authenticated_db(current_user.access_token)

        soap = await db.select_one(
            table="prontuarios_soap",
            filters={"consulta_id": consulta_id}
        )

        if not soap:
            return None

        return ProntuarioSOAPResponse(**soap)

    async def create_soap(
        self,
        data: ProntuarioSOAPCreate,
        current_user: CurrentUser
    ) -> ProntuarioSOAPResponse:
        """Cria prontuário SOAP."""
        logger.info("Criando SOAP", consulta_id=str(data.consulta_id))

        db = get_authenticated_db(current_user.access_token)

        soap_data = data.model_dump(exclude_none=True, mode='json')

        soap = await db.insert(
            table="prontuarios_soap",
            data=soap_data
        )

        return ProntuarioSOAPResponse(**soap)

    async def update_soap(
        self,
        id: str,
        data: ProntuarioSOAPUpdate,
        current_user: CurrentUser
    ) -> ProntuarioSOAPResponse:
        """Atualiza prontuário SOAP."""
        logger.info("Atualizando SOAP", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        update_data = data.model_dump(exclude_none=True, mode='json')

        if data.revisado_por_medico:
            update_data["revisado_em"] = datetime.now().isoformat()

        await db.update(
            table="prontuarios_soap",
            data=update_data,
            filters={"id": id}
        )

        soap = await db.select_one(
            table="prontuarios_soap",
            filters={"id": id}
        )

        return ProntuarioSOAPResponse(**soap)

    # ========================================================================
    # RECEITAS
    # ========================================================================

    async def list_receitas(
        self,
        current_user: CurrentUser,
        paciente_id: Optional[str] = None,
        consulta_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Lista receitas."""
        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if consulta_id:
            filters["consulta_id"] = consulta_id

        return await db.paginate(
            table="receitas",
            filters=filters if filters else None,
            order_by="created_at",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get_receita(
        self,
        id: str,
        current_user: CurrentUser
    ) -> ReceitaResponse:
        """Busca receita por ID."""
        db = get_authenticated_db(current_user.access_token)

        receita = await db.select_one(
            table="receitas",
            filters={"id": id}
        )

        if not receita:
            raise NotFoundError("Receita", id)

        return ReceitaResponse(**receita)

    async def create_receita(
        self,
        data: ReceitaCreate,
        current_user: CurrentUser
    ) -> ReceitaResponse:
        """Cria receita."""
        logger.info(
            "Criando receita",
            paciente_id=str(data.paciente_id),
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        receita_data = data.model_dump(exclude_none=True, mode='json')
        receita_data["clinica_id"] = current_user.clinica_id
        receita_data["data_emissao"] = date.today().isoformat()
        receita_data["status"] = "emitida"

        # Converte itens para lista de dicts
        if "itens" in receita_data:
            receita_data["itens"] = [
                item if isinstance(item, dict) else item.model_dump()
                for item in receita_data["itens"]
            ]

        receita = await db.insert(
            table="receitas",
            data=receita_data
        )

        logger.info("Receita criada", id=receita["id"])
        return await self.get_receita(receita["id"], current_user)

    async def update_receita(
        self,
        id: str,
        data: ReceitaUpdate,
        current_user: CurrentUser
    ) -> ReceitaResponse:
        """Atualiza receita."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="receitas",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Receita", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        await db.update(
            table="receitas",
            data=update_data,
            filters={"id": id}
        )

        return await self.get_receita(id, current_user)

    # ========================================================================
    # ATESTADOS
    # ========================================================================

    async def list_atestados(
        self,
        current_user: CurrentUser,
        paciente_id: Optional[str] = None,
        consulta_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Lista atestados."""
        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if consulta_id:
            filters["consulta_id"] = consulta_id

        return await db.paginate(
            table="atestados",
            filters=filters if filters else None,
            order_by="created_at",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get_atestado(
        self,
        id: str,
        current_user: CurrentUser
    ) -> AtestadoResponse:
        """Busca atestado por ID."""
        db = get_authenticated_db(current_user.access_token)

        atestado = await db.select_one(
            table="atestados",
            filters={"id": id}
        )

        if not atestado:
            raise NotFoundError("Atestado", id)

        return AtestadoResponse(**atestado)

    async def create_atestado(
        self,
        data: AtestadoCreate,
        current_user: CurrentUser
    ) -> AtestadoResponse:
        """Cria atestado."""
        logger.info(
            "Criando atestado",
            tipo=data.tipo,
            paciente_id=str(data.paciente_id),
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        atestado_data = data.model_dump(exclude_none=True, mode='json')
        atestado_data["clinica_id"] = current_user.clinica_id
        atestado_data["data_emissao"] = date.today().isoformat()
        atestado_data["status"] = "emitido"

        atestado = await db.insert(
            table="atestados",
            data=atestado_data
        )

        logger.info("Atestado criado", id=atestado["id"])
        return await self.get_atestado(atestado["id"], current_user)

    async def update_atestado(
        self,
        id: str,
        data: AtestadoUpdate,
        current_user: CurrentUser
    ) -> AtestadoResponse:
        """Atualiza atestado."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="atestados",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Atestado", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        await db.update(
            table="atestados",
            data=update_data,
            filters={"id": id}
        )

        return await self.get_atestado(id, current_user)

    # ========================================================================
    # EXAMES SOLICITADOS
    # ========================================================================

    async def list_exames(
        self,
        current_user: CurrentUser,
        paciente_id: Optional[str] = None,
        consulta_id: Optional[str] = None,
        status: Optional[str] = None,
        para_retorno: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Lista exames solicitados."""
        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if consulta_id:
            filters["consulta_id"] = consulta_id
        if status:
            filters["status"] = status
        if para_retorno is not None:
            filters["para_retorno"] = para_retorno

        return await db.paginate(
            table="exames_solicitados",
            filters=filters if filters else None,
            order_by="created_at",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get_exame(
        self,
        id: str,
        current_user: CurrentUser
    ) -> ExameSolicitadoResponse:
        """Busca exame por ID."""
        db = get_authenticated_db(current_user.access_token)

        exame = await db.select_one(
            table="exames_solicitados",
            filters={"id": id}
        )

        if not exame:
            raise NotFoundError("Exame", id)

        return ExameSolicitadoResponse(**exame)

    async def create_exame(
        self,
        data: ExameSolicitadoCreate,
        current_user: CurrentUser
    ) -> ExameSolicitadoResponse:
        """Cria solicitação de exame."""
        logger.info(
            "Criando exame",
            nome=data.nome,
            paciente_id=str(data.paciente_id),
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        exame_data = data.model_dump(exclude_none=True, mode='json')
        exame_data["status"] = "solicitado"

        exame = await db.insert(
            table="exames_solicitados",
            data=exame_data
        )

        logger.info("Exame criado", id=exame["id"])
        return await self.get_exame(exame["id"], current_user)

    async def create_exames_batch(
        self,
        consulta_id: str,
        paciente_id: str,
        medico_id: str,
        exames: List[str],
        para_retorno: bool,
        current_user: CurrentUser
    ) -> List[ExameSolicitadoResponse]:
        """Cria múltiplos exames de uma vez."""
        logger.info(
            "Criando exames em batch",
            qtd=len(exames),
            consulta_id=consulta_id
        )

        results = []
        for nome in exames:
            data = ExameSolicitadoCreate(
                consulta_id=consulta_id,
                paciente_id=paciente_id,
                medico_id=medico_id,
                nome=nome,
                para_retorno=para_retorno
            )
            exame = await self.create_exame(data, current_user)
            results.append(exame)

        return results

    async def update_exame(
        self,
        id: str,
        data: ExameSolicitadoUpdate,
        current_user: CurrentUser
    ) -> ExameSolicitadoResponse:
        """Atualiza exame."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="exames_solicitados",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Exame", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        await db.update(
            table="exames_solicitados",
            data=update_data,
            filters={"id": id}
        )

        return await self.get_exame(id, current_user)

    async def get_exames_pendentes(
        self,
        paciente_id: str,
        current_user: CurrentUser
    ) -> List[ExameSolicitadoResponse]:
        """Busca exames pendentes de um paciente."""
        db = get_authenticated_db(current_user.access_token)

        exames = await db.select(
            table="exames_solicitados",
            filters={
                "paciente_id": paciente_id,
                "status": "solicitado"
            },
            order_by="created_at",
            order_asc=False
        )

        return [ExameSolicitadoResponse(**e) for e in exames]

    # ========================================================================
    # ENCAMINHAMENTOS
    # ========================================================================

    async def list_encaminhamentos(
        self,
        current_user: CurrentUser,
        paciente_id: Optional[str] = None,
        consulta_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Lista encaminhamentos."""
        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if paciente_id:
            filters["paciente_id"] = paciente_id
        if consulta_id:
            filters["consulta_id"] = consulta_id

        return await db.paginate(
            table="encaminhamentos",
            filters=filters if filters else None,
            order_by="created_at",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get_encaminhamento(
        self,
        id: str,
        current_user: CurrentUser
    ) -> EncaminhamentoResponse:
        """Busca encaminhamento por ID."""
        db = get_authenticated_db(current_user.access_token)

        encaminhamento = await db.select_one(
            table="encaminhamentos",
            filters={"id": id}
        )

        if not encaminhamento:
            raise NotFoundError("Encaminhamento", id)

        return EncaminhamentoResponse(**encaminhamento)

    async def create_encaminhamento(
        self,
        data: EncaminhamentoCreate,
        current_user: CurrentUser
    ) -> EncaminhamentoResponse:
        """Cria encaminhamento."""
        logger.info(
            "Criando encaminhamento",
            especialidade=data.especialidade,
            paciente_id=str(data.paciente_id),
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        encaminhamento_data = data.model_dump(exclude_none=True, mode='json')
        encaminhamento_data["status"] = "emitido"

        encaminhamento = await db.insert(
            table="encaminhamentos",
            data=encaminhamento_data
        )

        logger.info("Encaminhamento criado", id=encaminhamento["id"])
        return await self.get_encaminhamento(encaminhamento["id"], current_user)

    async def update_encaminhamento(
        self,
        id: str,
        data: EncaminhamentoUpdate,
        current_user: CurrentUser
    ) -> EncaminhamentoResponse:
        """Atualiza encaminhamento."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="encaminhamentos",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Encaminhamento", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        if data.enviado_paciente:
            update_data["enviado_em"] = datetime.now().isoformat()

        await db.update(
            table="encaminhamentos",
            data=update_data,
            filters={"id": id}
        )

        return await self.get_encaminhamento(id, current_user)

    # ========================================================================
    # BRIEFING PRÉ-CONSULTA
    # ========================================================================

    async def get_briefing(
        self,
        paciente_id: str,
        current_user: CurrentUser
    ) -> BriefingPaciente:
        """
        Prepara briefing do paciente para o médico.
        Reúne dados importantes antes da consulta.
        """
        logger.info("Gerando briefing", paciente_id=paciente_id)

        db = get_authenticated_db(current_user.access_token)

        # Busca paciente
        paciente = await db.select_one(
            table="pacientes",
            filters={"id": paciente_id}
        )

        if not paciente:
            raise NotFoundError("Paciente", paciente_id)

        # Calcula idade
        idade = None
        if paciente.get("data_nascimento"):
            from app.core.utils import calculate_age
            idade = calculate_age(paciente["data_nascimento"])

        # Busca alergias
        alergias_records = await db.select(
            table="pacientes_alergias",
            filters={"paciente_id": paciente_id, "ativa": True}
        )
        alergias = [a.get("substancia", "") for a in alergias_records]

        # Busca medicamentos em uso
        medicamentos_records = await db.select(
            table="pacientes_medicamentos",
            filters={"paciente_id": paciente_id, "em_uso": True}
        )
        medicamentos = [
            f"{m.get('nome', '')} {m.get('dose', '')}"
            for m in medicamentos_records
        ]

        # Busca última consulta
        ultima_consulta = await db.select_one(
            table="consultas",
            filters={"paciente_id": paciente_id, "status": "finalizada"},
            order_by="data",
            order_asc=False
        )

        ultima_consulta_data = None
        if ultima_consulta:
            ultima_consulta_data = {
                "data": str(ultima_consulta.get("data")),
                "queixa": ultima_consulta.get("queixa_principal"),
                "conduta": ultima_consulta.get("conduta")
            }

        # Busca exames pendentes
        exames_pendentes = await db.select(
            table="exames_solicitados",
            filters={"paciente_id": paciente_id, "status": "solicitado"},
            limit=10
        )

        exames_list = [
            {"nome": e.get("nome"), "data": str(e.get("created_at", "")[:10])}
            for e in exames_pendentes
        ]

        # Monta alertas
        alertas = []
        if alergias:
            alertas.append(f"⚠️ ALERGIAS: {', '.join(alergias)}")
        if exames_pendentes:
            alertas.append(f"📋 {len(exames_pendentes)} exame(s) pendente(s)")

        return BriefingPaciente(
            paciente_id=paciente_id,
            nome=paciente.get("nome", ""),
            idade=idade,
            sexo=paciente.get("sexo"),
            alergias=alergias,
            medicamentos_uso=medicamentos,
            antecedentes=paciente.get("observacoes"),
            ultima_consulta=ultima_consulta_data,
            exames_pendentes=exames_list,
            alertas=alertas
        )

    # ========================================================================
    # HISTÓRICO
    # ========================================================================

    async def get_historico(
        self,
        paciente_id: str,
        current_user: CurrentUser,
        limit: int = 10
    ) -> List[dict]:
        """Busca histórico de consultas do paciente."""
        db = get_authenticated_db(current_user.access_token)

        consultas = await db.select(
            table="consultas",
            filters={"paciente_id": paciente_id, "status": "finalizada"},
            order_by="data",
            order_asc=False,
            limit=limit
        )

        historico = []
        for c in consultas:
            # Verifica se teve receita
            receita = await db.select_one(
                table="receitas",
                filters={"consulta_id": c["id"]}
            )

            # Verifica se teve exames
            exame = await db.select_one(
                table="exames_solicitados",
                filters={"consulta_id": c["id"]}
            )

            historico.append({
                "consulta_id": c["id"],
                "data": c["data"],
                "resumo": c.get("conduta"),
                "cids": [],
                "teve_receita": receita is not None,
                "teve_exames": exame is not None
            })

        return historico


# Instância singleton
prontuario_service = ProntuarioService()
