# API Documentation
## Sistema de Gestão de Clínicas

**Versão:** 1.1  
**Base URL:** `http://localhost:8080/v1` (dev) | `https://api.clinica.com/v1` (prod)  
**Formato:** JSON  
**Autenticação:** Bearer Token (Supabase Auth)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Autenticação](#2-autenticação)
3. [Padrões e Convenções](#3-padrões-e-convenções)
4. [Auth](#4-auth)
5. [Clínicas](#5-clínicas)
6. [Pacientes](#6-pacientes)
7. [Agenda](#7-agenda)
8. [Cards (Kanban)](#8-cards-kanban)
9. [Evidências](#9-evidências)
10. [Schemas](#10-schemas)
11. [Códigos de Erro](#11-códigos-de-erro)

---

## 1. Visão Geral

### 1.1 Arquitetura

```
Cliente (React/Mobile)
    │
    ▼ HTTP/JSON + Bearer Token
┌─────────────────────────────────────────┐
│              FastAPI                     │
│  ┌─────────────────────────────────┐    │
│  │           Routers               │    │
│  │  /auth  /pacientes  /agenda ... │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │          Services               │    │
│  │   current_user + get_db(token)  │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │    Supabase Client (auth)       │    │
│  │       RLS automático            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
    │
    ▼
Supabase (PostgreSQL + Auth + RLS)
```

### 1.2 Endpoints Disponíveis

| Módulo | Prefixo | Status |
|--------|---------|--------|
| Auth | `/v1/auth` | ✅ Implementado |
| Clínicas | `/v1/clinica` | ✅ Implementado |
| Pacientes | `/v1/pacientes` | ✅ Implementado |
| Agenda | `/v1/agenda` | ✅ Implementado |
| Cards/Kanban | `/v1/cards` | ✅ Implementado |
| Evidências | `/v1/evidencias` | ⚠️ Parcial (tabela não existe) |

---

## 2. Autenticação

### 2.1 Fluxo

```
1. POST /auth/login com {email, senha}
2. Recebe access_token + refresh_token
3. Envia access_token em todas as requisições
4. Token expira em ~1 hora
5. Use refresh_token para renovar
```

### 2.2 Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 2.3 Erros de Autenticação

| Código | Erro | Descrição |
|--------|------|-----------|
| 401 | `token_invalid` | Token inválido ou expirado |
| 401 | `token_missing` | Header Authorization ausente |
| 403 | `permission_denied` | Sem permissão para recurso |

---

## 3. Padrões e Convenções

### 3.1 Métodos HTTP

| Método | Uso |
|--------|-----|
| GET | Leitura |
| POST | Criação |
| PATCH | Atualização parcial |
| DELETE | Exclusão (soft delete) |

### 3.2 Códigos de Resposta

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Criado |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Não encontrado |
| 409 | Conflito (duplicado) |
| 422 | Erro de validação |
| 500 | Erro interno |

### 3.3 Formato de Resposta

**Sucesso (lista paginada):**
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

**Sucesso (item único):**
```json
{
  "id": "uuid",
  "nome": "...",
  ...
}
```

**Erro:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Dados inválidos"
  }
}
```

### 3.4 Paginação

```
GET /pacientes?page=1&per_page=20&sort=nome&order=asc
```

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| page | int | 1 | Página atual |
| per_page | int | 20 | Itens por página (max 100) |
| sort | string | created_at | Campo para ordenar |
| order | string | asc | asc ou desc |

---

## 4. Auth

### 4.1 Login

```http
POST /auth/login
```

**Request:**
```json
{
  "email": "usuario@clinica.com",
  "senha": "senha123"
}
```

> ⚠️ **Nota:** O campo é `senha`, não `password`

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "nome": "Dr. João Silva",
    "email": "joao@clinica.com",
    "clinica_id": "uuid",
    "perfil": {
      "id": "uuid",
      "nome": "Médico",
      "is_admin": false,
      "permissoes": {...}
    }
  }
}
```

---

### 4.2 Me (Usuário Atual)

```http
GET /auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "nome": "Dr. João Silva",
  "email": "joao@clinica.com",
  "clinica_id": "uuid",
  "perfil": {...}
}
```

---

### 4.3 Refresh Token

```http
POST /auth/refresh
```

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 4.4 Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

---

## 5. Clínicas

### 5.1 Obter Clínica Atual

```http
GET /clinica
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "nome": "Clínica Saúde",
  "cnpj": "12345678000199",
  "telefone": "1133334444",
  "email": "contato@clinica.com",
  "endereco": "Rua das Flores, 123",
  "cidade": "São Paulo",
  "uf": "SP"
}
```

---

### 5.2 Atualizar Clínica

```http
PATCH /clinica
Authorization: Bearer <token>
```

**Permissão:** `configuracoes: E`

**Request:**
```json
{
  "nome": "Clínica Saúde Plus",
  "telefone": "1133335555"
}
```

---

### 5.3 Configurações

```http
GET /clinica/configuracoes
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "clinica_id": "uuid",
  "antecedencia_minima_agendamento": 2,
  "antecedencia_maxima_agendamento": 90,
  "permitir_agendamento_online": true,
  "enviar_confirmacao_automatica": true,
  "enviar_lembrete_d1": true,
  "enviar_lembrete_d3": true
}
```

```http
PATCH /clinica/configuracoes
Authorization: Bearer <token>
```

**Request:**
```json
{
  "enviar_lembrete_d1": true
}
```

---

### 5.4 Perfis

```http
GET /clinica/perfis
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": "uuid",
    "nome": "Administrador",
    "descricao": "Acesso total",
    "is_admin": true,
    "is_medico": false,
    "is_sistema": true,
    "permissoes": {
      "agenda": "CLEX",
      "pacientes": "CLEX",
      "prontuario": "CLEX"
    }
  }
]
```

```http
POST /clinica/perfis
Authorization: Bearer <token>
```

**Request:**
```json
{
  "nome": "Recepção",
  "descricao": "Acesso à agenda",
  "permissoes": {
    "agenda": "CLE",
    "pacientes": "L"
  }
}
```

---

## 6. Pacientes

### 6.1 Listar Pacientes

```http
GET /pacientes
Authorization: Bearer <token>
```

**Query params:**
- `page`: Página (default: 1)
- `per_page`: Itens por página (default: 20, max: 100)
- `search`: Busca por nome
- `status`: Filtrar por status

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Maria Silva",
      "cpf": "12345678900",
      "data_nascimento": "1990-05-15",
      "idade": 35,
      "sexo": "F",
      "telefone": "11999999999",
      "email": "maria@email.com",
      "status": "ativo",
      "tem_alergias": true
    }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  }
}
```

---

### 6.2 Obter Paciente

```http
GET /pacientes/{paciente_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "nome": "Maria Silva",
  "nome_social": null,
  "cpf": "12345678900",
  "rg": "123456789",
  "data_nascimento": "1990-05-15",
  "idade": 35,
  "sexo": "F",
  "telefone": "11999999999",
  "telefone_secundario": null,
  "email": "maria@email.com",
  "aceita_whatsapp": true,
  "aceita_email": true,
  "logradouro": "Rua das Flores",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP",
  "cep": "01234567",
  "tipo_sanguineo": "O+",
  "status": "ativo",
  "alergias": [...],
  "medicamentos": [...],
  "convenios": [...]
}
```

---

### 6.3 Criar Paciente

```http
POST /pacientes
Authorization: Bearer <token>
```

**Permissão:** `pacientes: C`

**Request:**
```json
{
  "nome": "João Santos",
  "data_nascimento": "1985-10-20",
  "sexo": "M",
  "telefone": "11988888888",
  "email": "joao@email.com"
}
```

> **Nota:** CPF é opcional e validado se informado

---

### 6.4 Atualizar Paciente

```http
PATCH /pacientes/{paciente_id}
Authorization: Bearer <token>
```

**Request:**
```json
{
  "telefone": "11977777777",
  "email": "novo@email.com"
}
```

---

## 7. Agenda

### 7.1 Tipos de Consulta

```http
GET /agenda/tipos-consulta
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Consulta Padrão",
      "descricao": "Consulta médica padrão",
      "duracao_minutos": 30,
      "valor_particular": 250.00,
      "cor": "#3B82F6",
      "permite_encaixe": true,
      "antecedencia_minima_horas": 2,
      "antecedencia_maxima_dias": 90,
      "ativo": true
    }
  ]
}
```

---

### 7.2 Listar Agendamentos

```http
GET /agenda/agendamentos
Authorization: Bearer <token>
```

**Query params:**
- `data`: Data específica (YYYY-MM-DD)
- `data_inicio`: Início do período
- `data_fim`: Fim do período
- `medico_id`: Filtrar por médico
- `paciente_id`: Filtrar por paciente
- `status`: agendado, confirmado, aguardando, em_atendimento, atendido, faltou, cancelado

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "paciente": {
        "id": "uuid",
        "nome": "Maria Silva"
      },
      "medico": {
        "id": "uuid",
        "nome": "Dr. João"
      },
      "tipo_consulta": {
        "id": "uuid",
        "nome": "Consulta Padrão",
        "cor": "#3B82F6"
      },
      "data": "2026-01-20",
      "hora_inicio": "09:00",
      "hora_fim": "09:30",
      "status": "agendado",
      "forma_pagamento": "particular",
      "valor_previsto": 250.00
    }
  ],
  "meta": {...}
}
```

---

### 7.3 Métricas da Agenda

```http
GET /agenda/metricas
Authorization: Bearer <token>
```

**Query params:**
- `data`: Data (default: hoje)
- `medico_id`: Filtrar por médico

**Response (200):**
```json
{
  "data": "2026-01-15",
  "total_agendados": 15,
  "confirmados": 10,
  "atendidos": 5,
  "faltaram": 1,
  "aguardando": 2,
  "em_atendimento": 1,
  "taxa_ocupacao": 75.0
}
```

---

### 7.4 Bloqueios de Agenda

```http
GET /agenda/bloqueios
Authorization: Bearer <token>
```

**Query params:**
- `medico_id`: Filtrar por médico
- `data_inicio`: Início do período
- `data_fim`: Fim do período

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "medico_id": "uuid",
      "medico_nome": "Dr. João",
      "data_inicio": "2026-02-01",
      "data_fim": "2026-02-15",
      "motivo": "Férias",
      "tipo": "ferias"
    }
  ]
}
```

---

## 8. Cards (Kanban)

### 8.1 Listar Cards

```http
GET /cards
Authorization: Bearer <token>
```

**Query params:**
- `data`: Filtrar por data
- `medico_id`: Filtrar por médico
- `paciente_id`: Filtrar por paciente
- `status`: ativo, concluido, cancelado
- `fase`: 0, 1, 2, 3

---

### 8.2 Kanban por Fase

```http
GET /cards/kanban/{fase}
Authorization: Bearer <token>
```

**Fases:**
- `0`: Agendados (futuro)
- `1`: Pré-Consulta (D-3 a D-1)
- `2`: Dia da Consulta
- `3`: Pós-Consulta

**Query params:**
- `data`: Filtrar por data
- `medico_id`: Filtrar por médico

**Response (200):**
```json
{
  "fase": 2,
  "colunas": {
    "aguardando_checkin": [
      {
        "id": "uuid",
        "fase": 2,
        "coluna": "aguardando_checkin",
        "status": "ativo",
        "prioridade": "normal",
        "paciente_nome": "Maria Silva",
        "paciente_telefone": "11999999999",
        "data_agendamento": "2026-01-15",
        "hora_agendamento": "09:00",
        "tipo_consulta": "Consulta Padrão",
        "medico_id": "uuid"
      }
    ],
    "em_espera": [],
    "em_atendimento": [],
    "finalizado": []
  },
  "total_cards": 5
}
```

**Colunas por fase:**

| Fase | Colunas |
|------|---------|
| 0 | agendado |
| 1 | pendente_anamnese, pendente_confirmacao, pronto |
| 2 | aguardando_checkin, em_espera, em_atendimento, finalizado |
| 3 | pendente_documentos, pendente_pagamento, concluido |

---

### 8.3 Mover Card

```http
POST /cards/{card_id}/mover
Authorization: Bearer <token>
```

**Request:**
```json
{
  "coluna": "em_espera",
  "posicao": 0
}
```

---

### 8.4 Checklist do Card

```http
GET /cards/{card_id}/checklist
Authorization: Bearer <token>
```

```http
PATCH /cards/{card_id}/checklist/{item_id}
Authorization: Bearer <token>
```

**Request:**
```json
{
  "concluido": true
}
```

---

## 9. Evidências

> ⚠️ **Nota:** A tabela `evidencias` ainda não existe no banco. Os endpoints retornam listas vazias.

### 9.1 Listar Evidências

```http
GET /evidencias
Authorization: Bearer <token>
```

**Query params:**
- `entidade`: Tabela (contas_pagar, receitas, etc)
- `entidade_id`: ID do registro
- `tipo`: Tipo de evidência
- `categoria`: documento, api_response, comprovante, etc
- `status`: ativo, substituido, invalido

---

### 9.2 Por Entidade

```http
GET /evidencias/entidade/{entidade}/{entidade_id}
Authorization: Bearer <token>
```

---

### 9.3 Verificar Obrigatórias

```http
GET /evidencias/verificar/{entidade}/{entidade_id}/{acao}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "pode_executar": true,
  "evidencias_faltando": [],
  "mensagem": "OK"
}
```

---

## 10. Schemas

### 10.1 PaginationMeta

```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

### 10.2 Enums

**StatusAgendamento:**
```
agendado | confirmado | aguardando | em_atendimento | atendido | faltou | cancelado
```

**StatusCard:**
```
ativo | concluido | cancelado
```

**FaseCard:**
```
0 | 1 | 2 | 3
```

**Sexo:**
```
M | F | O
```

**FormaPagamento:**
```
particular | convenio
```

---

## 11. Códigos de Erro

| Código | HTTP | Descrição |
|--------|------|-----------|
| `token_invalid` | 401 | Token inválido ou expirado |
| `token_missing` | 401 | Token não fornecido |
| `invalid_credentials` | 401 | Email ou senha incorretos |
| `permission_denied` | 403 | Sem permissão |
| `not_found` | 404 | Recurso não encontrado |
| `validation_error` | 422 | Erro de validação |
| `conflict` | 409 | Registro duplicado |
| `internal_error` | 500 | Erro interno |

---

## Apêndice: Testando a API

### Via Script

```bash
cd backend
python test_api.py
```

### Via cURL

```bash
# Login
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@clinica.com","senha":"123456"}'

# Listar pacientes (com token)
curl http://localhost:8080/v1/pacientes \
  -H "Authorization: Bearer <token>"
```

### Via Swagger

Acesse: `http://localhost:8080/docs`

---

**Documento atualizado em:** Janeiro 2026  
**Versão:** 1.1  
**Mudanças:**
- Campo de login é `senha` (não `password`)
- Endpoints testados e funcionando
- Documentados módulos implementados
