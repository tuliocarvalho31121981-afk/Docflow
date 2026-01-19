# Backend Documentation
## Sistema de Gestão de Clínicas - API FastAPI

**Versão:** 1.0  
**Stack:** Python 3.12 + FastAPI + Supabase + Kestra  
**Última atualização:** Janeiro 2026

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Core](#4-core)
5. [Módulos de Negócio](#5-módulos-de-negócio)
6. [Integrações](#6-integrações)
7. [Fluxos Automatizados](#7-fluxos-automatizados)
8. [Configuração e Deploy](#8-configuração-e-deploy)
9. [Padrões e Convenções](#9-padrões-e-convenções)
10. [Guia de Desenvolvimento](#10-guia-de-desenvolvimento)

---

## 1. Visão Geral

### 1.1 O que é

Backend API RESTful para sistema de gestão de clínicas médicas. Não é apenas CRUD - combina:

| Camada | Função |
|--------|--------|
| **CRUD** | Operações básicas de dados |
| **Automações** | Workflows que executam sozinhos (Kestra) |
| **Inteligência** | IA para transcrição, SOAP, OCR |
| **Tempo Real** | WebSockets, push notifications |

### 1.2 Princípios

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRINCÍPIOS DO BACKEND                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Mobile-first: API otimizada para apps mobile                │
│  2. Event-driven: Ações disparam automações                     │
│  3. Multi-tenant: Uma instância, múltiplas clínicas            │
│  4. Auditável: Tudo é rastreado e tem evidência                │
│  5. Seguro: RLS no banco, validação em toda camada             │
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
| Redis | 7 | Cache + Rate limiting |
| Kestra | Latest | Orquestração de workflows |
| OpenAI | 1.10 | Whisper (transcrição) |
| Anthropic | 0.18 | Claude (IA/SOAP) |

---

## 2. Arquitetura

### 2.1 Visão Macro

```
                                    ┌─────────────────┐
                                    │   Mobile App    │
                                    │ (React Native)  │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │    Web App      │
                                    │    (React)      │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │                   CLOUDFLARE                     │
                    │              (CDN + DDoS + WAF)                  │
                    └────────────────────────┬────────────────────────┘
                                             │
┌────────────────┐  ┌────────────────────────▼────────────────────────┐
│                │  │                                                  │
│   Evolution    │◄─┤                  FASTAPI                         │
│   (WhatsApp)   │  │                                                  │
│                │  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
└───────┬────────┘  │  │  Routers │ │ Services │ │   Integrations   │ │
        │           │  │          │ │          │ │                  │ │
        │           │  │ /auth    │ │ Auth     │ │ WhatsApp Client  │ │
        │           │  │ /pacient │ │ Paciente │ │ Whisper Client   │ │
        │           │  │ /agenda  │ │ Agenda   │ │ Claude Client    │ │
        │           │  │ /cards   │ │ Cards    │ │ OCR Client       │ │
        │           │  │ /prontu  │ │ Prontu   │ │                  │ │
        │           │  │ /financ  │ │ Financ   │ │                  │ │
        │           │  └──────────┘ └──────────┘ └──────────────────┘ │
        │           │                                                  │
        │           └────────────────────────┬────────────────────────┘
        │                                    │
        │           ┌────────────────────────▼────────────────────────┐
        │           │                   SUPABASE                       │
        │           │                                                  │
        │           │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
        │           │  │ Postgres │ │   Auth   │ │     Storage      │ │
        │           │  │   + RLS  │ │  + JWT   │ │   (Arquivos)     │ │
        │           │  └──────────┘ └──────────┘ └──────────────────┘ │
        │           │                                                  │
        │           └────────────────────────┬────────────────────────┘
        │                                    │
        │           ┌────────────────────────▼────────────────────────┐
        │           │                    KESTRA                        │
        └──────────►│             (Workflow Orchestration)             │
                    │                                                  │
                    │  ┌─────────────────────────────────────────────┐ │
                    │  │ • Lembretes de consulta                     │ │
                    │  │ • Processamento de transcrição              │ │
                    │  │ • Geração de SOAP                           │ │
                    │  │ • OCR de documentos                         │ │
                    │  │ • Conciliação financeira                    │ │
                    │  │ • Notificações e alertas                    │ │
                    │  └─────────────────────────────────────────────┘ │
                    │                                                  │
                    └─────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Requisição

```
1. Request chega via HTTPS
         │
         ▼
2. Middleware de logging registra
         │
         ▼
3. Rate limiting verifica limites
         │
         ▼
4. Auth middleware valida JWT
         │
         ▼
5. Dependency injection carrega user + permissões
         │
         ▼
6. Router direciona para handler
         │
         ▼
7. Service executa lógica de negócio
         │
         ▼
8. Database layer (Supabase) persiste
         │
         ▼
9. Response formatada retorna
         │
         ▼
10. Eventos disparam workflows (async)
```

### 2.3 Padrão de Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                          ROUTER                                  │
│  • Recebe request                                               │
│  • Valida input (Pydantic)                                      │
│  • Chama service                                                │
│  • Retorna response                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          SERVICE                                 │
│  • Lógica de negócio                                            │
│  • Validações complexas                                         │
│  • Orquestra múltiplas operações                               │
│  • Dispara eventos/webhooks                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE                                 │
│  • CRUD genérico                                                │
│  • Queries específicas via RPC                                  │
│  • Storage de arquivos                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Estrutura do Projeto

### 3.1 Árvore de Diretórios

```
backend/
│
├── app/                           # Código da aplicação
│   │
│   ├── __init__.py               # Package init
│   ├── main.py                   # Aplicação FastAPI principal
│   │
│   ├── core/                     # Núcleo compartilhado
│   │   ├── __init__.py
│   │   ├── config.py             # Configurações (env vars)
│   │   ├── database.py           # Cliente Supabase
│   │   ├── security.py           # Auth e permissões
│   │   ├── exceptions.py         # Exceções customizadas
│   │   ├── schemas.py            # Schemas base
│   │   └── utils.py              # Utilitários
│   │
│   ├── auth/                     # Módulo de autenticação
│   │   ├── __init__.py
│   │   ├── schemas.py            # DTOs de auth
│   │   ├── service.py            # Lógica de auth
│   │   └── router.py             # Endpoints /auth/*
│   │
│   ├── pacientes/                # Módulo de pacientes
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── router.py
│   │
│   ├── agenda/                   # Módulo de agenda
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── router.py
│   │
│   ├── cards/                    # Módulo Kanban
│   │   └── ...
│   │
│   ├── prontuario/               # Módulo prontuário
│   │   └── ...
│   │
│   ├── financeiro/               # Módulo financeiro
│   │   └── ...
│   │
│   ├── evidencias/               # Módulo de evidências
│   │   └── ...
│   │
│   ├── webhooks/                 # Webhooks recebidos
│   │   └── ...
│   │
│   └── integracoes/              # Clientes externos
│       ├── __init__.py
│       ├── whatsapp/
│       │   └── client.py         # Evolution API
│       ├── whisper/
│       │   └── client.py         # OpenAI Whisper
│       ├── claude/
│       │   └── client.py         # Anthropic Claude
│       └── ocr/
│           └── client.py         # Google Vision
│
├── tests/                        # Testes
│   ├── __init__.py
│   ├── conftest.py               # Fixtures pytest
│   ├── test_auth.py
│   ├── test_pacientes.py
│   └── ...
│
├── .env.example                  # Template de variáveis
├── requirements.txt              # Dependências Python
├── Dockerfile                    # Container da API
└── docker-compose.yml            # Stack local
```

### 3.2 Convenção de Nomes

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Módulo | snake_case | `pacientes/` |
| Arquivo | snake_case | `service.py` |
| Classe | PascalCase | `PacienteService` |
| Função | snake_case | `get_paciente()` |
| Constante | UPPER_SNAKE | `MAX_UPLOAD_SIZE` |
| Schema Request | PascalCase + verbo | `PacienteCreate` |
| Schema Response | PascalCase + Response | `PacienteResponse` |

---

## 4. Core

### 4.1 Config (`core/config.py`)

Gerencia configurações via variáveis de ambiente usando Pydantic Settings.

```python
from app.core.config import settings

# Acessando configurações
settings.supabase_url
settings.debug
settings.is_production
```

**Variáveis principais:**

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `APP_ENV` | str | development, staging, production |
| `DEBUG` | bool | Habilita debug e docs |
| `SUPABASE_URL` | str | URL do projeto Supabase |
| `SUPABASE_KEY` | str | Chave anon (RLS) |
| `SUPABASE_SERVICE_KEY` | str | Chave service (bypass RLS) |
| `JWT_SECRET` | str | Secret para validar tokens |
| `OPENAI_API_KEY` | str | API key do Whisper |
| `ANTHROPIC_API_KEY` | str | API key do Claude |

### 4.2 Database (`core/database.py`)

Cliente Supabase singleton com métodos auxiliares.

```python
from app.core.database import db

# SELECT com filtros
pacientes = await db.select(
    "pacientes",
    columns="id, nome, telefone",
    filters={
        "clinica_id": clinica_id,
        "status": "ativo",
        "nome__like": "João"  # ILIKE %João%
    },
    order_by="nome",
    limit=20
)

# SELECT único
paciente = await db.select_one(
    "pacientes",
    filters={"id": paciente_id}
)

# INSERT
novo = await db.insert("pacientes", {
    "nome": "João Silva",
    "cpf": "12345678900",
    ...
})

# UPDATE
await db.update(
    "pacientes",
    {"status": "inativo"},
    {"id": paciente_id}
)

# DELETE
await db.delete("pacientes", {"id": paciente_id})

# RPC (funções do banco)
resultado = await db.rpc("get_slots_disponiveis", {
    "p_medico_id": medico_id,
    "p_data": "2024-01-20"
})

# Storage
await db.upload_file("path/arquivo.pdf", file_bytes, "application/pdf")
url = await db.get_signed_url("path/arquivo.pdf", expires_in=3600)
```

**Operadores de filtro:**

| Sufixo | Operação SQL | Exemplo |
|--------|--------------|---------|
| (nenhum) | `=` | `{"status": "ativo"}` |
| `__gte` | `>=` | `{"data__gte": "2024-01-01"}` |
| `__lte` | `<=` | `{"valor__lte": 1000}` |
| `__like` | `ILIKE %x%` | `{"nome__like": "João"}` |
| `__in` | `IN (...)` | `{"status__in": ["a", "b"]}` |
| `__neq` | `!=` | `{"tipo__neq": "cancelado"}` |

### 4.3 Security (`core/security.py`)

Autenticação e autorização.

```python
from app.core.security import (
    get_current_user,
    require_permission,
    require_admin,
    require_medico,
    CurrentUser
)

# Dependency básica - usuário autenticado
@router.get("/recurso")
async def get_recurso(current_user: CurrentUser = Depends(get_current_user)):
    print(current_user.id)
    print(current_user.clinica_id)
    print(current_user.is_admin)
    print(current_user.is_medico)

# Requer permissão específica
@router.post("/pacientes")
async def create(
    current_user: CurrentUser = Depends(require_permission("pacientes", "C"))
):
    # C = Create, L = List/Read, E = Edit, X = Delete
    pass

# Requer admin
@router.delete("/clinica/users/{id}")
async def delete_user(
    current_user: CurrentUser = Depends(require_admin())
):
    pass

# Requer médico
@router.get("/prontuario/{id}")
async def get_prontuario(
    current_user: CurrentUser = Depends(require_medico())
):
    pass
```

**CurrentUser:**

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `id` | str | UUID do usuário |
| `email` | str | Email |
| `nome` | str | Nome completo |
| `clinica_id` | str | UUID da clínica |
| `perfil` | dict | Dados do perfil |
| `is_admin` | bool | É administrador? |
| `is_medico` | bool | É profissional de saúde? |
| `permissoes` | dict | Mapa de permissões |

### 4.4 Exceptions (`core/exceptions.py`)

Exceções customizadas com códigos padronizados.

```python
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    BusinessError,
    SlotUnavailableError,
    InvalidStatusTransitionError,
    EvidenceRequiredError,
    IntegrationError
)

# Uso
raise NotFoundError("Paciente")
# → 404: {"code": "not_found", "message": "Paciente não encontrado"}

raise ValidationError("CPF inválido", details=[
    {"field": "cpf", "message": "Dígito verificador incorreto"}
])
# → 422: {"code": "validation_error", ...}

raise SlotUnavailableError()
# → 409: {"code": "slot_unavailable", "message": "Horário não disponível"}

raise BusinessError("saldo_insuficiente", "Saldo insuficiente para operação")
# → 422: {"code": "saldo_insuficiente", ...}
```

### 4.5 Schemas (`core/schemas.py`)

Schemas base reutilizáveis.

```python
from app.core.schemas import (
    BaseSchema,
    DataResponse,
    PaginatedResponse,
    PaginationMeta,
    MessageResponse,
    PacienteRef,
    MedicoRef,
    ConvenioRef
)

# Response única
class PacienteResponse(BaseSchema):
    id: UUID
    nome: str

# No router
@router.get("/{id}", response_model=DataResponse[PacienteResponse])
async def get(id: UUID):
    return DataResponse(data=paciente)
# → {"data": {"id": "...", "nome": "..."}}

# Response paginada
@router.get("", response_model=PaginatedResponse[PacienteListItem])
async def list():
    return {"data": [...], "meta": {"total": 100, "page": 1, ...}}
```

### 4.6 Utils (`core/utils.py`)

Utilitários diversos.

```python
from app.core.utils import (
    # Data/hora
    now_utc,
    now_br,
    calculate_age,
    
    # Formatação
    format_cpf,      # 12345678900 → 123.456.789-00
    format_cnpj,
    format_phone,    # 11999999999 → (11) 99999-9999
    format_currency, # 1234.56 → R$ 1.234,56
    
    # Limpeza
    clean_cpf,       # Remove formatação
    clean_phone,
    
    # Validação
    is_valid_cpf,
    is_valid_cnpj,
    is_valid_email,
    
    # Hash
    hash_file,       # SHA-256 de arquivo
    
    # Paginação
    build_pagination_meta
)
```

---

## 5. Módulos de Negócio

### 5.1 Auth

**Responsabilidade:** Autenticação e gerenciamento de sessão.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/v1/auth/login` | Login com email/senha |
| POST | `/v1/auth/logout` | Encerra sessão |
| POST | `/v1/auth/refresh` | Renova token |
| GET | `/v1/auth/me` | Dados do usuário atual |
| POST | `/v1/auth/change-password` | Altera senha |
| POST | `/v1/auth/forgot-password` | Solicita reset |
| POST | `/v1/auth/reset-password` | Reseta com token |

**Fluxo de login:**

```
1. Cliente envia email + senha
2. Supabase Auth valida credenciais
3. Se válido, retorna access_token + refresh_token
4. Backend busca dados do usuário (perfil, clínica)
5. Registra tentativa de login (auditoria)
6. Retorna tokens + dados do usuário
```

**Proteção contra brute force:**

```
- 5 tentativas falhas em 30 min = bloqueio temporário
- Registra todas as tentativas (IP, user agent, etc)
- Alerta admin após 3 bloqueios do mesmo usuário
```

### 5.2 Pacientes

**Responsabilidade:** CRUD de pacientes e dados relacionados.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/pacientes` | Lista pacientes |
| GET | `/v1/pacientes/{id}` | Obtém paciente |
| POST | `/v1/pacientes` | Cria paciente |
| PATCH | `/v1/pacientes/{id}` | Atualiza paciente |
| DELETE | `/v1/pacientes/{id}` | Inativa paciente |
| POST | `/v1/pacientes/{id}/alergias` | Adiciona alergia |
| POST | `/v1/pacientes/{id}/alergias/{aid}/confirmar` | Médico confirma |
| DELETE | `/v1/pacientes/{id}/alergias/{aid}` | Remove alergia |
| POST | `/v1/pacientes/{id}/medicamentos` | Adiciona medicamento |
| DELETE | `/v1/pacientes/{id}/medicamentos/{mid}` | Remove medicamento |
| POST | `/v1/pacientes/{id}/convenios` | Vincula convênio |
| DELETE | `/v1/pacientes/{id}/convenios/{cid}` | Remove convênio |
| GET | `/v1/pacientes/{id}/historico` | Histórico médico |

**Regras de negócio:**

```
- CPF único por clínica
- Alergias precisam confirmação médica para ativar alertas críticos
- Delete é soft delete (status = inativo)
- Histórico médico só acessível por profissionais de saúde
```

### 5.3 Agenda

**Responsabilidade:** Agendamentos, slots, bloqueios.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/agenda/tipos-consulta` | Lista tipos |
| GET | `/v1/agenda/slots` | Slots disponíveis |
| GET | `/v1/agenda/agendamentos` | Lista agendamentos |
| GET | `/v1/agenda/agendamentos/{id}` | Obtém agendamento |
| POST | `/v1/agenda/agendamentos` | Cria agendamento |
| PATCH | `/v1/agenda/agendamentos/{id}/status` | Atualiza status |
| POST | `/v1/agenda/agendamentos/{id}/checkin` | Check-in |
| POST | `/v1/agenda/agendamentos/{id}/chamar` | Chama paciente |
| POST | `/v1/agenda/agendamentos/{id}/finalizar` | Finaliza |
| POST | `/v1/agenda/agendamentos/{id}/remarcar` | Remarca |
| GET | `/v1/agenda/bloqueios` | Lista bloqueios |
| POST | `/v1/agenda/bloqueios` | Cria bloqueio |
| GET | `/v1/agenda/metricas` | Métricas do dia |

**Máquina de estados:**

```
                    ┌──────────────┐
                    │   agendado   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │confirmado│ │cancelado │ │remarcado │
        └────┬─────┘ └──────────┘ └──────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌───────┐ ┌──────┐ ┌──────────┐
│faltou │ │aguard│ │          │
└───────┘ └──┬───┘ │          │
             │     │          │
             ▼     │          │
      ┌──────────┐ │          │
      │em_atend. │◄┘          │
      └────┬─────┘            │
           │                  │
           ▼                  │
      ┌──────────┐            │
      │ atendido │            │
      └──────────┘            │
```

**Eventos disparados:**

| Transição | Evento | Ação |
|-----------|--------|------|
| → confirmado | `agendamento.confirmado` | Atualiza card Kanban |
| → aguardando | `paciente.checkin` | Notifica médico, move card |
| → em_atendimento | `paciente.chamado` | Cria consulta, move card |
| → atendido | `consulta.finalizada` | Gera conta a receber |
| → faltou | `paciente.faltou` | Libera slot, notifica |
| → cancelado | `agendamento.cancelado` | Libera slot, notifica |

### 5.4 Cards (Kanban)

**Responsabilidade:** Gestão visual do fluxo de atendimento.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/cards` | Lista cards por fase/coluna |
| GET | `/v1/cards/{id}` | Obtém card completo |
| POST | `/v1/cards/{id}/mover` | Move para coluna |
| POST | `/v1/cards/{id}/checklist/{item}/concluir` | Conclui item |
| POST | `/v1/cards/{id}/checklist` | Adiciona item |
| POST | `/v1/cards/{id}/documentos` | Upload de documento |
| GET | `/v1/cards/{id}/historico` | Histórico de movimentações |

**Fases e colunas:**

```
FASE 0: Pré-agendamento
├── agendado

FASE 1: Pré-consulta (D-7 a D-1)
├── pendente_anamnese
├── pendente_confirmacao
└── pronto

FASE 2: Dia da consulta
├── aguardando_checkin
├── em_espera
├── em_atendimento
└── finalizado

FASE 3: Pós-consulta
├── pendente_documentos
├── pendente_pagamento
└── concluido
```

**Automações:**

```
Card criado automaticamente ao agendar
Card move automaticamente baseado em eventos:
  - Paciente confirmou WhatsApp → move coluna
  - Paciente enviou exame → atualiza checklist
  - Paciente fez check-in → muda fase
  - Médico finalizou → gera financeiro
```

### 5.5 Prontuário

**Responsabilidade:** Consultas, SOAP, receitas, atestados, exames.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/prontuario/consultas/{id}` | Obtém consulta |
| GET | `/v1/prontuario/consultas/{id}/briefing` | Briefing do paciente |
| POST | `/v1/prontuario/consultas/{id}/transcricao/iniciar` | Inicia transcrição |
| GET | `/v1/prontuario/consultas/{id}/transcricao` | Obtém transcrição |
| POST | `/v1/prontuario/consultas/{id}/soap/gerar` | Gera SOAP com IA |
| GET | `/v1/prontuario/consultas/{id}/soap` | Obtém SOAP |
| PATCH | `/v1/prontuario/consultas/{id}/soap` | Edita SOAP |
| POST | `/v1/prontuario/consultas/{id}/soap/assinar` | Assina SOAP |
| POST | `/v1/prontuario/consultas/{id}/receitas` | Cria receita |
| POST | `/v1/prontuario/consultas/{id}/receitas/{rid}/emitir` | Gera PDF |
| POST | `/v1/prontuario/consultas/{id}/receitas/{rid}/enviar` | Envia WhatsApp |
| POST | `/v1/prontuario/consultas/{id}/atestados` | Cria atestado |
| POST | `/v1/prontuario/consultas/{id}/exames` | Solicita exame |
| POST | `/v1/prontuario/consultas/{id}/encaminhamentos` | Encaminha |
| POST | `/v1/prontuario/consultas/{id}/retorno` | Agenda retorno |

**Fluxo de transcrição + SOAP:**

```
1. Médico envia áudio da consulta
         │
         ▼
2. API salva áudio no Storage
         │
         ▼
3. Dispara workflow Kestra "transcricao-consulta"
         │
         ▼
4. Kestra chama Whisper API
         │
         ▼
5. Transcrição salva no banco
         │
         ▼
6. Médico pode gerar SOAP
         │
         ▼
7. API chama Claude com:
   - Transcrição
   - Dados do paciente
   - Alergias/medicamentos
   - Anamnese
         │
         ▼
8. Claude retorna SOAP estruturado + CIDs sugeridos
         │
         ▼
9. Médico revisa e assina
```

### 5.6 Financeiro

**Responsabilidade:** Contas a pagar/receber, conciliação, relatórios.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/financeiro/dashboard` | Resumo financeiro |
| GET | `/v1/financeiro/fluxo-caixa` | Fluxo de caixa |
| GET | `/v1/financeiro/dre` | DRE do mês |
| GET | `/v1/financeiro/contas-pagar` | Lista contas a pagar |
| POST | `/v1/financeiro/contas-pagar` | Cria conta |
| POST | `/v1/financeiro/contas-pagar/{id}/documento` | Upload NF/boleto |
| POST | `/v1/financeiro/contas-pagar/{id}/aprovar` | Aprova pagamento |
| POST | `/v1/financeiro/contas-pagar/{id}/pagar` | Registra pagamento |
| GET | `/v1/financeiro/contas-receber` | Lista contas a receber |
| POST | `/v1/financeiro/contas-receber/{id}/receber` | Registra recebimento |
| GET | `/v1/financeiro/contas-bancarias` | Lista contas |
| POST | `/v1/financeiro/contas-bancarias/{id}/importar` | Importa OFX |
| GET | `/v1/financeiro/contas-bancarias/{id}/extrato` | Lista extrato |
| POST | `/v1/financeiro/extrato/{id}/conciliar` | Concilia transação |

**Fluxo de conta a pagar com OCR:**

```
1. Usuário faz upload de NF/boleto
         │
         ▼
2. API salva arquivo
         │
         ▼
3. Dispara workflow "processar-documento-financeiro"
         │
         ▼
4. Kestra chama Google Vision (OCR)
         │
         ▼
5. Claude analisa texto extraído e identifica:
   - Fornecedor
   - Valor
   - Vencimento
   - Código de barras
         │
         ▼
6. Sistema preenche conta automaticamente
         │
         ▼
7. Usuário só confirma
```

**Conciliação automática:**

```
1. Importa extrato OFX
         │
         ▼
2. Para cada transação:
   │
   ├─► Busca contas pagar/receber com:
   │   - Valor igual ou próximo (±1%)
   │   - Data próxima (±3 dias)
   │   - Nome similar (fuzzy match)
   │
   ├─► Calcula score de confiança
   │
   └─► Se score > 90%: sugere match
         │
         ▼
3. Usuário aprova sugestões em lote
```

### 5.7 Evidências

**Responsabilidade:** Gerenciar documentos comprobatórios.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/evidencias` | Lista evidências |
| POST | `/v1/evidencias` | Upload de evidência |
| POST | `/v1/evidencias/{id}/validar` | Valida evidência |
| GET | `/v1/evidencias/verificar` | Verifica obrigatórias |

**Regras:**

```
Antes de executar certas ações, sistema verifica evidências:

PAGAR CONTA:
  - Exige: nota_fiscal OU boleto
  - Exige: comprovante_pagamento

EMITIR RECEITA CONTROLADA:
  - Exige: consulta assinada

FINALIZAR CONSULTA:
  - Exige: SOAP assinado (se tipo exigir)
```

### 5.8 Webhooks

**Responsabilidade:** Receber callbacks de sistemas externos.

**Endpoints:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/v1/webhooks/whatsapp` | Mensagens WhatsApp |
| POST | `/v1/webhooks/kestra` | Callbacks de workflows |
| POST | `/v1/webhooks/convenio` | Retornos de convênios |

**Webhook WhatsApp:**

```python
@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    # Valida assinatura
    # Processa mensagem:
    #   - Confirmação: "SIM" → confirma agendamento
    #   - Cancelamento: "CANCELAR" → cancela
    #   - Mídia: foto/PDF → processa como exame
    #   - Texto livre: salva como observação
```

---

## 6. Integrações

### 6.1 WhatsApp (Evolution API)

**Arquivo:** `integracoes/whatsapp/client.py`

```python
from app.integracoes.whatsapp.client import whatsapp_client

# Enviar texto
await whatsapp_client.send_text(
    to="11999999999",
    message="Olá! Sua consulta está confirmada."
)

# Enviar template
await whatsapp_client.send_template(
    to="11999999999",
    template_name="confirmacao_consulta",
    variables=["20/01/2024", "14:00", "Dr. João Silva"]
)

# Enviar documento
await whatsapp_client.send_document(
    to="11999999999",
    document_url="https://storage.../receita.pdf",
    filename="receita.pdf",
    caption="Sua receita médica"
)
```

**Templates disponíveis:**

| Nome | Variáveis | Uso |
|------|-----------|-----|
| `confirmacao_consulta` | data, hora, médico | Confirmar agendamento |
| `lembrete_consulta` | data, hora, médico | D-1 lembrete |
| `paciente_chamado` | consultório | Chamar para atendimento |
| `exame_solicitado` | lista de exames | Pedir envio de exames |
| `receita_disponivel` | link | Enviar receita |
| `anamnese_pendente` | link | Pedir preenchimento |

### 6.2 Whisper (OpenAI)

**Arquivo:** `integracoes/whisper/client.py`

```python
from app.integracoes.whisper.client import whisper_client

# Transcrição básica
result = await whisper_client.transcribe(
    audio_file=audio_bytes,
    filename="consulta.mp3",
    language="pt"
)
# result = {"text": "...", "duration": 1200, "segments": [...]}

# Transcrição otimizada para consulta médica
result = await whisper_client.transcribe_medical_consultation(
    audio_file=audio_bytes,
    patient_info={
        "queixa": "Dor de cabeça",
        "medicamentos": ["Losartana", "Metformina"]
    }
)
```

**Configurações:**

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| Model | whisper-1 | Modelo utilizado |
| Language | pt | Português brasileiro |
| Response format | verbose_json | Inclui timestamps |

### 6.3 Claude (Anthropic)

**Arquivo:** `integracoes/claude/client.py`

```python
from app.integracoes.claude.client import claude_client

# Gerar SOAP
soap = await claude_client.generate_soap(
    transcricao="Paciente refere dor de cabeça...",
    paciente_info={
        "nome": "João Silva",
        "idade": 45,
        "sexo": "M",
        "alergias": [{"substancia": "Dipirona"}],
        "medicamentos": [{"nome": "Losartana", "dosagem": "50mg"}]
    },
    anamnese={
        "queixa_principal": "Cefaleia há 3 dias"
    }
)
# soap = {
#   "subjetivo": "...",
#   "objetivo": "...",
#   "avaliacao": "...",
#   "plano": "...",
#   "cids_sugeridos": [...]
# }

# Analisar exame
analise = await claude_client.analyze_exam_results(
    exam_text="Hemoglobina: 10.5 g/dL...",
    exam_type="Hemograma",
    patient_context="Paciente diabético em uso de Metformina"
)

# Sugerir prescrição (⚠️ requer validação médica)
sugestao = await claude_client.suggest_prescription(
    diagnostico="Cefaleia tensional",
    paciente_info={...}
)
```

### 6.4 OCR (Google Vision)

**Arquivo:** `integracoes/ocr/client.py` (a implementar)

```python
from app.integracoes.ocr.client import ocr_client

# Extrair texto de imagem/PDF
text = await ocr_client.extract_text(
    file_bytes=image_bytes,
    mime_type="image/jpeg"
)

# Extrair dados estruturados de NF
dados = await ocr_client.extract_invoice_data(file_bytes)
# dados = {
#   "fornecedor": "ABC Ltda",
#   "cnpj": "12.345.678/0001-99",
#   "valor": 1500.00,
#   "data_emissao": "2024-01-15",
#   "codigo_barras": "..."
# }
```

---

## 7. Fluxos Automatizados

### 7.1 Visão Geral

O backend dispara workflows no Kestra que executam tarefas assíncronas.

```python
# No service, após ação
async def create_agendamento(...):
    # Cria agendamento
    agendamento = await db.insert(...)
    
    # Dispara workflow
    await trigger_workflow("agendamento-criado", {
        "agendamento_id": agendamento["id"],
        "paciente_telefone": paciente["telefone"],
        "data": agendamento["data"]
    })
```

### 7.2 Workflows Principais

| Workflow | Trigger | Ações |
|----------|---------|-------|
| `confirmacao-consulta` | Agendamento criado | Envia WhatsApp de confirmação |
| `lembrete-d1` | Cron D-1 | Envia lembrete |
| `anamnese-pendente` | Cron D-3 | Envia link da anamnese |
| `processar-mensagem-whatsapp` | Webhook WhatsApp | Processa resposta do paciente |
| `transcrever-audio` | Upload de áudio | Whisper → salva transcrição |
| `gerar-soap` | Solicitação médico | Claude → SOAP estruturado |
| `processar-documento-financeiro` | Upload NF/boleto | OCR → preenche conta |
| `conciliar-extrato` | Importação OFX | Match automático |
| `alertas-vencimento` | Cron diário | Notifica contas vencendo |

### 7.3 Padrão de Trigger

```python
import httpx
from app.core.config import settings

async def trigger_workflow(workflow_id: str, inputs: dict):
    """Dispara workflow no Kestra."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.kestra_api_url}/executions/trigger",
            json={
                "namespace": settings.kestra_namespace,
                "flowId": workflow_id,
                "inputs": inputs
            },
            timeout=10.0
        )
```

---

## 8. Configuração e Deploy

### 8.1 Variáveis de Ambiente

```bash
# App
APP_NAME=clinica-api
APP_ENV=production
DEBUG=false
API_VERSION=v1

# Server
HOST=0.0.0.0
PORT=8000

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# APIs Externas
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# WhatsApp
EVOLUTION_API_URL=https://api.evolution.com
EVOLUTION_API_KEY=...
EVOLUTION_INSTANCE=clinica

# Kestra
KESTRA_API_URL=http://kestra:8080/api/v1
KESTRA_NAMESPACE=clinica

# Storage
STORAGE_BUCKET=clinica-files
MAX_UPLOAD_SIZE_MB=10

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS
CORS_ORIGINS=["https://app.clinica.com"]

# Sentry (opcional)
SENTRY_DSN=https://...
```

### 8.2 Docker

**Desenvolvimento:**

```bash
# Sobe toda a stack
docker-compose up -d

# Logs
docker-compose logs -f api

# Rebuild
docker-compose up -d --build api
```

**Produção (Railway):**

```bash
# railway.json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 8.3 Health Check

```python
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 8.4 Documentação da API

- **Swagger UI:** `/docs` (apenas em desenvolvimento)
- **ReDoc:** `/redoc` (apenas em desenvolvimento)

---

## 9. Padrões e Convenções

### 9.1 Estrutura de um Módulo

```
modulo/
├── __init__.py      # Exports públicos
├── schemas.py       # Pydantic models (Request/Response)
├── service.py       # Lógica de negócio
├── router.py        # Endpoints FastAPI
└── utils.py         # Helpers específicos (opcional)
```

### 9.2 Schemas

```python
# schemas.py

# Base (campos compartilhados)
class PacienteBase(BaseSchema):
    nome: str
    cpf: str

# Create (campos para criação)
class PacienteCreate(PacienteBase):
    data_nascimento: date

# Update (campos opcionais)
class PacienteUpdate(BaseSchema):
    nome: Optional[str] = None
    telefone: Optional[str] = None

# Response (campos de saída)
class PacienteResponse(PacienteBase):
    id: UUID
    created_at: datetime

# List Item (versão resumida)
class PacienteListItem(BaseSchema):
    id: UUID
    nome: str
    telefone: str
```

### 9.3 Service

```python
# service.py

class PacienteService:
    """Docstring explicando responsabilidade."""
    
    async def list(self, clinica_id: str, **filters) -> dict:
        """Lista com paginação."""
        pass
    
    async def get(self, id: str, clinica_id: str) -> PacienteResponse:
        """Obtém um registro."""
        pass
    
    async def create(self, data: PacienteCreate, clinica_id: str) -> PacienteResponse:
        """Cria registro."""
        pass
    
    async def update(self, id: str, data: PacienteUpdate, clinica_id: str) -> PacienteResponse:
        """Atualiza registro."""
        pass
    
    async def delete(self, id: str, clinica_id: str) -> None:
        """Remove (soft delete)."""
        pass

# Instância singleton
paciente_service = PacienteService()
```

### 9.4 Router

```python
# router.py

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.get(
    "",
    response_model=PaginatedResponse[PacienteListItem],
    summary="Listar Pacientes",
    description="Lista pacientes com filtros e paginação"
)
async def list_pacientes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("pacientes", "L"))
):
    """
    Docstring detalhada para Swagger.
    
    - **page**: Número da página
    - **per_page**: Itens por página
    - **search**: Busca por nome
    """
    return await paciente_service.list(
        clinica_id=current_user.clinica_id,
        page=page,
        per_page=per_page,
        search=search
    )
```

### 9.5 Tratamento de Erros

```python
# Sempre use exceções tipadas
from app.core.exceptions import NotFoundError, ValidationError

# No service
async def get(self, id: str, clinica_id: str):
    result = await db.select_one("tabela", filters={"id": id})
    
    if not result:
        raise NotFoundError("Paciente")
    
    if result["clinica_id"] != clinica_id:
        raise AuthorizationError("Sem acesso a este recurso")
    
    return result
```

### 9.6 Logging

```python
import structlog

logger = structlog.get_logger()

# No service
async def create(self, data):
    logger.info("Criando paciente", nome=data.nome)
    
    try:
        result = await db.insert(...)
        logger.info("Paciente criado", id=result["id"])
        return result
    except Exception as e:
        logger.error("Erro ao criar paciente", error=str(e))
        raise
```

---

## 10. Guia de Desenvolvimento

### 10.1 Setup Local

```bash
# Clone
git clone <repo>
cd backend

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Dependências
pip install -r requirements.txt

# Variáveis
cp .env.example .env
# Edite .env com suas credenciais

# Rodar
uvicorn app.main:app --reload

# Ou com Docker
docker-compose up -d
```

### 10.2 Adicionando um Módulo

```bash
# 1. Criar estrutura
mkdir -p app/novo_modulo
touch app/novo_modulo/{__init__,schemas,service,router}.py

# 2. Implementar schemas.py
# 3. Implementar service.py
# 4. Implementar router.py

# 5. Registrar no main.py
from app.novo_modulo.router import router as novo_router
app.include_router(novo_router, prefix="/v1")
```

### 10.3 Testes

```bash
# Rodar todos
pytest

# Com coverage
pytest --cov=app --cov-report=html

# Arquivo específico
pytest tests/test_pacientes.py

# Teste específico
pytest tests/test_pacientes.py::test_create_paciente
```

### 10.4 Linting

```bash
# Formatação
black app/
isort app/

# Lint
flake8 app/

# Type check
mypy app/
```

### 10.5 Git Workflow

```bash
# Branch naming
feature/adicionar-modulo-x
fix/corrigir-bug-y
refactor/melhorar-z

# Commit messages
feat: adiciona endpoint de receitas
fix: corrige validação de CPF
refactor: extrai lógica para service
docs: atualiza README
test: adiciona testes de agenda
```

---

## Anexos

### A. Códigos de Erro

| Código | HTTP | Descrição |
|--------|------|-----------|
| `token_invalid` | 401 | Token JWT inválido |
| `token_missing` | 401 | Token não enviado |
| `invalid_credentials` | 401 | Email/senha incorretos |
| `user_blocked` | 401 | Usuário bloqueado |
| `too_many_attempts` | 429 | Muitas tentativas |
| `permission_denied` | 403 | Sem permissão |
| `clinica_mismatch` | 403 | Recurso de outra clínica |
| `not_found` | 404 | Recurso não encontrado |
| `validation_error` | 422 | Dados inválidos |
| `conflict` | 409 | Registro duplicado |
| `slot_unavailable` | 409 | Horário ocupado |
| `invalid_status_transition` | 422 | Transição inválida |
| `evidence_required` | 422 | Falta evidência |
| `integration_error` | 502 | Erro em API externa |
| `internal_error` | 500 | Erro interno |

### B. Permissões

```
Formato: CLEX (Create, List, Edit, eXclude)

Módulos:
- agenda
- pacientes
- prontuario
- financeiro
- configuracoes
- relatorios

Exemplo perfil Recepção:
{
  "agenda": "CLE",      // Pode criar, listar, editar
  "pacientes": "CLE",   // Pode criar, listar, editar
  "prontuario": "L",    // Só pode listar
  "financeiro": "L",    // Só pode listar
  "configuracoes": "",  // Sem acesso
  "relatorios": "L"     // Só pode listar
}
```

### C. Rate Limits

| Endpoint | Limite | Janela |
|----------|--------|--------|
| Geral (autenticado) | 100 req | 1 min |
| Geral (anônimo) | 20 req | 1 min |
| Login | 5 tentativas | 30 min |
| Upload | 10 req | 1 min |
| Webhooks | 1000 req | 1 min |

---

**Documento gerado em:** Janeiro 2026  
**Versão:** 1.0  
**Mantido por:** Equipe de Desenvolvimento
