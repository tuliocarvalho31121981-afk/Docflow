# Sistema de Gestão de Clínicas - API Backend

API REST para sistema de gestão de clínicas médicas.

## Stack

- **Framework**: FastAPI 0.109+
- **Banco de Dados**: Supabase (PostgreSQL)
- **Autenticação**: Supabase Auth (JWT)
- **Validação**: Pydantic 2.5+
- **Logging**: Structlog

## Estrutura

```
app/
├── main.py              # Entry point, CORS, exception handlers
├── requirements.txt     # Dependências
├── SECURITY.md          # Documentação de segurança
│
├── core/                # Módulo central
│   ├── config.py        # Configurações via env vars
│   ├── database.py      # Cliente Supabase
│   ├── exceptions.py    # Exceções customizadas
│   ├── schemas.py       # Schemas base (PaginatedResponse, etc)
│   ├── security.py      # Auth, permissões, CurrentUser
│   └── utils.py         # Utilitários (CPF, telefone, datas)
│
├── auth/                # Autenticação
│   ├── router.py        # /v1/auth/*
│   ├── service.py       # Lógica de login/refresh
│   └── schemas.py       # DTOs
│
├── clinicas/            # Gestão de clínicas e perfis
│   ├── router.py        # /v1/clinica/*
│   ├── service.py
│   └── schemas.py
│
├── pacientes/           # Gestão de pacientes
│   ├── router.py        # /v1/pacientes/*
│   ├── service.py
│   └── schemas.py
│
├── agenda/              # Agendamentos
│   ├── router.py        # /v1/agenda/*
│   ├── service.py
│   └── schemas.py
│
├── cards/               # Kanban de atendimento
│   ├── router.py        # /v1/cards/*
│   ├── service.py
│   └── schemas.py
│
└── evidencias/          # Documentos e evidências
    ├── router.py        # /v1/evidencias/*
    ├── service.py
    └── schemas.py
```

## Configuração

### Variáveis de Ambiente

```env
# App
APP_ENV=development
APP_DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# JWT (para validações extras)
JWT_SECRET=sua-chave-secreta-aqui

# CORS
CORS_ORIGINS=http://localhost:3000,https://app.exemplo.com
```

### Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar em desenvolvimento
uvicorn app.main:app --reload
```

## API

### Autenticação

```bash
# Login
POST /v1/auth/login
{
  "email": "usuario@clinica.com",
  "senha": "123456"
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "nome": "Dr. João",
    "clinica_id": "uuid",
    "perfil": { ... }
  }
}
```

### Endpoints Principais

| Módulo | Endpoints |
|--------|-----------|
| Auth | `POST /v1/auth/login`, `POST /v1/auth/refresh`, `GET /v1/auth/me` |
| Clínica | `GET /v1/clinica`, `PATCH /v1/clinica`, `GET /v1/clinica/perfis` |
| Pacientes | `GET /v1/pacientes`, `POST /v1/pacientes`, `GET /v1/pacientes/{id}` |
| Agenda | `GET /v1/agenda`, `POST /v1/agenda`, `GET /v1/agenda/slots` |
| Cards | `GET /v1/cards/kanban/{fase}`, `POST /v1/cards/{id}/mover` |
| Evidências | `GET /v1/evidencias`, `POST /v1/evidencias` |

### Documentação Interativa

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Padrões de Código

### Services

```python
async def method(self, current_user: CurrentUser):
    db = get_authenticated_db(current_user.access_token)
    
    # SEMPRE filtrar por clinica_id
    return await db.select(
        table="tabela",
        filters={"clinica_id": current_user.clinica_id}
    )
```

### Routers

```python
@router.get("/items")
async def list_items(
    current_user: CurrentUser = Depends(require_permission("modulo", "L"))
):
    return await service.list(current_user=current_user)
```

### Permissões

- `L` = Listar/Ler
- `C` = Criar
- `E` = Editar
- `X` = Excluir

## Testes

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html
```

## Produção

```bash
# Variáveis obrigatórias
export APP_ENV=production
export APP_DEBUG=false
export JWT_SECRET=<chave-segura-32-chars>

# Rodar com Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Segurança

Veja [SECURITY.md](./SECURITY.md) para documentação completa do modelo de segurança.

## Licença

Proprietário - Todos os direitos reservados.
