# app/usuarios/service.py
"""
Service de Usuários

Gerencia usuários da clínica com integração ao Supabase Auth.

IMPORTANTE:
- Criar usuário = criar no Supabase Auth + criar na tabela usuarios
- Desativar = soft delete (ativo = false), NÃO deleta do Auth
- Sempre filtrar por clinica_id para isolamento multi-tenant
"""

import structlog
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import CurrentUser
from app.usuarios.schemas import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    UsuarioListItem, ListaUsuariosResponse, PerfilResumo
)

logger = structlog.get_logger()

# Cliente Supabase com service key (bypass RLS)
_service_client = None


def _get_service_client():
    """Retorna cliente Supabase com service key."""
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _service_client


class UsuarioService:
    """Service para operações de usuários."""

    async def list(
        self,
        current_user: CurrentUser,
        incluir_inativos: bool = False,
        tipo: Optional[str] = None,
        busca: Optional[str] = None
    ) -> ListaUsuariosResponse:
        """
        Lista usuários da clínica.

        Args:
            current_user: Usuário logado (contém clinica_id)
            incluir_inativos: Se inclui usuários desativados
            tipo: Filtrar por tipo (admin, medico, etc)
            busca: Busca por nome ou email
        """
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        # Query base
        query = supabase.table("usuarios").select(
            "id, nome, email, tipo, ativo, ultimo_acesso, perfil_id, perfis(nome)"
        ).eq("clinica_id", clinica_id)

        # Filtros
        if not incluir_inativos:
            query = query.eq("ativo", True)

        if tipo:
            query = query.eq("tipo", tipo)

        if busca:
            query = query.or_(f"nome.ilike.%{busca}%,email.ilike.%{busca}%")

        # Ordenação
        query = query.order("nome")

        result = query.execute()

        usuarios = []
        ativos = 0
        inativos = 0

        for u in result.data:
            perfil_nome = None
            if u.get("perfis"):
                perfil_nome = u["perfis"].get("nome")

            usuarios.append(UsuarioListItem(
                id=str(u["id"]),
                nome=u["nome"],
                email=u["email"],
                tipo=u.get("tipo"),
                perfil_nome=perfil_nome,
                ativo=u.get("ativo", True),
                ultimo_acesso=u.get("ultimo_acesso")
            ))

            if u.get("ativo", True):
                ativos += 1
            else:
                inativos += 1

        return ListaUsuariosResponse(
            usuarios=usuarios,
            total=len(usuarios),
            ativos=ativos,
            inativos=inativos
        )

    async def get(self, id: str, current_user: CurrentUser) -> UsuarioResponse:
        """Retorna detalhes de um usuário."""
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        result = supabase.table("usuarios").select(
            "*, perfis(id, nome)"
        ).eq("id", id).eq("clinica_id", clinica_id).single().execute()

        if not result.data:
            raise NotFoundError("Usuário não encontrado")

        u = result.data

        perfil = None
        if u.get("perfis"):
            perfil = PerfilResumo(
                id=str(u["perfis"]["id"]),
                nome=u["perfis"]["nome"]
            )

        return UsuarioResponse(
            id=str(u["id"]),
            nome=u["nome"],
            email=u["email"],
            telefone=u.get("telefone"),
            cpf=u.get("cpf"),
            tipo=u.get("tipo"),
            perfil=perfil,
            crm=u.get("crm"),
            crm_uf=u.get("crm_uf"),
            especialidade=u.get("especialidade"),
            registro_conselho=u.get("registro_conselho"),
            conselho_tipo=u.get("conselho_tipo"),
            avatar_url=u.get("avatar_url"),
            assinatura_digital_url=u.get("assinatura_digital_url"),
            ativo=u.get("ativo", True),
            primeiro_acesso=u.get("primeiro_acesso", True),
            ultimo_acesso=u.get("ultimo_acesso"),
            created_at=u["created_at"],
            updated_at=u["updated_at"]
        )

    async def create(self, data: UsuarioCreate, current_user: CurrentUser) -> UsuarioResponse:
        """
        Cria novo usuário.

        FLUXO:
        1. Cria usuário no Supabase Auth (email + senha)
        2. Cria registro na tabela usuarios vinculado ao auth_user_id
        """
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        # Verifica se email já existe na clínica
        existing = supabase.table("usuarios").select("id").eq(
            "email", data.email
        ).eq("clinica_id", clinica_id).execute()

        if existing.data:
            raise ValidationError("Já existe um usuário com este email")

        # Verifica se perfil existe e pertence à clínica
        perfil_result = supabase.table("perfis").select("id").eq(
            "id", data.perfil_id
        ).eq("clinica_id", clinica_id).execute()

        if not perfil_result.data:
            raise ValidationError("Perfil não encontrado")

        # 1. Cria usuário no Supabase Auth
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": data.email,
                "password": data.senha,
                "email_confirm": True  # Auto-confirma email
            })
            auth_user_id = auth_response.user.id
        except Exception as e:
            logger.error("Erro ao criar usuário no Auth", error=str(e))
            # Se email já existe no Auth (de outra clínica), busca o ID
            if "already been registered" in str(e):
                raise ValidationError("Este email já está cadastrado no sistema")
            raise ValidationError(f"Erro ao criar usuário: {str(e)}")

        # 2. Cria registro na tabela usuarios
        usuario_id = str(uuid4())

        usuario_data = {
            "id": usuario_id,
            "clinica_id": clinica_id,
            "auth_user_id": str(auth_user_id),
            "nome": data.nome,
            "email": data.email,
            "telefone": data.telefone,
            "cpf": data.cpf,
            "perfil_id": data.perfil_id,
            "tipo": data.tipo.value if data.tipo else None,
            "crm": data.crm,
            "crm_uf": data.crm_uf,
            "especialidade": data.especialidade,
            "registro_conselho": data.registro_conselho,
            "conselho_tipo": data.conselho_tipo,
            "ativo": True,
            "primeiro_acesso": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        try:
            supabase.table("usuarios").insert(usuario_data).execute()
        except Exception as e:
            # Se falhar, tenta remover do Auth (rollback)
            try:
                supabase.auth.admin.delete_user(auth_user_id)
            except:
                pass
            logger.error("Erro ao criar usuário na tabela", error=str(e))
            raise ValidationError(f"Erro ao criar usuário: {str(e)}")

        logger.info("Usuário criado", usuario_id=usuario_id, email=data.email)

        return await self.get(usuario_id, current_user)

    async def update(self, id: str, data: UsuarioUpdate, current_user: CurrentUser) -> UsuarioResponse:
        """Atualiza dados do usuário."""
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        # Verifica se usuário existe
        existing = supabase.table("usuarios").select("id").eq(
            "id", id
        ).eq("clinica_id", clinica_id).execute()

        if not existing.data:
            raise NotFoundError("Usuário não encontrado")

        # Se mudou perfil, verifica se existe
        if data.perfil_id:
            perfil_result = supabase.table("perfis").select("id").eq(
                "id", data.perfil_id
            ).eq("clinica_id", clinica_id).execute()

            if not perfil_result.data:
                raise ValidationError("Perfil não encontrado")

        # Monta dados para update
        update_data = data.model_dump(exclude_none=True)

        # Converte enum para string
        if "tipo" in update_data and update_data["tipo"]:
            update_data["tipo"] = update_data["tipo"].value

        update_data["updated_at"] = datetime.utcnow().isoformat()

        supabase.table("usuarios").update(update_data).eq("id", id).execute()

        logger.info("Usuário atualizado", usuario_id=id)

        return await self.get(id, current_user)

    async def delete(self, id: str, current_user: CurrentUser) -> None:
        """
        Desativa usuário (soft delete).

        NÃO remove do Supabase Auth, apenas marca como inativo.
        """
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        # Verifica se usuário existe
        existing = supabase.table("usuarios").select("id, tipo").eq(
            "id", id
        ).eq("clinica_id", clinica_id).execute()

        if not existing.data:
            raise NotFoundError("Usuário não encontrado")

        # Não permite desativar o próprio usuário
        if id == current_user.id:
            raise ValidationError("Você não pode desativar seu próprio usuário")

        # Não permite desativar o último admin
        if existing.data[0].get("tipo") == "admin":
            admin_count = supabase.table("usuarios").select("id").eq(
                "clinica_id", clinica_id
            ).eq("tipo", "admin").eq("ativo", True).execute()

            if len(admin_count.data) <= 1:
                raise ValidationError("Não é possível desativar o último administrador")

        # Soft delete
        supabase.table("usuarios").update({
            "ativo": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", id).execute()

        logger.info("Usuário desativado", usuario_id=id)

    async def reativar(self, id: str, current_user: CurrentUser) -> UsuarioResponse:
        """Reativa um usuário desativado."""
        clinica_id = current_user.clinica_id
        if not clinica_id:
            raise ValidationError("Clínica não identificada")

        supabase = _get_service_client()

        # Verifica se usuário existe
        existing = supabase.table("usuarios").select("id, ativo").eq(
            "id", id
        ).eq("clinica_id", clinica_id).execute()

        if not existing.data:
            raise NotFoundError("Usuário não encontrado")

        if existing.data[0].get("ativo"):
            raise ValidationError("Usuário já está ativo")

        supabase.table("usuarios").update({
            "ativo": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", id).execute()

        logger.info("Usuário reativado", usuario_id=id)

        return await self.get(id, current_user)

    async def get_me(self, current_user: CurrentUser) -> UsuarioResponse:
        """Retorna dados do usuário logado."""
        return await self.get(current_user.id, current_user)

    async def update_me(self, data: UsuarioUpdate, current_user: CurrentUser) -> UsuarioResponse:
        """Atualiza dados do próprio usuário (campos limitados)."""
        # Usuário comum só pode alterar alguns campos próprios
        data_limitada = UsuarioUpdate(
            nome=data.nome,
            telefone=data.telefone,
            avatar_url=data.avatar_url
        )
        return await self.update(current_user.id, data_limitada, current_user)


# Singleton
usuario_service = UsuarioService()
