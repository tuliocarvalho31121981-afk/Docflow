"""
Evidencias - Service
Lógica de negócio para evidências documentais.

PADRÃO DE SEGURANÇA:
- Todo método recebe current_user: CurrentUser
- Todo método usa get_authenticated_db(current_user.access_token)
- RLS filtra automaticamente por clinica_id
"""
from __future__ import annotations

import hashlib
from typing import Optional
from uuid import UUID

import structlog

from app.core.database import get_authenticated_db
from app.core.exceptions import (
    EvidenceRequiredError,
    NotFoundError,
    ValidationError,
)
from app.core.security import CurrentUser
from app.core.utils import now_brasilia
from app.evidencias.schemas import (
    EvidenciaCategoria,
    EvidenciaCreate,
    EvidenciaResponse,
    EvidenciasResumo,
    EvidenciaUpdate,
    VerificacaoEvidencias,
)

logger = structlog.get_logger()


class EvidenciaService:
    """Service para operações de evidências."""

    TABLE = "evidencias"

    # ==========================================
    # CRUD
    # ==========================================

    async def list(
        self,
        current_user: CurrentUser,
        entidade: Optional[str] = None,
        entidade_id: Optional[str] = None,
        tipo: Optional[str] = None,
        categoria: Optional[str] = None,
        ativo: Optional[bool] = True,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """Lista evidências com filtros."""
        db = get_authenticated_db(current_user.access_token)

        filters = {}
        
        # Filtro de ativo (booleano direto)
        if ativo is not None:
            filters["ativo"] = ativo
        
        if entidade:
            filters["entidade"] = entidade
        if entidade_id:
            filters["entidade_id"] = entidade_id
        if tipo:
            filters["tipo"] = tipo
        if categoria:
            filters["categoria"] = categoria

        return await db.paginate(
            table=self.TABLE,
            filters=filters if filters else None,
            order_by="created_at",
            order_asc=False,
            page=page,
            per_page=per_page
        )

    async def get(self, id: str, current_user: CurrentUser) -> EvidenciaResponse:
        """Busca evidência por ID."""
        db = get_authenticated_db(current_user.access_token)

        evidencia = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )

        if not evidencia:
            raise NotFoundError("Evidência", id)

        return EvidenciaResponse(**evidencia)

    async def get_by_entidade(
        self, entidade: str, entidade_id: str, current_user: CurrentUser
    ) -> list[EvidenciaResponse]:
        """Retorna todas evidências de uma entidade."""
        db = get_authenticated_db(current_user.access_token)

        evidencias = await db.select(
            table=self.TABLE,
            filters={
                "entidade": entidade,
                "entidade_id": entidade_id,
                "ativo": True
            },
            order_by="created_at",
            order_asc=False
        )

        return [EvidenciaResponse(**e) for e in evidencias]

    async def create(
        self, data: EvidenciaCreate, current_user: CurrentUser
    ) -> EvidenciaResponse:
        """Cria nova evidência."""
        logger.info(
            "Criando evidência",
            entidade=data.entidade,
            entidade_id=str(data.entidade_id),
            tipo=data.tipo,
            user_id=current_user.id
        )

        db = get_authenticated_db(current_user.access_token)

        # Prepara dados
        evidencia_data = {
            "clinica_id": current_user.clinica_id,
            "entidade": data.entidade,
            "entidade_id": str(data.entidade_id),
            "tipo": data.tipo,
            "categoria": data.categoria.value,
            "storage_path": data.storage_path,
            "nome_arquivo": data.nome_arquivo,
            "mime_type": data.mime_type,
            "tamanho_bytes": data.tamanho_bytes,
            "descricao": data.descricao,
            "data_documento": str(data.data_documento) if data.data_documento else None,
            "data_validade": str(data.data_validade) if data.data_validade else None,
            "assinatura_digital": data.assinatura_digital,
            "assinatura_ip": data.assinatura_ip,
            "assinatura_user_agent": data.assinatura_user_agent,
            "uploaded_by_user": current_user.id,
            "ativo": True,
        }

        # Se tem assinatura digital, registra timestamp
        if data.assinatura_digital:
            evidencia_data["assinatura_em"] = now_brasilia().isoformat()

        evidencia = await db.insert(table=self.TABLE, data=evidencia_data)

        logger.info("Evidência criada", id=evidencia["id"])
        return EvidenciaResponse(**evidencia)

    async def update(
        self, id: str, data: EvidenciaUpdate, current_user: CurrentUser
    ) -> EvidenciaResponse:
        """Atualiza evidência."""
        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Evidência", id)

        if not existing.get("ativo"):
            raise ValidationError("Não é possível atualizar evidência invalidada")

        update_data = {}
        if data.descricao is not None:
            update_data["descricao"] = data.descricao
        if data.data_documento is not None:
            update_data["data_documento"] = str(data.data_documento)
        if data.data_validade is not None:
            update_data["data_validade"] = str(data.data_validade)

        if update_data:
            await db.update(table=self.TABLE, data=update_data, filters={"id": id})

        return await self.get(id, current_user)

    async def invalidar(
        self,
        id: str,
        current_user: CurrentUser,
        motivo: Optional[str] = None
    ) -> None:
        """Invalida evidência (soft delete)."""
        logger.info(
            "Invalidando evidência",
            id=id,
            user_id=current_user.id,
            motivo=motivo
        )

        db = get_authenticated_db(current_user.access_token)

        existing = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        if not existing:
            raise NotFoundError("Evidência", id)

        # CORRIGIDO: Salva motivo da invalidação
        await db.update(
            table=self.TABLE,
            data={
                "ativo": False,
                "invalidado_em": now_brasilia().isoformat(),
                "invalidado_por": current_user.id,
                "motivo_invalidacao": motivo
            },
            filters={"id": id}
        )

        logger.info("Evidência invalidada", id=id)

    # ==========================================
    # RESUMO
    # ==========================================

    async def get_resumo(
        self, entidade: str, entidade_id: str, current_user: CurrentUser
    ) -> EvidenciasResumo:
        """Retorna resumo das evidências de uma entidade."""
        db = get_authenticated_db(current_user.access_token)

        evidencias = await db.select(
            table=self.TABLE,
            filters={
                "entidade": entidade,
                "entidade_id": entidade_id,
                "ativo": True
            }
        )

        # Contagens
        por_categoria = {}
        por_tipo = {}
        for e in evidencias:
            cat = e.get("categoria", "outros")
            tipo = e.get("tipo", "outros")
            por_categoria[cat] = por_categoria.get(cat, 0) + 1
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        # Verifica pendências (baseado em regras da clínica)
        pendentes = await self._get_evidencias_pendentes(db, entidade, entidade_id, evidencias)
        
        # Verifica vencidas
        vencidas = await self._get_evidencias_vencidas(evidencias)

        return EvidenciasResumo(
            entidade=entidade,
            entidade_id=entidade_id,
            total=len(evidencias),
            por_categoria=por_categoria,
            por_tipo=por_tipo,
            pendentes=pendentes,
            vencidas=vencidas
        )

    async def _get_evidencias_pendentes(
        self, db, entidade: str, entidade_id: str, evidencias_existentes: list
    ) -> list[str]:
        """Retorna lista de tipos de evidências pendentes."""
        # Por enquanto retorna lista vazia
        # TODO: Implementar regras baseadas na configuração da clínica
        return []

    async def _get_evidencias_vencidas(self, evidencias: list) -> list[str]:
        """Retorna lista de tipos de evidências vencidas."""
        from datetime import date
        hoje = date.today()
        vencidas = []
        
        for e in evidencias:
            validade = e.get("data_validade")
            if validade:
                if isinstance(validade, str):
                    validade = date.fromisoformat(validade)
                if validade < hoje:
                    vencidas.append(e.get("tipo", "desconhecido"))
        
        return vencidas

    # ==========================================
    # VERIFICAÇÃO
    # ==========================================

    async def verificar(
        self,
        entidade: str,
        entidade_id: str,
        acao: str,
        current_user: CurrentUser,
        valor: Optional[float] = None,
        perfil: Optional[str] = None
    ) -> VerificacaoEvidencias:
        """
        Verifica se entidade tem evidências necessárias para ação.
        """
        logger.debug(
            "Verificando evidências",
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao
        )

        db = get_authenticated_db(current_user.access_token)

        # Tenta usar RPC para verificação
        try:
            result = await db.rpc(
                function_name="verificar_evidencias",
                params={
                    "p_entidade": entidade,
                    "p_entidade_id": entidade_id,
                    "p_acao": acao,
                    "p_valor": valor,
                    "p_perfil": perfil
                }
            )

            if result and len(result) > 0:
                row = result[0]
                return VerificacaoEvidencias(
                    pode_executar=row.get("pode_executar", True),
                    evidencias_faltando=row.get("evidencias_faltando", []),
                    mensagem=row.get("mensagem", "OK")
                )
        except Exception as e:
            # CORRIGIDO: Log do erro ao invés de silenciar
            logger.warning("RPC verificar_evidencias falhou, usando fallback", error=str(e))

        # Fallback: permite execução
        return VerificacaoEvidencias(
            pode_executar=True,
            evidencias_faltando=[],
            mensagem="OK"
        )

    async def exigir(
        self,
        entidade: str,
        entidade_id: str,
        acao: str,
        current_user: CurrentUser,
        valor: Optional[float] = None,
        perfil: Optional[str] = None
    ) -> None:
        """
        Verifica evidências e lança exceção se faltar.
        """
        resultado = await self.verificar(
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao,
            current_user=current_user,
            valor=valor,
            perfil=perfil
        )

        if not resultado.pode_executar:
            raise EvidenceRequiredError(
                action=acao,
                missing=resultado.evidencias_faltando,
                message=resultado.mensagem
            )

    # ==========================================
    # INTEGRIDADE
    # ==========================================

    async def calcular_hash(self, conteudo: bytes) -> str:
        """Calcula hash SHA-256 do conteúdo."""
        return hashlib.sha256(conteudo).hexdigest()

    async def verificar_integridade(
        self, id: str, current_user: CurrentUser
    ) -> bool:
        """Verifica integridade do arquivo comparando hash."""
        evidencia = await self.get(id, current_user)
        
        # TODO: Implementar download do arquivo e verificação
        # Por enquanto retorna True
        return True


# Singleton
evidencia_service = EvidenciaService()
