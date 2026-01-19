"""
Pacientes - Service
Lógica de negócio para gestão de pacientes.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- RLS filtra automaticamente por clinica_id
"""
from __future__ import annotations

from typing import Optional

import structlog

from app.core.database import get_authenticated_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import CurrentUser
from app.core.utils import calculate_age
from app.pacientes.schemas import (
    PacienteCreate,
    PacienteResponse,
    PacienteUpdate,
)

logger = structlog.get_logger()


class PacienteService:
    """Service para operações com pacientes."""

    TABLE = "pacientes"

    # ==========================================
    # CRUD
    # ==========================================

    async def list(
        self,
        current_user: CurrentUser,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        ativo: Optional[bool] = None,
        convenio_id: Optional[str] = None,
        sort: str = "nome",
        order: str = "asc"
    ) -> dict:
        """
        Lista pacientes com paginação e filtros.
        
        RLS garante que só retorna pacientes da clínica do usuário.
        """
        logger.info(
            "Listando pacientes",
            clinica_id=current_user.clinica_id,
            user_id=current_user.id,
            page=page,
            search=search
        )

        db = get_authenticated_db(current_user.access_token)

        # Filtros
        filters = {}
        
        if ativo is not None:
            filters["ativo"] = ativo
        
        if convenio_id:
            filters["convenio_id"] = convenio_id

        # Paginação padrão
        return await db.paginate(
            table=self.TABLE,
            columns="id, nome, telefone, cpf, data_nascimento, ativo, created_at",
            filters=filters if filters else None,
            order_by=sort,
            order_asc=(order == "asc"),
            page=page,
            per_page=per_page
        )

    async def get(self, id: str, current_user: CurrentUser) -> PacienteResponse:
        """
        Busca paciente por ID.
        
        RLS garante que só pode buscar pacientes da própria clínica.
        """
        logger.info("Buscando paciente", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        paciente = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )

        if not paciente:
            raise NotFoundError("Paciente", id)

        # Calcula idade se tem data de nascimento
        if paciente.get("data_nascimento"):
            paciente["idade"] = calculate_age(paciente["data_nascimento"])
        else:
            paciente["idade"] = None

        return PacienteResponse(**paciente)

    async def create(
        self, 
        data: PacienteCreate, 
        current_user: CurrentUser
    ) -> PacienteResponse:
        """
        Cria novo paciente.
        
        clinica_id é pego automaticamente do current_user.
        """
        logger.info(
            "Criando paciente", 
            nome=data.nome, 
            clinica_id=current_user.clinica_id,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        # Verifica duplicidade de CPF (RLS garante que é só na clínica)
        if data.cpf:
            existing = await db.select_one(
                table=self.TABLE,
                filters={"cpf": data.cpf}
            )
            if existing:
                raise ConflictError("cpf", data.cpf)

        # Verifica duplicidade de telefone
        existing_phone = await db.select_one(
            table=self.TABLE,
            filters={"telefone": data.telefone}
        )
        if existing_phone:
            raise ConflictError("telefone", data.telefone)

        # Prepara dados
        paciente_data = data.model_dump(exclude_none=True, mode='json')
        paciente_data["clinica_id"] = current_user.clinica_id
        paciente_data["ativo"] = True

        # Insere
        paciente = await db.insert(
            table=self.TABLE,
            data=paciente_data
        )

        logger.info("Paciente criado", id=paciente["id"])
        return await self.get(paciente["id"], current_user)

    async def update(
        self,
        id: str,
        data: PacienteUpdate,
        current_user: CurrentUser
    ) -> PacienteResponse:
        """Atualiza paciente."""
        logger.info(
            "Atualizando paciente", 
            id=id, 
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        # Verifica se existe (RLS garante que é da clínica)
        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Paciente", id)

        # Verifica duplicidade de CPF (se alterou)
        if data.cpf and data.cpf != existing.get("cpf"):
            dup = await db.select_one(
                table=self.TABLE,
                filters={"cpf": data.cpf}
            )
            if dup and dup["id"] != id:
                raise ConflictError("cpf", data.cpf)

        # Verifica duplicidade de telefone (se alterou)
        if data.telefone and data.telefone != existing.get("telefone"):
            dup = await db.select_one(
                table=self.TABLE,
                filters={"telefone": data.telefone}
            )
            if dup and dup["id"] != id:
                raise ConflictError("telefone", data.telefone)

        # Prepara dados (remove None)
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            return await self.get(id, current_user)

        # Atualiza (RLS garante que é da clínica)
        await db.update(
            table=self.TABLE,
            data=update_data,
            filters={"id": id}
        )

        logger.info("Paciente atualizado", id=id)
        return await self.get(id, current_user)

    async def delete(self, id: str, current_user: CurrentUser) -> None:
        """Soft delete de paciente."""
        logger.info(
            "Deletando paciente", 
            id=id, 
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Paciente", id)

        # Soft delete (muda ativo para False)
        await db.update(
            table=self.TABLE,
            data={"ativo": False},
            filters={"id": id}
        )

        logger.info("Paciente inativado", id=id)

    # ==========================================
    # BUSCAS ESPECÍFICAS
    # ==========================================

    async def buscar_por_telefone(
        self,
        telefone: str,
        current_user: CurrentUser
    ) -> Optional[PacienteResponse]:
        """Busca paciente por telefone."""
        logger.info("Buscando por telefone", telefone=telefone[-4:])

        db = get_authenticated_db(current_user.access_token)

        paciente = await db.select_one(
            table=self.TABLE,
            filters={"telefone": telefone}
        )

        if paciente:
            return await self.get(paciente["id"], current_user)
        
        return None

    async def buscar_por_cpf(
        self,
        cpf: str,
        current_user: CurrentUser
    ) -> Optional[PacienteResponse]:
        """Busca paciente por CPF."""
        logger.info("Buscando por CPF", cpf=cpf[:3] + "***")

        db = get_authenticated_db(current_user.access_token)

        paciente = await db.select_one(
            table=self.TABLE,
            filters={"cpf": cpf}
        )

        if paciente:
            return await self.get(paciente["id"], current_user)
        
        return None

    async def autocomplete(
        self,
        current_user: CurrentUser,
        termo: str,
        limit: int = 10
    ) -> list[dict]:
        """Autocomplete de pacientes para busca rápida."""
        if len(termo) < 2:
            return []

        db = get_authenticated_db(current_user.access_token)

        # OTIMIZADO: Busca com ilike no SQL
        # Primeiro tenta buscar por nome (mais comum)
        results = await db.select(
            table=self.TABLE,
            columns="id, nome, telefone, cpf",
            filters={
                "ativo": True,
                "nome__ilike": termo
            },
            limit=limit
        )

        # Se não encontrou o suficiente, busca por CPF/telefone
        if len(results) < limit:
            remaining = limit - len(results)
            existing_ids = {str(r["id"]) for r in results}
            
            # Busca por telefone
            telefone_results = await db.select(
                table=self.TABLE,
                columns="id, nome, telefone, cpf",
                filters={
                    "ativo": True,
                    "telefone__ilike": termo
                },
                limit=remaining
            )
            
            for r in telefone_results:
                if str(r["id"]) not in existing_ids:
                    results.append(r)
                    existing_ids.add(str(r["id"]))

        return results[:limit]


# Instância singleton
paciente_service = PacienteService()
