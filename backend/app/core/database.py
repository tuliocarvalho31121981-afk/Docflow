"""
Core - Database
Cliente Supabase com wrapper async.

MODELO DE SEGURANÇA
===================

Este módulo usa `service_key` (service_role) que faz BYPASS de RLS.
Isso é intencional para permitir operações administrativas.

A segurança é garantida por:

1. **Validação JWT**: Sempre validar token antes de chamar get_authenticated_db()
2. **Filtros Explícitos**: Services DEVEM filtrar por clinica_id
3. **RLS como Backup**: Ainda protege contra acessos diretos ao banco

NUNCA expor o cliente diretamente para o usuário.
SEMPRE validar current_user antes de usar.

Exemplo de uso correto:
    
    async def list(self, current_user: CurrentUser):
        db = get_authenticated_db(current_user.access_token)
        return await db.select(
            table="pacientes",
            filters={"clinica_id": current_user.clinica_id}  # ← OBRIGATÓRIO
        )

Veja SECURITY.md para documentação completa.
"""
from typing import Any, Optional

from supabase import create_client, Client

from app.core.config import settings


# Cache do cliente service (singleton)
_service_client: Optional[Client] = None


def get_service_client() -> Client:
    """
    Retorna cliente Supabase com service_key (bypass RLS).
    Cliente é cacheado para reuso de conexões.
    """
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _service_client


# Alias para compatibilidade
get_supabase_client = get_service_client


def get_admin_db() -> "SupabaseClient":
    """
    Retorna wrapper do cliente Supabase para operações administrativas.

    Usado em contextos sem usuário autenticado, como webhooks.
    Usa service_key para bypass de RLS.

    ATENÇÃO: Use com cuidado, pois não há validação de usuário.
    """
    client = get_service_client()
    return SupabaseClient(client)


def get_authenticated_db(access_token: str) -> "SupabaseClient":
    """
    Retorna wrapper do cliente Supabase autenticado.
    
    NOTA: Usa service_key para bypass de RLS.
    A segurança é garantida pelo JWT já validado + filtros nos services.
    
    Args:
        access_token: Token JWT do usuário (usado para identificação, não para auth no DB)
    
    Returns:
        SupabaseClient wrapper com métodos async
    """
    # Usa cliente service cacheado
    client = get_service_client()
    return SupabaseClient(client)


class SupabaseClient:
    """
    Wrapper async para cliente Supabase.
    Fornece interface simplificada para operações comuns.
    """
    
    def __init__(self, client: Client):
        self._client = client
    
    # ==========================================
    # SELECT
    # ==========================================
    
    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        order_asc: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[dict]:
        """
        Executa SELECT na tabela.
        
        Filters suportam operadores especiais:
        - {"campo": valor} -> eq (igual)
        - {"campo__gte": valor} -> gte (maior ou igual)
        - {"campo__lte": valor} -> lte (menor ou igual)
        - {"campo__gt": valor} -> gt (maior que)
        - {"campo__lt": valor} -> lt (menor que)
        - {"campo__neq": valor} -> neq (diferente)
        - {"campo__in": [valores]} -> in_ (está na lista)
        - {"campo__ilike": valor} -> ilike (like case-insensitive)
        """
        query = self._client.table(table).select(columns)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        if order_by:
            query = query.order(order_by, desc=not order_asc)
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
        
        result = query.execute()
        return result.data or []
    
    def _apply_filters(self, query, filters: dict):
        """Aplica filtros com suporte a operadores."""
        for key, value in filters.items():
            if "__" in key:
                field, op = key.rsplit("__", 1)
                if op == "gte":
                    query = query.gte(field, value)
                elif op == "lte":
                    query = query.lte(field, value)
                elif op == "gt":
                    query = query.gt(field, value)
                elif op == "lt":
                    query = query.lt(field, value)
                elif op == "neq":
                    query = query.neq(field, value)
                elif op == "in":
                    query = query.in_(field, value)
                elif op == "ilike":
                    query = query.ilike(field, f"%{value}%")
                else:
                    # Operador desconhecido, trata como campo normal
                    query = query.eq(key, value)
            else:
                query = query.eq(key, value)
        return query
    
    async def select_one(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict] = None
    ) -> Optional[dict]:
        """Executa SELECT e retorna primeiro resultado."""
        query = self._client.table(table).select(columns)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        query = query.limit(1)
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    
    # ==========================================
    # INSERT
    # ==========================================
    
    async def insert(
        self,
        table: str,
        data: dict
    ) -> dict:
        """Insere registro na tabela."""
        result = self._client.table(table).insert(data).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        raise Exception(f"Falha ao inserir em {table}")
    
    async def insert_many(
        self,
        table: str,
        data: list[dict]
    ) -> list[dict]:
        """Insere múltiplos registros."""
        result = self._client.table(table).insert(data).execute()
        return result.data or []
    
    # ==========================================
    # UPDATE
    # ==========================================
    
    async def update(
        self,
        table: str,
        data: dict,
        filters: dict
    ) -> list[dict]:
        """Atualiza registros na tabela."""
        query = self._client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data or []
    
    # ==========================================
    # DELETE
    # ==========================================
    
    async def delete(
        self,
        table: str,
        filters: dict
    ) -> list[dict]:
        """Remove registros da tabela."""
        query = self._client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data or []
    
    # ==========================================
    # COUNT
    # ==========================================
    
    async def count(
        self,
        table: str,
        filters: Optional[dict] = None
    ) -> int:
        """Conta registros na tabela."""
        query = self._client.table(table).select("*", count="exact")
        
        if filters:
            query = self._apply_filters(query, filters)
        
        result = query.execute()
        return result.count or 0
    
    # ==========================================
    # PAGINATION
    # ==========================================
    
    async def paginate(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict] = None,
        order_by: str = "created_at",
        order_asc: bool = False,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """
        Retorna resultados paginados.
        
        Returns:
            dict com items, total, page, per_page, pages
        """
        # Count total
        total = await self.count(table, filters)
        
        # Calcula offset
        offset = (page - 1) * per_page
        
        # Busca items
        items = await self.select(
            table=table,
            columns=columns,
            filters=filters,
            order_by=order_by,
            order_asc=order_asc,
            limit=per_page,
            offset=offset
        )
        
        # Calcula total de páginas
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }
    
    # ==========================================
    # RPC
    # ==========================================
    
    async def rpc(
        self,
        function_name: str,
        params: Optional[dict] = None
    ) -> Any:
        """Executa função RPC no Supabase."""
        result = self._client.rpc(function_name, params or {}).execute()
        return result.data
