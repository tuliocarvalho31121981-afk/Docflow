# Backend Documentation
## Sistema de Gestão de Clínicas - API FastAPI

**Versão:** 1.1  
**Stack:** Python 3.12 + FastAPI + Supabase  
**Última atualização:** Janeiro 2026

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Core](#4-core)
5. [Módulos de Negócio](#5-módulos-de-negócio)
6. [Autenticação e RLS](#6-autenticação-e-rls)
7. [Padrões e Convenções](#7-padrões-e-convenções)
8. [Configuração e Deploy](#8-configuração-e-deploy)
9. [Guia de Desenvolvimento](#9-guia-de-desenvolvimento)

---

## 1. Visão Geral

### 1.1 O que é

Backend API RESTful para sistema de gestão de clínicas médicas:

| Camada | Função |
|--------|--------|
| **CRUD** | Operações básicas de dados |
| **Autenticação** | JWT via Supabase Auth |
| **RLS** | Row Level Security automático |
| **Multi-tenant** | Isolamento por clínica |

### 1.2 Princípios

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRINCÍPIOS DO BACKEND                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Token-based RLS: Cada query usa o token do usuário          │
│  2. Multi-tenant: Isolamento automático por clinica_id          │
│  3. Auditável: Tudo é rastreado                                 │
│  4. Seguro: RLS no banco, validação em toda camada              │
│  5. Stateless: Sem estado no servidor                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Stack Tecnológica

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.12 | Linguagem |
| FastAPI | 0.109 | Framework web |
| Pydantic | 2.5 | Validação de dados |
| Supabase | 2.3 | Banco + Auth + Storage |
| structlog | 24.1 | Logging estruturado |

---

## 2. Arquitetura

### 2.1 Visão Macro

```
                                    ┌─────────────────┐
                                    │   Frontend      │
                                    │   (React)       │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │                   FASTAPI                        │
                    │                                                  │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
                    │  │  Routers │ │ Services │ │    Database      │ │
                    │  │          │ │          │ │                  │ │
                    │  │ /auth    │ │ Auth     │ │ get_db(token)    │ │
                    │  │ /pacient │ │ Paciente │ │ ↓                │ │
                    │  │ /agenda  │ │ Agenda   │ │ Supabase Client  │ │
                    │  │ /cards   │ │ Cards    │ │ (autenticado)    │ │
                    │  │ /clinica │ │ Clinica  │ │                  │ │
                    │  │ /evidenc │ │ Evidenc  │ │                  │ │
                    │  └──────────┘ └──────────┘ └──────────────────┘ │
                    │                                                  │
                    └────────────────────────┬────────────────────────┘
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │                   SUPABASE                       │
                    │                                                  │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
                    │  │ Postgres │ │   Auth   │ │     Storage      │ │
                    │  │   + RLS  │ │  + JWT   │ │   (Arquivos)     │ │
                    │  └──────────┘ └──────────┘ └──────────────────┘ │
                    │                                                  │
                    └─────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Requisição com RLS

```
1. Request chega com Bearer Token
         │
         ▼
2. get_current_user() valida JWT com Supabase
         │
         ▼
3. CurrentUser extraído (id, clinica_id, perfil, access_token)
         │
         ▼
4. Router passa current_user para Service
         │
         ▼
5. Service chama get_db(current_user.access_token)
         │
         ▼
6. Supabase Client criado COM o token do usuário
         │
         ▼
7. RLS policies filtram automaticamente por clinica_id
         │
         ▼
8. Usuário só vê dados da sua clínica
```

### 2.3 Padrão de Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                          ROUTER                                  │
│  • Recebe request                                               │
│  • Valida input (Pydantic)                                      │
│  • Extrai current_user via Depends                              │
│  • Passa current_user para service                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          SERVICE                                 │
│  • Recebe current_user: CurrentUser                             │
│  • Chama get_db(current_user.access_token)                      │
│  • Executa lógica de negócio                                    │
│  • RLS garante isolamento automático                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE                                 │
│  • Cliente Supabase autenticado                                 │
│  • Queries respeitam RLS                                        │
│  • Não precisa filtrar por clinica_id manualmente               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Estrutura do Projeto

```
backend/
│
├── app/                           # Código da aplicação
│   │
│   ├── __init__.py               
│   ├── main.py                   # FastAPI app + registro de routers
│   │
│   ├── core/                     # Núcleo compartilhado
│   │   ├── config.py             # Configurações (env vars)
│   │   ├── database.py           # get_db(token) → Supabase Client
│   │   ├── security.py           # CurrentUser, get_current_user
│   │   ├── exceptions.py         # Exceções customizadas
│   │   ├── schemas.py            # Schemas base (BaseSchema, etc)
│   │   └── utils.py              # Utilitários (datas, validações)
│   │
│   ├── auth/                     # Módulo de autenticação
│   │   ├── router.py             # /auth/login, /auth/me, etc
│   │   └── schemas.py            
│   │
│   ├── pacientes/                # Módulo de pacientes
│   │   ├── router.py             
│   │   ├── service.py            
│   │   └── schemas.py            
│   │
│   ├── agenda/                   # Módulo de agenda
│   │   ├── router.py             
│   │   ├── service.py            
│   │   └── schemas.py            
│   │
│   ├── cards/                    # Módulo Kanban
│   │   ├── router.py             
│   │   ├── service.py            
│   │   └── schemas.py            
│   │
│   ├── clinicas/                 # Módulo clínica + perfis
│   │   ├── router.py             
│   │   ├── service.py            
│   │   └── schemas.py            
│   │
│   ├── evidencias/               # Módulo de evidências
│   │   ├── router.py             
│   │   ├── service.py            
│   │   └── schemas.py            
│   │
│   └── webhooks/                 # Webhooks recebidos
│       └── whatsapp.py           
│
├── tests/                        
│   └── test_api.py               # Script de teste completo
│
├── requirements.txt              
├── .env                          # Variáveis de ambiente
└── README.md                     
```

---

## 4. Core

### 4.1 database.py

O módulo de database foi refatorado para usar **cliente autenticado**:

```python
from supabase import create_client, Client

# Cliente anon (para login inicial)
_anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_db(access_token: str) -> SupabaseClient:
    """
    Retorna cliente Supabase autenticado com o token do usuário.
    
    O token é passado no header Authorization, fazendo com que
    as RLS policies do Supabase filtrem automaticamente os dados
    pela clinica_id do usuário.
    """
    client = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {access_token}"}
        )
    )
    return SupabaseClient(client)
```

### 4.2 security.py

```python
class CurrentUser(BaseModel):
    """Usuário atual extraído do token JWT."""
    
    id: str
    email: str
    nome: str
    clinica_id: str
    perfil_id: str
    perfil_nome: str
    permissoes: Dict[str, str]
    is_admin: bool
    is_medico: bool
    access_token: str  # Token para criar cliente autenticado


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency que extrai e valida o usuário do token JWT.
    
    1. Valida token com Supabase Auth
    2. Busca dados do usuário na tabela users
    3. Retorna CurrentUser com todas as informações + token
    """
    token = credentials.credentials
    
    # Valida com Supabase
    user_response = db.client.auth.get_user(token)
    
    # Busca dados completos
    user_data = db.client.table("users").select(
        "*, perfis(*)"
    ).eq("id", user_response.user.id).single().execute()
    
    return CurrentUser(
        id=str(user_data.data["id"]),
        email=user_data.data["email"],
        nome=user_data.data["nome"],
        clinica_id=str(user_data.data["clinica_id"]),
        # ... outros campos
        access_token=token  # Importante!
    )
```

### 4.3 exceptions.py

```python
class AppException(Exception):
    """Base para exceções da aplicação."""
    status_code: int = 500
    code: str = "internal_error"
    message: str = "Erro interno"

class NotFoundError(AppException):
    status_code = 404
    code = "not_found"

class ValidationError(AppException):
    status_code = 422
    code = "validation_error"

class ConflictError(AppException):
    status_code = 409
    code = "conflict"

class AuthorizationError(AppException):
    status_code = 403
    code = "permission_denied"
```

---

## 5. Módulos de Negócio

### 5.1 Padrão Service

Todos os services seguem o mesmo padrão:

```python
class ExemploService:
    """Service para operações de Exemplo."""
    
    TABLE = "exemplos"
    
    async def list(
        self,
        current_user: CurrentUser,  # Sempre recebe current_user
        **filters
    ) -> dict:
        """Lista com paginação."""
        db = get_db(current_user.access_token)  # Cliente autenticado
        
        # RLS filtra automaticamente por clinica_id
        result = await db.select(
            table=self.TABLE,
            filters=filters
        )
        return result
    
    async def get(
        self, 
        id: str, 
        current_user: CurrentUser
    ) -> ExemploResponse:
        """Obtém um registro."""
        db = get_db(current_user.access_token)
        
        # Não precisa filtrar por clinica_id - RLS faz isso
        result = await db.select_one(
            table=self.TABLE,
            filters={"id": id}
        )
        
        if not result:
            raise NotFoundError("Exemplo", id)
        
        return ExemploResponse(**result)
    
    async def create(
        self, 
        data: ExemploCreate, 
        current_user: CurrentUser
    ) -> ExemploResponse:
        """Cria registro."""
        db = get_db(current_user.access_token)
        
        # clinica_id vem do current_user
        record = {
            "clinica_id": current_user.clinica_id,
            **data.model_dump()
        }
        
        result = await db.insert(self.TABLE, record)
        return ExemploResponse(**result)


# Instância singleton
exemplo_service = ExemploService()
```

### 5.2 Padrão Router

```python
router = APIRouter(prefix="/exemplos", tags=["Exemplos"])

@router.get("", response_model=PaginatedResponse[ExemploListItem])
async def list_exemplos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("exemplos", "L"))
):
    """Lista exemplos com paginação."""
    return await exemplo_service.list(
        current_user=current_user,  # Passa current_user
        page=page,
        per_page=per_page
    )

@router.get("/{id}", response_model=ExemploResponse)
async def get_exemplo(
    id: UUID,
    current_user: CurrentUser = Depends(require_permission("exemplos", "L"))
):
    """Obtém exemplo por ID."""
    return await exemplo_service.get(
        id=str(id),
        current_user=current_user
    )

@router.post("", response_model=ExemploResponse, status_code=201)
async def create_exemplo(
    data: ExemploCreate,
    current_user: CurrentUser = Depends(require_permission("exemplos", "C"))
):
    """Cria novo exemplo."""
    return await exemplo_service.create(
        data=data,
        current_user=current_user
    )
```

### 5.3 Módulos Implementados

| Módulo | Prefixo | Tabelas | Status |
|--------|---------|---------|--------|
| Auth | `/auth` | users, perfis | ✅ |
| Pacientes | `/pacientes` | pacientes, alergias, medicamentos | ✅ |
| Agenda | `/agenda` | agendamentos, tipos_consulta, bloqueios_agenda | ✅ |
| Cards | `/cards` | cards, cards_checklist, cards_historico | ✅ |
| Clínicas | `/clinica` | clinicas, perfis | ✅ |
| Evidências | `/evidencias` | (tabela ainda não existe) | ⚠️ |

---

## 6. Autenticação e RLS

### 6.1 Fluxo de Login

```
1. Cliente POST /auth/login com {email, senha}
         │
         ▼
2. Backend chama Supabase Auth sign_in_with_password
         │
         ▼
3. Supabase retorna access_token + refresh_token
         │
         ▼
4. Backend busca dados do usuário na tabela users
         │
         ▼
5. Retorna tokens + dados do usuário para o cliente
```

### 6.2 Como RLS Funciona

```sql
-- Policy no Supabase (exemplo para tabela pacientes)
CREATE POLICY "pacientes_clinica" ON pacientes
    FOR ALL USING (
        clinica_id IN (
            SELECT clinica_id FROM users WHERE id = auth.uid()
        )
    );
```

Quando o backend faz uma query com o token do usuário:

```python
db = get_db(current_user.access_token)
pacientes = await db.select("pacientes")  # Sem filtro!
```

O Supabase automaticamente:
1. Extrai o `user_id` do token (via `auth.uid()`)
2. Encontra a `clinica_id` do usuário
3. Filtra pacientes apenas dessa clínica

### 6.3 Vantagens do RLS

| Aspecto | Sem RLS | Com RLS |
|---------|---------|---------|
| Segurança | Depende do código | Garantida pelo banco |
| Performance | N+1 queries | Query única otimizada |
| Manutenção | Filtro em todo lugar | Policy centralizada |
| Bugs | Fácil esquecer filtro | Impossível vazar dados |

---

## 7. Padrões e Convenções

### 7.1 Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ExemploBase(BaseSchema):
    """Campos compartilhados."""
    nome: str = Field(min_length=2, max_length=255)
    descricao: Optional[str] = None

class ExemploCreate(ExemploBase):
    """Campos para criação."""
    pass

class ExemploUpdate(BaseSchema):
    """Campos para atualização (todos opcionais)."""
    nome: Optional[str] = None
    descricao: Optional[str] = None

class ExemploResponse(ExemploBase):
    """Response completa."""
    id: UUID
    created_at: Optional[datetime] = None
```

### 7.2 Tratamento de Erros

```python
# No service
async def get(self, id: str, current_user: CurrentUser):
    db = get_db(current_user.access_token)
    
    result = await db.select_one(self.TABLE, {"id": id})
    
    if not result:
        raise NotFoundError("Recurso", id)
    
    return result

# Exception handler no main.py
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.to_dict()}
    )
```

### 7.3 Logging

```python
import structlog

logger = structlog.get_logger()

async def create(self, data, current_user):
    logger.info(
        "Criando registro",
        tabela=self.TABLE,
        user_id=current_user.id,
        clinica_id=current_user.clinica_id
    )
    
    try:
        result = await db.insert(...)
        logger.info("Registro criado", id=result["id"])
        return result
    except Exception as e:
        logger.error("Erro ao criar", error=str(e))
        raise
```

---

## 8. Configuração e Deploy

### 8.1 Variáveis de Ambiente

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...  # Apenas para operações admin

# App
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
FRONTEND_URL=http://localhost:3000

# Teste
TEST_EMAIL=usuario@teste.com
TEST_PASSWORD=senha123
```

### 8.2 Rodando Local

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

pip install -r requirements.txt

# Copiar e editar .env
cp .env.example .env

# Rodar
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload

# Testar
python test_api.py
```

---

## 9. Guia de Desenvolvimento

### 9.1 Adicionando um Módulo

```bash
# 1. Criar estrutura
mkdir -p app/novo_modulo
touch app/novo_modulo/{__init__,schemas,service,router}.py

# 2. Implementar schemas.py (DTOs)
# 3. Implementar service.py (lógica + get_db(token))
# 4. Implementar router.py (endpoints + current_user)

# 5. Registrar no main.py
# Adicionar à lista routers_to_register
```

### 9.2 Checklist para Novo Endpoint

- [ ] Schema de request (Create/Update)
- [ ] Schema de response
- [ ] Método no service recebendo `current_user`
- [ ] Service usando `get_db(current_user.access_token)`
- [ ] Router com `Depends(require_permission(...))`
- [ ] Testes básicos

### 9.3 Testando

```bash
# Script completo
python test_api.py

# Teste manual via curl
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@clinica.com","senha":"123456"}'

# Swagger
http://localhost:8080/docs
```

---

## Anexos

### A. Tabelas Existentes no Banco

| Tabela | Módulo |
|--------|--------|
| clinicas | Clínicas |
| perfis | Clínicas |
| users | Auth |
| pacientes | Pacientes |
| pacientes_alergias | Pacientes |
| pacientes_medicamentos | Pacientes |
| pacientes_convenios | Pacientes |
| tipos_consulta | Agenda |
| agendamentos | Agenda |
| bloqueios_agenda | Agenda |
| horarios_disponiveis | Agenda |
| cards | Cards |
| cards_checklist | Cards |
| cards_historico | Cards |
| cards_documentos | Cards |
| cards_mensagens | Cards |
| consultas | Prontuário |
| prontuarios_soap | Prontuário |
| receitas | Prontuário |
| atestados | Prontuário |
| anamneses | Prontuário |
| convenios | Convênios |
| contas_pagar | Financeiro |
| contas_receber | Financeiro |
| contas_bancarias | Financeiro |
| categorias_financeiras | Financeiro |

### B. Códigos de Erro

| Código | HTTP | Descrição |
|--------|------|-----------|
| `token_invalid` | 401 | Token JWT inválido |
| `token_missing` | 401 | Token não enviado |
| `invalid_credentials` | 401 | Email/senha incorretos |
| `permission_denied` | 403 | Sem permissão |
| `not_found` | 404 | Recurso não encontrado |
| `validation_error` | 422 | Dados inválidos |
| `conflict` | 409 | Registro duplicado |
| `internal_error` | 500 | Erro interno |

### C. Permissões

```
Formato: CLEX (Create, List, Edit, eXclude)

Módulos:
- agenda
- pacientes
- prontuario
- financeiro
- configuracoes
- usuarios
- relatorios
```

---

**Documento atualizado em:** Janeiro 2026  
**Versão:** 1.1  
**Principais mudanças:**
- Refatoração para usar cliente Supabase autenticado
- CurrentUser agora inclui access_token
- Services usam get_db(current_user.access_token)
- RLS funciona automaticamente
