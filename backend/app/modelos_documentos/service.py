"""
Modelos de Documentos - Service
Lógica de negócio para templates de documentos médicos.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- RLS filtra automaticamente por clinica_id
"""
from __future__ import annotations

from typing import Optional, List

import structlog

from app.core.database import get_authenticated_db
from app.core.exceptions import NotFoundError
from app.core.security import CurrentUser
from app.modelos_documentos.schemas import (
    ModeloDocumentoCreate,
    ModeloDocumentoUpdate,
    ModeloDocumentoResponse,
    ModeloDocumentoListItem,
)

logger = structlog.get_logger()


class ModelosDocumentosService:
    """Service para operações de modelos de documentos."""

    async def list_modelos(
        self,
        current_user: CurrentUser,
        categoria: Optional[str] = None,
        apenas_ativos: bool = True,
        incluir_privados: bool = True,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """
        Lista modelos de documentos.

        Args:
            categoria: Filtrar por categoria
            apenas_ativos: Retornar apenas modelos ativos
            incluir_privados: Incluir modelos privados do usuário
        """
        logger.info(
            "Listando modelos de documentos",
            user_id=current_user.id,
            categoria=categoria
        )

        db = get_authenticated_db(current_user.access_token)

        filters = {}

        if categoria:
            filters["categoria"] = categoria

        if apenas_ativos:
            filters["ativo"] = True

        result = await db.paginate(
            table="modelos_documentos",
            filters=filters if filters else None,
            order_by="titulo",
            order_asc=True,
            page=page,
            per_page=per_page
        )

        # Filtra modelos privados de outros usuários se necessário
        if not incluir_privados:
            result["items"] = [
                item for item in result["items"]
                if not item.get("uso_exclusivo_usuario_id") or
                   item.get("uso_exclusivo_usuario_id") == current_user.id
            ]
            result["total"] = len(result["items"])

        return result

    async def list_por_categoria(
        self,
        current_user: CurrentUser,
        apenas_ativos: bool = True
    ) -> dict:
        """
        Lista modelos agrupados por categoria.

        Retorna:
            {
                "Atestados": [...],
                "Exames": [...],
                ...
            }
        """
        logger.info("Listando modelos por categoria", user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        filters = {}
        if apenas_ativos:
            filters["ativo"] = True

        modelos = await db.select(
            table="modelos_documentos",
            filters=filters if filters else None,
            order_by="titulo",
            order_asc=True
        )

        # Agrupa por categoria
        resultado = {}
        for modelo in modelos:
            categoria = modelo.get("categoria", "Outros")
            if categoria not in resultado:
                resultado[categoria] = []
            resultado[categoria].append(
                ModeloDocumentoListItem(**modelo).model_dump()
            )

        return resultado

    async def get_modelo(
        self,
        id: str,
        current_user: CurrentUser
    ) -> ModeloDocumentoResponse:
        """Busca modelo por ID."""
        logger.info("Buscando modelo", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        modelo = await db.select_one(
            table="modelos_documentos",
            filters={"id": id}
        )

        if not modelo:
            raise NotFoundError("Modelo de documento", id)

        return ModeloDocumentoResponse(**modelo)

    async def create_modelo(
        self,
        data: ModeloDocumentoCreate,
        current_user: CurrentUser
    ) -> ModeloDocumentoResponse:
        """Cria novo modelo de documento."""
        logger.info(
            "Criando modelo de documento",
            titulo=data.titulo,
            categoria=data.categoria,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        modelo_data = data.model_dump(exclude_none=True, mode='json')
        modelo_data["clinica_id"] = current_user.clinica_id
        modelo_data["created_by"] = current_user.id
        modelo_data["ativo"] = True

        modelo = await db.insert(
            table="modelos_documentos",
            data=modelo_data
        )

        logger.info("Modelo criado", id=modelo["id"])
        return await self.get_modelo(modelo["id"], current_user)

    async def update_modelo(
        self,
        id: str,
        data: ModeloDocumentoUpdate,
        current_user: CurrentUser
    ) -> ModeloDocumentoResponse:
        """Atualiza modelo de documento."""
        logger.info("Atualizando modelo", id=id, user_id=current_user.id)

        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="modelos_documentos",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Modelo de documento", id)

        update_data = data.model_dump(exclude_none=True, mode='json')

        if not update_data:
            return await self.get_modelo(id, current_user)

        await db.update(
            table="modelos_documentos",
            data=update_data,
            filters={"id": id}
        )

        logger.info("Modelo atualizado", id=id)
        return await self.get_modelo(id, current_user)

    async def delete_modelo(
        self,
        id: str,
        current_user: CurrentUser,
        soft_delete: bool = True
    ) -> bool:
        """
        Remove modelo de documento.

        Args:
            soft_delete: Se True, apenas desativa. Se False, remove permanentemente.
        """
        logger.info(
            "Removendo modelo",
            id=id,
            soft_delete=soft_delete,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table="modelos_documentos",
            filters={"id": id}
        )

        if not existing:
            raise NotFoundError("Modelo de documento", id)

        if soft_delete:
            await db.update(
                table="modelos_documentos",
                data={"ativo": False},
                filters={"id": id}
            )
        else:
            await db.delete(
                table="modelos_documentos",
                filters={"id": id}
            )

        logger.info("Modelo removido", id=id, soft_delete=soft_delete)
        return True

    async def duplicar_modelo(
        self,
        id: str,
        novo_titulo: Optional[str],
        current_user: CurrentUser
    ) -> ModeloDocumentoResponse:
        """
        Duplica um modelo existente.

        Útil para criar variações de um template.
        """
        logger.info("Duplicando modelo", id=id, user_id=current_user.id)

        # Busca modelo original
        original = await self.get_modelo(id, current_user)

        # Cria cópia
        data = ModeloDocumentoCreate(
            categoria=original.categoria,
            titulo=novo_titulo or f"{original.titulo} (cópia)",
            conteudo=original.conteudo,
            uso_exclusivo_usuario_id=original.uso_exclusivo_usuario_id
        )

        return await self.create_modelo(data, current_user)

    async def contar_por_categoria(
        self,
        current_user: CurrentUser
    ) -> List[dict]:
        """
        Conta modelos por categoria.

        Retorna lista de {categoria, total}.
        """
        db = get_authenticated_db(current_user.access_token)

        # Busca todos os modelos ativos
        modelos = await db.select(
            table="modelos_documentos",
            filters={"ativo": True}
        )

        # Conta por categoria
        contagem = {}
        for modelo in modelos:
            cat = modelo.get("categoria", "Outros")
            contagem[cat] = contagem.get(cat, 0) + 1

        return [
            {"categoria": k, "total": v}
            for k, v in sorted(contagem.items())
        ]


# Instância singleton
modelos_documentos_service = ModelosDocumentosService()
