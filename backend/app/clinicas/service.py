"""
Clinicas - Service
Lógica de negócio para clínicas e perfis.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- Filtros explícitos por clinica_id como camada extra de segurança
"""
from __future__ import annotations

import structlog

from app.core.database import get_authenticated_db
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.security import CurrentUser
from app.clinicas.schemas import (
    ClinicaResponse,
    ClinicaUpdate,
    ConfiguracaoResponse,
    PerfilCreate,
    PerfilListItem,
    PerfilResponse,
    PerfilUpdate,
)

logger = structlog.get_logger()


class ClinicaService:
    """Service para operações de clínicas."""

    TABLE = "clinicas"

    async def get(self, current_user: CurrentUser) -> ClinicaResponse:
        """Busca clínica do usuário atual."""
        db = get_authenticated_db(current_user.access_token)

        clinica = await db.select_one(
            table=self.TABLE,
            filters={"id": current_user.clinica_id}
        )

        if not clinica:
            raise NotFoundError("Clínica", current_user.clinica_id)

        return ClinicaResponse(**clinica)

    async def update(self, data: ClinicaUpdate, current_user: CurrentUser) -> ClinicaResponse:
        """Atualiza clínica do usuário atual."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": current_user.clinica_id}
        )
        if not existing:
            raise NotFoundError("Clínica", current_user.clinica_id)

        update_data = data.model_dump(exclude_none=True)
        if update_data:
            await db.update(
                table=self.TABLE,
                data=update_data,
                filters={"id": current_user.clinica_id}
            )

        return await self.get(current_user)

    async def get_configuracoes(self, current_user: CurrentUser) -> ConfiguracaoResponse:
        """Retorna configurações da clínica."""
        db = get_authenticated_db(current_user.access_token)

        config = await db.select_one(
            table="clinicas_configuracoes",
            filters={"clinica_id": current_user.clinica_id}
        )

        if not config:
            # Retorna valores padrão
            default_config = {
                "clinica_id": current_user.clinica_id,
                "agenda_antecedencia_minima": 2,
                "agenda_antecedencia_maxima": 90,
                "agenda_permitir_encaixe": False,
                "agenda_intervalo_padrao": 30,
                "agendamento_online_ativo": True,
                "agendamento_online_antecedencia": 24,
                "whatsapp_confirmacao_ativo": True,
                "whatsapp_confirmacao_horas": 24,
                "whatsapp_lembrete_ativo": True,
                "whatsapp_lembrete_horas": 24,
                "whatsapp_nps_ativo": True,
                "whatsapp_nps_horas": 24,
                "financeiro_alerta_saldo_minimo": 5000.00,
                "financeiro_alerta_contas_vencer": 7,
                "financeiro_fechamento_dia": 25,
                "ia_transcricao_auto": True,
                "ia_soap_auto": True,
                "ia_modelo_preferido": "gpt-4",
                "notificacoes_email_ativo": True,
                "notificacoes_push_ativo": True,
                "seguranca_2fa_obrigatorio": False,
                "seguranca_sessao_timeout": 480,
            }
            return ConfiguracaoResponse(**default_config)

        return ConfiguracaoResponse(**config)

    async def update_configuracoes(self, data: dict, current_user: CurrentUser) -> ConfiguracaoResponse:
        """Atualiza configurações da clínica."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="clinicas_configuracoes",
            filters={"clinica_id": current_user.clinica_id}
        )

        if existing:
            await db.update(
                table="clinicas_configuracoes",
                data=data,
                filters={"clinica_id": current_user.clinica_id}
            )
        else:
            await db.insert(
                table="clinicas_configuracoes",
                data={"clinica_id": current_user.clinica_id, **data}
            )

        return await self.get_configuracoes(current_user)


class PerfilService:
    """Service para operações de perfis."""

    TABLE = "perfis"

    async def list(self, current_user: CurrentUser, incluir_inativos: bool = False) -> list[PerfilListItem]:
        """Lista perfis da clínica."""
        db = get_authenticated_db(current_user.access_token)

        # CORRIGIDO: Adiciona filtro por clinica_id
        filters = {"clinica_id": current_user.clinica_id}
        if not incluir_inativos:
            filters["ativo"] = True

        perfis = await db.select(
            table=self.TABLE,
            filters=filters,
            order_by="nome"
        )

        return [PerfilListItem(**p) for p in perfis]

    async def get(self, id: str, current_user: CurrentUser) -> PerfilResponse:
        """Busca perfil por ID."""
        db = get_authenticated_db(current_user.access_token)

        # CORRIGIDO: Adiciona filtro por clinica_id
        perfil = await db.select_one(
            table=self.TABLE,
            filters={"id": id, "clinica_id": current_user.clinica_id}
        )

        if not perfil:
            raise NotFoundError("Perfil", id)

        return PerfilResponse(**perfil)

    async def create(self, data: PerfilCreate, current_user: CurrentUser) -> PerfilResponse:
        """Cria novo perfil."""
        logger.info("Criando perfil", nome=data.nome, clinica_id=current_user.clinica_id)

        db = get_authenticated_db(current_user.access_token)

        # CORRIGIDO: Verifica nome duplicado NA MESMA CLÍNICA
        existing = await db.select_one(
            table=self.TABLE,
            filters={"nome": data.nome, "clinica_id": current_user.clinica_id}
        )
        if existing:
            raise ConflictError("nome", data.nome)

        perfil_data = {
            "clinica_id": current_user.clinica_id,
            **data.model_dump(exclude_none=True),
            "is_sistema": False,
        }

        perfil = await db.insert(table=self.TABLE, data=perfil_data)

        logger.info("Perfil criado", id=perfil["id"])
        return PerfilResponse(**perfil)

    async def update(self, id: str, data: PerfilUpdate, current_user: CurrentUser) -> PerfilResponse:
        """Atualiza perfil."""
        db = get_authenticated_db(current_user.access_token)

        # CORRIGIDO: Adiciona filtro por clinica_id
        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id, "clinica_id": current_user.clinica_id}
        )
        if not existing:
            raise NotFoundError("Perfil", id)

        if existing.get("is_sistema"):
            raise ValidationError("Não é possível alterar perfil do sistema")

        # CORRIGIDO: Verifica nome duplicado NA MESMA CLÍNICA
        if data.nome and data.nome != existing["nome"]:
            existing_nome = await db.select_one(
                table=self.TABLE,
                filters={"nome": data.nome, "clinica_id": current_user.clinica_id}
            )
            if existing_nome:
                raise ConflictError("nome", data.nome)

        update_data = data.model_dump(exclude_none=True)
        if update_data:
            await db.update(
                table=self.TABLE,
                data=update_data,
                filters={"id": id}
            )

        return await self.get(id, current_user)

    async def delete(self, id: str, current_user: CurrentUser) -> None:
        """Desativa perfil (soft delete)."""
        db = get_authenticated_db(current_user.access_token)

        # CORRIGIDO: Adiciona filtro por clinica_id
        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id, "clinica_id": current_user.clinica_id}
        )
        if not existing:
            raise NotFoundError("Perfil", id)

        if existing.get("is_sistema"):
            raise ValidationError("Não é possível remover perfil do sistema")

        # Verifica se há usuários usando este perfil
        users_count = await db.count(
            table="usuarios",
            filters={"perfil_id": id, "ativo": True}
        )
        if users_count > 0:
            raise ValidationError(f"Perfil possui {users_count} usuário(s) ativo(s)")

        await db.update(
            table=self.TABLE,
            data={"ativo": False},
            filters={"id": id}
        )

        logger.info("Perfil desativado", id=id)


# Singletons
clinica_service = ClinicaService()
perfil_service = PerfilService()
