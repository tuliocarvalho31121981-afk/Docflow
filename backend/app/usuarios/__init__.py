# app/usuarios/__init__.py
"""
Módulo de Usuários

Gerencia usuários da clínica:
- CRUD de usuários
- Vinculação com Supabase Auth
- Gerenciamento de perfis de acesso
- Dados profissionais (CRM, especialidade)

Endpoints:
- GET    /usuarios          - Lista usuários da clínica
- GET    /usuarios/{id}     - Detalhes do usuário
- POST   /usuarios          - Criar usuário
- PATCH  /usuarios/{id}     - Atualizar usuário
- DELETE /usuarios/{id}     - Desativar usuário (soft delete)
- POST   /usuarios/{id}/reativar - Reativar usuário
"""

from .router import router

__all__ = ["router"]
