# Modelo de Segurança

## Visão Geral

Este sistema utiliza uma arquitetura de segurança em camadas:

1. **Autenticação**: Supabase Auth (JWT)
2. **Autorização**: Perfis e Permissões
3. **Isolamento de Dados**: RLS + Filtros Explícitos

## Fluxo de Autenticação

```
Cliente → API (JWT) → Supabase Auth (validação) → Service (lógica) → Database
```

1. Cliente envia JWT no header `Authorization: Bearer <token>`
2. Middleware `get_current_user()` valida token com Supabase Auth
3. Se válido, extrai `CurrentUser` com clinica_id, perfil, permissões
4. Services usam `get_authenticated_db()` para acessar banco

## Modelo de Dados do Usuário

```python
class CurrentUser:
    id: str                 # ID do usuário na tabela usuarios
    auth_user_id: str       # ID no Supabase Auth
    email: str
    nome: str
    clinica_id: str         # Clínica do usuário (isolamento)
    perfil_id: str          # Perfil de permissões
    permissoes: dict        # Mapa de permissões do perfil
    access_token: str       # JWT original
```

## Sistema de Permissões

### Estrutura

```python
permissoes = {
    "pacientes": "LCEX",    # L=Listar, C=Criar, E=Editar, X=Excluir
    "agenda": "LCE",        # Sem permissão de excluir
    "configuracoes": "L",   # Apenas leitura
}
```

### Verificação

```python
@router.get("/pacientes")
async def list_pacientes(
    current_user = Depends(require_permission("pacientes", "L"))
):
    # Só executa se usuário tem permissão "L" em "pacientes"
```

## Isolamento de Dados por Clínica

### Camada 1: RLS (Row Level Security)

Políticas no Supabase garantem que usuários só veem dados da própria clínica:

```sql
CREATE POLICY "usuarios_clinica" ON pacientes
    FOR ALL
    USING (clinica_id = auth.jwt() ->> 'clinica_id');
```

### Camada 2: Filtros Explícitos nos Services

**IMPORTANTE**: Como usamos `service_key` para bypass de RLS em alguns casos,
os services DEVEM adicionar filtros explícitos por `clinica_id`:

```python
# ✅ CORRETO - Filtro explícito
async def list(self, current_user: CurrentUser):
    filters = {"clinica_id": current_user.clinica_id}
    return await db.select(table="perfis", filters=filters)

# ❌ INCORRETO - Sem filtro (depende apenas de RLS)
async def list(self, current_user: CurrentUser):
    return await db.select(table="perfis")  # PERIGOSO!
```

### Por que duas camadas?

1. **RLS**: Proteção contra acesso direto ao banco (Supabase Dashboard, SQL)
2. **Filtros**: Proteção quando service_key é usado (bypass RLS)

## Cliente de Banco de Dados

### `get_authenticated_db(access_token)`

Retorna cliente Supabase com `service_key` (bypass RLS).

**Razão**: Permite operações que o usuário não poderia fazer diretamente,
mas que são seguras no contexto da API (ex: criar registros com clinica_id).

**Responsabilidade do Desenvolvedor**:
- Sempre validar `current_user` antes de chamar
- Sempre filtrar por `clinica_id` quando relevante
- Nunca expor este cliente diretamente ao usuário

## Checklist de Segurança para Novos Endpoints

- [ ] Usa `Depends(require_permission(...))` para autorização
- [ ] Recebe `current_user: CurrentUser` no service
- [ ] Filtra queries por `clinica_id` quando aplicável
- [ ] Valida ownership antes de UPDATE/DELETE
- [ ] Log de ações sensíveis com `logger.info()`
- [ ] Não expõe IDs internos desnecessários

## Configurações de Produção

### Variáveis Obrigatórias

```env
APP_ENV=production
APP_DEBUG=false
JWT_SECRET=<string-aleatoria-32-chars>
CORS_ORIGINS=https://app.minhaempresa.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_KEY=<service-role-key>
```

### Validações Automáticas

O sistema valida automaticamente em produção:
- `JWT_SECRET` não pode ser o valor default
- Aviso se `CORS_ORIGINS` está como `*`
- Aviso se `APP_DEBUG` está habilitado

## Auditoria

### Logs Estruturados

```python
logger.info(
    "Paciente criado",
    id=paciente["id"],
    user_id=current_user.id,
    clinica_id=current_user.clinica_id
)
```

### Dados Sensíveis

CPF e telefone são mascarados nos logs:

```python
logger.info("Buscando por CPF", cpf=cpf[:3] + "***")
```

## Vulnerabilidades Conhecidas e Mitigações

| Risco | Mitigação |
|-------|-----------|
| SQL Injection | Supabase client usa prepared statements |
| JWT Forgery | Validação via Supabase Auth |
| Cross-Tenant Access | RLS + Filtros explícitos |
| IDOR | Validação de ownership nos services |
| Sensitive Data Exposure | Mascaramento em logs |
