"""
CIDs - Service Layer
"""
from typing import Optional, List
from app.core.database import db
from app.core.security import CurrentUser
from app.cids.schemas import (
    EspecialidadeResponse,
    CIDResponse,
    CIDBuscaResponse,
)


class CIDsService:
    """Serviço para gerenciamento de CIDs e Especialidades."""

    # ========================================================================
    # ESPECIALIDADES
    # ========================================================================

    async def list_especialidades(
        self,
        apenas_ativas: bool = True,
    ) -> List[EspecialidadeResponse]:
        """Lista todas as especialidades."""
        query = db.client.table("especialidades").select("*")

        if apenas_ativas:
            query = query.eq("ativa", True)

        result = query.order("nome").execute()

        return [EspecialidadeResponse(**item) for item in result.data]

    async def get_especialidade(self, id: str) -> Optional[EspecialidadeResponse]:
        """Busca especialidade por ID."""
        result = (
            db.client.table("especialidades")
            .select("*")
            .eq("id", id)
            .single()
            .execute()
        )

        if result.data:
            return EspecialidadeResponse(**result.data)
        return None

    async def get_especialidade_by_codigo(
        self, codigo: str
    ) -> Optional[EspecialidadeResponse]:
        """Busca especialidade por código."""
        result = (
            db.client.table("especialidades")
            .select("*")
            .eq("codigo", codigo)
            .single()
            .execute()
        )

        if result.data:
            return EspecialidadeResponse(**result.data)
        return None

    # ========================================================================
    # CIDs
    # ========================================================================

    async def buscar_cids(
        self,
        search: Optional[str] = None,
        especialidade_id: Optional[str] = None,
        limit: int = 50,
    ) -> CIDBuscaResponse:
        """
        Busca CIDs com filtro opcional por especialidade.

        Se especialidade_id for informado, retorna apenas CIDs vinculados
        e ordena por frequência de uso e favoritos.
        """
        especialidade_nome = None

        if especialidade_id:
            # Buscar nome da especialidade
            esp = await self.get_especialidade(especialidade_id)
            if esp:
                especialidade_nome = esp.nome

            # Usar função do banco para busca otimizada
            result = db.client.rpc(
                "get_cids_por_especialidade",
                {
                    "p_especialidade_id": especialidade_id,
                    "p_search": search,
                    "p_limit": limit,
                },
            ).execute()

            items = [
                CIDResponse(
                    codigo=item["codigo"],
                    descricao=item["descricao"],
                    descricao_abreviada=item["descricao_abreviada"],
                    frequencia_uso=item["frequencia_uso"],
                    favorito=item["favorito"],
                )
                for item in result.data
            ]

        else:
            # Busca geral sem especialidade
            query = db.client.table("cids").select("*").eq("ativo", True)

            if search:
                # Busca por código ou descrição
                query = query.or_(
                    f"codigo.ilike.%{search}%,descricao.ilike.%{search}%"
                )

            result = query.order("codigo").limit(limit).execute()

            items = [CIDResponse(**item) for item in result.data]

        return CIDBuscaResponse(
            items=items,
            total=len(items),
            especialidade_id=especialidade_id,
            especialidade_nome=especialidade_nome,
        )

    async def get_cid(self, codigo: str) -> Optional[CIDResponse]:
        """Busca CID por código."""
        result = (
            db.client.table("cids")
            .select("*")
            .eq("codigo", codigo)
            .single()
            .execute()
        )

        if result.data:
            return CIDResponse(**result.data)
        return None

    async def incrementar_uso_cid(
        self,
        especialidade_id: str,
        cid_codigo: str,
    ) -> None:
        """
        Incrementa contador de uso do CID para a especialidade.
        Usado para melhorar ordenação por relevância.
        """
        db.client.rpc(
            "incrementar_uso_cid",
            {
                "p_especialidade_id": especialidade_id,
                "p_cid_codigo": cid_codigo,
            },
        ).execute()

    async def get_cids_favoritos(
        self,
        especialidade_id: str,
        limit: int = 10,
    ) -> List[CIDResponse]:
        """Retorna CIDs favoritos de uma especialidade."""
        result = (
            db.client.table("cids_especialidades")
            .select("cid_codigo, frequencia_uso, favorito, cids(*)")
            .eq("especialidade_id", especialidade_id)
            .eq("favorito", True)
            .order("frequencia_uso", desc=True)
            .limit(limit)
            .execute()
        )

        items = []
        for item in result.data:
            cid_data = item.get("cids", {})
            items.append(
                CIDResponse(
                    codigo=item["cid_codigo"],
                    descricao=cid_data.get("descricao", ""),
                    descricao_abreviada=cid_data.get("descricao_abreviada"),
                    capitulo=cid_data.get("capitulo"),
                    grupo=cid_data.get("grupo"),
                    categoria=cid_data.get("categoria"),
                    frequencia_uso=item["frequencia_uso"],
                    favorito=item["favorito"],
                )
            )

        return items

    async def toggle_favorito(
        self,
        especialidade_id: str,
        cid_codigo: str,
    ) -> bool:
        """Alterna status de favorito do CID."""
        # Buscar estado atual
        result = (
            db.client.table("cids_especialidades")
            .select("id, favorito")
            .eq("especialidade_id", especialidade_id)
            .eq("cid_codigo", cid_codigo)
            .single()
            .execute()
        )

        if result.data:
            # Atualizar
            novo_favorito = not result.data["favorito"]
            db.client.table("cids_especialidades").update(
                {"favorito": novo_favorito}
            ).eq("id", result.data["id"]).execute()
            return novo_favorito
        else:
            # Criar vínculo como favorito
            db.client.table("cids_especialidades").insert(
                {
                    "especialidade_id": especialidade_id,
                    "cid_codigo": cid_codigo,
                    "favorito": True,
                    "frequencia_uso": 0,
                }
            ).execute()
            return True


# Instância singleton
cids_service = CIDsService()
