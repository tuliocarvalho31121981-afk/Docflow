# API Documentation
## Sistema de Gestão de Clínicas

**Versão:** 1.0  
**Base URL:** `https://api.clinica.com/v1`  
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
9. [Prontuário](#9-prontuário)
10. [Financeiro](#10-financeiro)
11. [Evidências](#11-evidências)
12. [Webhooks](#12-webhooks)
13. [Schemas](#13-schemas)

---

## 1. Visão Geral

### 1.1 Arquitetura

```
Cliente (React)
    │
    ▼ HTTP/JSON
┌─────────────────────────────────────────┐
│              FastAPI                     │
│  ┌─────────────────────────────────┐    │
│  │           Routers               │    │
│  │  /auth  /pacientes  /agenda ... │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │          Services               │    │
│  │   Lógica de negócio             │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │         Supabase Client         │    │
│  │   DB + Auth + Storage           │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
    │
    ▼
Supabase (PostgreSQL + Auth + Storage)
```

### 1.2 Versionamento

- API versionada na URL: `/v1/`, `/v2/`
- Versão atual: `v1`
- Breaking changes = nova versão

### 1.3 Rate Limiting

| Tipo | Limite |
|------|--------|
| Por usuário | 100 req/min |
| Por IP (não autenticado) | 20 req/min |
| Upload de arquivos | 10 req/min |

---

## 2. Autenticação

### 2.1 Fluxo

```
1. Cliente faz login via Supabase Auth
2. Recebe access_token + refresh_token
3. Envia access_token no header Authorization
4. Backend valida token com Supabase
5. Backend verifica permissões do perfil
```

### 2.2 Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Clinica-ID: <uuid>  # Opcional, para admins multi-clínica
```

### 2.3 Erros de Autenticação

| Código | Erro | Descrição |
|--------|------|-----------|
| 401 | `token_invalid` | Token inválido ou expirado |
| 401 | `token_missing` | Header Authorization ausente |
| 403 | `permission_denied` | Sem permissão para recurso |
| 403 | `clinica_mismatch` | Recurso de outra clínica |

---

## 3. Padrões e Convenções

### 3.1 Métodos HTTP

| Método | Uso |
|--------|-----|
| GET | Leitura |
| POST | Criação |
| PUT | Atualização completa |
| PATCH | Atualização parcial |
| DELETE | Exclusão (soft delete) |

### 3.2 Códigos de Resposta

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Criado |
| 204 | Sem conteúdo (delete) |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Não encontrado |
| 409 | Conflito (duplicado) |
| 422 | Erro de validação |
| 429 | Rate limit |
| 500 | Erro interno |

### 3.3 Formato de Resposta

**Sucesso:**
```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

**Erro:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Dados inválidos",
    "details": [
      { "field": "email", "message": "Email inválido" }
    ]
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
| order | string | desc | asc ou desc |

### 3.5 Filtros

```
GET /pacientes?nome=João&status=ativo&created_at_gte=2024-01-01
```

| Sufixo | Operação |
|--------|----------|
| (nenhum) | Igual |
| `_gte` | Maior ou igual |
| `_lte` | Menor ou igual |
| `_like` | Contém (ILIKE) |
| `_in` | Em lista (comma separated) |

---

## 4. Auth

### 4.1 Login

```http
POST /auth/login
```

**Request:**
```json
{
  "email": "medico@clinica.com",
  "password": "senha123"
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "email": "medico@clinica.com",
      "nome": "Dr. João Silva",
      "perfil": {
        "id": "uuid",
        "nome": "Médico",
        "is_admin": false,
        "is_medico": true,
        "permissoes": { ... }
      },
      "clinica": {
        "id": "uuid",
        "nome": "Clínica Saúde"
      }
    }
  }
}
```

**Erros:**
| Código | Erro | Descrição |
|--------|------|-----------|
| 401 | `invalid_credentials` | Email ou senha incorretos |
| 401 | `user_blocked` | Usuário bloqueado |
| 429 | `too_many_attempts` | Muitas tentativas (5 em 30min) |

---

### 4.2 Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response (204):** No content

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
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600
  }
}
```

---

### 4.4 Me (Usuário Atual)

```http
GET /auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "medico@clinica.com",
    "nome": "Dr. João Silva",
    "telefone": "11999999999",
    "crm": "123456-SP",
    "especialidade": "Cardiologia",
    "perfil": { ... },
    "clinica": { ... }
  }
}
```

---

### 4.5 Alterar Senha

```http
POST /auth/change-password
Authorization: Bearer <token>
```

**Request:**
```json
{
  "current_password": "senha123",
  "new_password": "novaSenha456"
}
```

**Response (200):**
```json
{
  "data": {
    "message": "Senha alterada com sucesso"
  }
}
```

---

### 4.6 Esqueci a Senha

```http
POST /auth/forgot-password
```

**Request:**
```json
{
  "email": "medico@clinica.com"
}
```

**Response (200):**
```json
{
  "data": {
    "message": "Email de recuperação enviado"
  }
}
```

---

### 4.7 Reset de Senha

```http
POST /auth/reset-password
```

**Request:**
```json
{
  "token": "token-do-email",
  "new_password": "novaSenha456"
}
```

**Response (200):**
```json
{
  "data": {
    "message": "Senha redefinida com sucesso"
  }
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
  "data": {
    "id": "uuid",
    "nome": "Clínica Saúde",
    "cnpj": "12345678000199",
    "telefone": "1133334444",
    "email": "contato@clinica.com",
    "endereco": "Rua das Flores, 123",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01234567",
    "fuso_horario": "America/Sao_Paulo",
    "logo_url": "https://...",
    "saldo_minimo_alerta": 5000.00
  }
}
```

---

### 5.2 Atualizar Clínica

```http
PATCH /clinica
Authorization: Bearer <token>
```

**Permissão:** `is_admin = true`

**Request:**
```json
{
  "nome": "Clínica Saúde Plus",
  "telefone": "1133335555",
  "saldo_minimo_alerta": 10000.00
}
```

**Response (200):** Clínica atualizada

---

### 5.3 Listar Perfis

```http
GET /clinica/perfis
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Administrador",
      "descricao": "Acesso total ao sistema",
      "is_admin": true,
      "is_medico": false,
      "is_sistema": true,
      "permissoes": {
        "agenda": "CLEX",
        "pacientes": "CLEX",
        "prontuario": "CLEX",
        "financeiro": "CLEX",
        "configuracoes": "CLEX"
      }
    },
    ...
  ]
}
```

---

### 5.4 Criar Perfil

```http
POST /clinica/perfis
Authorization: Bearer <token>
```

**Permissão:** `is_admin = true`

**Request:**
```json
{
  "nome": "Estagiário",
  "descricao": "Acesso limitado",
  "is_medico": false,
  "permissoes": {
    "agenda": "L",
    "pacientes": "L"
  }
}
```

**Response (201):** Perfil criado

---

### 5.5 Listar Usuários

```http
GET /clinica/users
Authorization: Bearer <token>
```

**Query params:**
- `status`: ativo, inativo, bloqueado
- `perfil_id`: UUID do perfil
- `search`: busca por nome/email

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "Dr. João Silva",
      "email": "joao@clinica.com",
      "telefone": "11999999999",
      "crm": "123456-SP",
      "especialidade": "Cardiologia",
      "perfil": {
        "id": "uuid",
        "nome": "Médico"
      },
      "status": "ativo",
      "created_at": "2024-01-15T10:00:00Z"
    },
    ...
  ],
  "meta": { "total": 5 }
}
```

---

### 5.6 Criar Usuário

```http
POST /clinica/users
Authorization: Bearer <token>
```

**Permissão:** `is_admin = true`

**Request:**
```json
{
  "nome": "Dra. Maria Santos",
  "email": "maria@clinica.com",
  "telefone": "11988888888",
  "perfil_id": "uuid-perfil-medico",
  "crm": "654321-SP",
  "especialidade": "Dermatologia",
  "senha_temporaria": "temp123"
}
```

**Response (201):** Usuário criado (email de boas-vindas enviado)

---

### 5.7 Atualizar Usuário

```http
PATCH /clinica/users/{user_id}
Authorization: Bearer <token>
```

**Permissão:** `is_admin = true` ou próprio usuário (campos limitados)

**Request:**
```json
{
  "nome": "Dra. Maria Santos Costa",
  "telefone": "11977777777",
  "status": "ativo"
}
```

**Response (200):** Usuário atualizado

---

### 5.8 Bloquear/Desbloquear Usuário

```http
POST /clinica/users/{user_id}/block
POST /clinica/users/{user_id}/unblock
Authorization: Bearer <token>
```

**Permissão:** `is_admin = true`

**Response (200):**
```json
{
  "data": {
    "message": "Usuário bloqueado com sucesso"
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
- `search`: busca por nome, CPF, telefone
- `status`: ativo, inativo, bloqueado
- `created_at_gte`: data mínima
- `created_at_lte`: data máxima

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "nome": "José da Silva",
      "cpf": "12345678900",
      "data_nascimento": "1980-05-15",
      "idade": 44,
      "sexo": "M",
      "telefone": "11999999999",
      "email": "jose@email.com",
      "status": "ativo",
      "tem_alergias": true,
      "ultima_consulta": "2024-01-10",
      "created_at": "2023-06-01T10:00:00Z"
    },
    ...
  ],
  "meta": { "total": 150, "page": 1, "per_page": 20 }
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
  "data": {
    "id": "uuid",
    "nome": "José da Silva",
    "cpf": "12345678900",
    "data_nascimento": "1980-05-15",
    "idade": 44,
    "sexo": "M",
    "telefone": "11999999999",
    "email": "jose@email.com",
    "endereco": "Rua das Palmeiras, 456",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "04567890",
    "tipo_sanguineo": "O+",
    "emergencia_contato": "Maria - 11988888888 (esposa)",
    "como_conheceu": "Indicação",
    "indicado_por": {
      "id": "uuid",
      "nome": "Carlos Souza"
    },
    "status": "ativo",
    "alergias": [
      {
        "id": "uuid",
        "substancia": "Dipirona",
        "tipo": "medicamento",
        "gravidade": "moderada",
        "reacao": "Urticária",
        "confirmada": true
      }
    ],
    "medicamentos": [
      {
        "id": "uuid",
        "nome": "Losartana",
        "principio_ativo": "Losartana potássica",
        "dosagem": "50mg",
        "posologia": "1x ao dia, manhã",
        "motivo": "Hipertensão",
        "uso_continuo": true
      }
    ],
    "convenios": [
      {
        "id": "uuid",
        "convenio": {
          "id": "uuid",
          "nome": "Unimed"
        },
        "numero_carteirinha": "123456789",
        "plano": "Especial",
        "data_validade": "2025-12-31",
        "principal": true
      }
    ],
    "created_at": "2023-06-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

---

### 6.3 Criar Paciente

```http
POST /pacientes
Authorization: Bearer <token>
```

**Request:**
```json
{
  "nome": "Ana Paula Ferreira",
  "cpf": "98765432100",
  "data_nascimento": "1990-08-20",
  "sexo": "F",
  "telefone": "11977776666",
  "email": "ana@email.com",
  "endereco": "Av. Brasil, 789",
  "cidade": "São Paulo",
  "uf": "SP",
  "cep": "01234000",
  "tipo_sanguineo": "A+",
  "emergencia_contato": "João - 11966665555 (marido)",
  "como_conheceu": "Google"
}
```

**Response (201):** Paciente criado

---

### 6.4 Atualizar Paciente

```http
PATCH /pacientes/{paciente_id}
Authorization: Bearer <token>
```

**Request:**
```json
{
  "telefone": "11955554444",
  "endereco": "Rua Nova, 100"
}
```

**Response (200):** Paciente atualizado

---

### 6.5 Adicionar Alergia

```http
POST /pacientes/{paciente_id}/alergias
Authorization: Bearer <token>
```

**Request:**
```json
{
  "substancia": "Penicilina",
  "tipo": "medicamento",
  "gravidade": "grave",
  "reacao": "Choque anafilático"
}
```

**Response (201):** Alergia adicionada

---

### 6.6 Confirmar Alergia (Médico)

```http
POST /pacientes/{paciente_id}/alergias/{alergia_id}/confirmar
Authorization: Bearer <token>
```

**Permissão:** `is_medico = true`

**Response (200):**
```json
{
  "data": {
    "confirmada": true,
    "confirmada_por": "Dr. João Silva",
    "confirmada_em": "2024-01-15T10:00:00Z"
  }
}
```

---

### 6.7 Remover Alergia

```http
DELETE /pacientes/{paciente_id}/alergias/{alergia_id}
Authorization: Bearer <token>
```

**Response (204):** No content

---

### 6.8 Adicionar Medicamento

```http
POST /pacientes/{paciente_id}/medicamentos
Authorization: Bearer <token>
```

**Request:**
```json
{
  "nome": "Metformina",
  "principio_ativo": "Cloridrato de metformina",
  "dosagem": "850mg",
  "posologia": "1 comprimido após almoço e jantar",
  "motivo": "Diabetes tipo 2",
  "uso_continuo": true
}
```

**Response (201):** Medicamento adicionado

---

### 6.9 Adicionar Convênio ao Paciente

```http
POST /pacientes/{paciente_id}/convenios
Authorization: Bearer <token>
```

**Request:**
```json
{
  "convenio_id": "uuid-convenio",
  "numero_carteirinha": "987654321",
  "plano": "Premium",
  "data_validade": "2026-06-30",
  "principal": true
}
```

**Response (201):** Convênio vinculado

---

### 6.10 Histórico do Paciente

```http
GET /pacientes/{paciente_id}/historico
Authorization: Bearer <token>
```

**Permissão:** `is_medico = true`

**Query params:**
- `limit`: quantidade (default 10)

**Response (200):**
```json
{
  "data": [
    {
      "consulta_id": "uuid",
      "data": "2024-01-10",
      "medico": "Dr. João Silva",
      "tipo": "Consulta",
      "queixa_principal": "Dor de cabeça frequente",
      "diagnosticos": ["Cefaleia tensional"],
      "cids": ["G44.2"]
    },
    ...
  ]
}
```

---

## 7. Agenda

### 7.1 Listar Tipos de Consulta

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
      "nome": "Consulta",
      "duracao_minutos": 30,
      "valor_particular": 250.00,
      "cor": "#3B82F6",
      "permite_encaixe": true,
      "antecedencia_minima": 2,
      "antecedencia_maxima": 90,
      "ativo": true
    },
    ...
  ]
}
```

---

### 7.2 Obter Slots Disponíveis

```http
GET /agenda/slots
Authorization: Bearer <token>
```

**Query params (obrigatórios):**
- `medico_id`: UUID do médico
- `data`: YYYY-MM-DD

**Query params (opcionais):**
- `tipo_consulta_id`: filtra por tipo

**Response (200):**
```json
{
  "data": {
    "data": "2024-01-20",
    "medico": {
      "id": "uuid",
      "nome": "Dr. João Silva"
    },
    "slots": [
      {
        "hora_inicio": "08:00",
        "hora_fim": "08:30",
        "disponivel": true
      },
      {
        "hora_inicio": "08:30",
        "hora_fim": "09:00",
        "disponivel": false,
        "motivo": "Agendado"
      },
      {
        "hora_inicio": "09:00",
        "hora_fim": "09:30",
        "disponivel": false,
        "motivo": "Bloqueio: Reunião"
      },
      ...
    ]
  }
}
```

---

### 7.3 Listar Agendamentos

```http
GET /agenda/agendamentos
Authorization: Bearer <token>
```

**Query params:**
- `data`: YYYY-MM-DD (obrigatório se não informar período)
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD
- `medico_id`: UUID
- `status`: agendado, confirmado, aguardando, em_atendimento, atendido, faltou, cancelado
- `paciente_id`: UUID

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "paciente": {
        "id": "uuid",
        "nome": "José da Silva",
        "telefone": "11999999999",
        "tem_alergias": true
      },
      "medico": {
        "id": "uuid",
        "nome": "Dr. João Silva"
      },
      "tipo_consulta": {
        "id": "uuid",
        "nome": "Consulta",
        "cor": "#3B82F6"
      },
      "data": "2024-01-20",
      "hora_inicio": "08:00",
      "hora_fim": "08:30",
      "forma_pagamento": "particular",
      "valor_previsto": 250.00,
      "status": "confirmado",
      "confirmado_em": "2024-01-18T14:00:00Z",
      "observacoes": null
    },
    ...
  ],
  "meta": { "total": 15 }
}
```

---

### 7.4 Criar Agendamento

```http
POST /agenda/agendamentos
Authorization: Bearer <token>
```

**Request:**
```json
{
  "paciente_id": "uuid",
  "medico_id": "uuid",
  "tipo_consulta_id": "uuid",
  "data": "2024-01-25",
  "hora_inicio": "10:00",
  "forma_pagamento": "convenio",
  "convenio_id": "uuid",
  "observacoes": "Retorno de exames"
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "status": "agendado",
    "card_id": "uuid",
    ...
  }
}
```

**Erros:**
| Código | Erro | Descrição |
|--------|------|-----------|
| 409 | `slot_unavailable` | Horário não disponível |
| 422 | `antecedencia_minima` | Muito em cima da hora |
| 422 | `antecedencia_maxima` | Muito distante |

---

### 7.5 Atualizar Status do Agendamento

```http
PATCH /agenda/agendamentos/{agendamento_id}/status
Authorization: Bearer <token>
```

**Request:**
```json
{
  "status": "confirmado"
}
```

**Transições válidas:**

| De | Para | Quem pode |
|----|------|-----------|
| agendado | confirmado | Qualquer |
| agendado | cancelado | Qualquer |
| confirmado | aguardando | Recepção |
| confirmado | cancelado | Qualquer |
| confirmado | faltou | Recepção |
| aguardando | em_atendimento | Médico |
| em_atendimento | atendido | Médico |

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "confirmado",
    "confirmado_em": "2024-01-18T14:30:00Z"
  }
}
```

---

### 7.6 Remarcar Agendamento

```http
POST /agenda/agendamentos/{agendamento_id}/remarcar
Authorization: Bearer <token>
```

**Request:**
```json
{
  "nova_data": "2024-01-28",
  "nova_hora_inicio": "14:00",
  "motivo": "Paciente solicitou"
}
```

**Response (200):**
```json
{
  "data": {
    "agendamento_antigo": {
      "id": "uuid",
      "status": "remarcado"
    },
    "agendamento_novo": {
      "id": "uuid-novo",
      "data": "2024-01-28",
      "hora_inicio": "14:00",
      "status": "agendado"
    }
  }
}
```

---

### 7.7 Check-in do Paciente

```http
POST /agenda/agendamentos/{agendamento_id}/checkin
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "aguardando",
    "checkin_em": "2024-01-20T07:55:00Z"
  }
}
```

---

### 7.8 Chamar Paciente

```http
POST /agenda/agendamentos/{agendamento_id}/chamar
Authorization: Bearer <token>
```

**Permissão:** `is_medico = true`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "em_atendimento",
    "chamado_em": "2024-01-20T08:05:00Z",
    "consulta_id": "uuid-consulta"
  }
}
```

---

### 7.9 Finalizar Atendimento

```http
POST /agenda/agendamentos/{agendamento_id}/finalizar
Authorization: Bearer <token>
```

**Permissão:** `is_medico = true`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "atendido",
    "finalizado_em": "2024-01-20T08:35:00Z",
    "tempo_espera_minutos": 10,
    "tempo_consulta_minutos": 30
  }
}
```

---

### 7.10 Listar Bloqueios

```http
GET /agenda/bloqueios
Authorization: Bearer <token>
```

**Query params:**
- `medico_id`: UUID (null = bloqueios da clínica)
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "medico": null,
      "data_inicio": "2024-12-25",
      "data_fim": "2024-12-25",
      "hora_inicio": null,
      "hora_fim": null,
      "motivo": "Natal",
      "tipo": "feriado",
      "recorrente_anual": true
    },
    ...
  ]
}
```

---

### 7.11 Criar Bloqueio

```http
POST /agenda/bloqueios
Authorization: Bearer <token>
```

**Request:**
```json
{
  "medico_id": "uuid",
  "data_inicio": "2024-02-10",
  "data_fim": "2024-02-20",
  "motivo": "Férias",
  "tipo": "ferias"
}
```

**Response (201):** Bloqueio criado

---

### 7.12 Métricas do Dia

```http
GET /agenda/metricas
Authorization: Bearer <token>
```

**Query params:**
- `data`: YYYY-MM-DD (default hoje)
- `medico_id`: UUID (opcional)

**Response (200):**
```json
{
  "data": {
    "data": "2024-01-20",
    "total_agendados": 20,
    "confirmados": 18,
    "atendidos": 12,
    "faltaram": 1,
    "aguardando": 3,
    "em_atendimento": 1,
    "taxa_ocupacao": 0.90,
    "tempo_medio_espera_minutos": 12,
    "tempo_medio_consulta_minutos": 28
  }
}
```

---

## 8. Cards (Kanban)

### 8.1 Listar Cards (Kanban)

```http
GET /cards
Authorization: Bearer <token>
```

**Query params:**
- `fase`: 0, 1, 2, 3
- `coluna`: nome da coluna
- `medico_id`: UUID
- `data`: YYYY-MM-DD (para fase 2)
- `status`: ativo, concluido, cancelado

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "fase": 2,
      "coluna": "em_espera",
      "posicao": 1,
      "status": "ativo",
      "paciente": {
        "id": "uuid",
        "nome": "José da Silva",
        "telefone": "11999999999",
        "tem_alergias": true
      },
      "medico": {
        "id": "uuid",
        "nome": "Dr. João Silva"
      },
      "agendamento": {
        "id": "uuid",
        "data": "2024-01-20",
        "hora_inicio": "08:00",
        "tipo_consulta": "Consulta"
      },
      "checklist": {
        "total": 3,
        "concluidos": 2,
        "pendentes": [
          {
            "id": "uuid",
            "tipo": "checkin",
            "descricao": "Check-in na recepção",
            "obrigatorio": true
          }
        ]
      },
      "tempo_espera_minutos": 15,
      "is_derivado": false
    },
    ...
  ]
}
```

---

### 8.2 Obter Card

```http
GET /cards/{card_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "fase": 1,
    "coluna": "pendente_anamnese",
    "posicao": 2,
    "status": "ativo",
    "paciente": { ... },
    "medico": { ... },
    "agendamento": { ... },
    "checklist": [
      {
        "id": "uuid",
        "fase": 1,
        "tipo": "anamnese",
        "descricao": "Preencher anamnese",
        "obrigatorio": true,
        "concluido": false
      },
      {
        "id": "uuid",
        "fase": 1,
        "tipo": "exame_upload",
        "descricao": "Enviar Hemograma",
        "obrigatorio": true,
        "concluido": true,
        "concluido_em": "2024-01-18T10:00:00Z",
        "referencia_tipo": "exame_solicitado",
        "referencia_id": "uuid"
      }
    ],
    "documentos": [
      {
        "id": "uuid",
        "tipo": "exame",
        "nome": "hemograma.pdf",
        "exame_tipo": "Hemograma",
        "exame_data": "2024-01-15",
        "match_status": "matched"
      }
    ],
    "mensagens": [
      {
        "id": "uuid",
        "direcao": "enviada",
        "tipo": "template",
        "template_nome": "confirmacao_consulta",
        "status_entrega": "lida",
        "created_at": "2024-01-17T14:00:00Z"
      }
    ],
    "anamnese": {
      "id": "uuid",
      "queixa_principal": "Dor de cabeça há 3 dias",
      "preenchida_em": "2024-01-18T09:30:00Z"
    },
    "fase0_em": "2024-01-15T10:00:00Z",
    "fase1_em": "2024-01-17T00:00:00Z",
    "is_derivado": false
  }
}
```

---

### 8.3 Mover Card

```http
POST /cards/{card_id}/mover
Authorization: Bearer <token>
```

**Request:**
```json
{
  "coluna": "pronto",
  "posicao": 1
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "coluna": "pronto",
    "posicao": 1
  }
}
```

---

### 8.4 Concluir Item do Checklist

```http
POST /cards/{card_id}/checklist/{item_id}/concluir
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "concluido": true,
    "concluido_em": "2024-01-20T08:00:00Z",
    "concluido_por": "Maria Santos"
  }
}
```

---

### 8.5 Adicionar Item ao Checklist

```http
POST /cards/{card_id}/checklist
Authorization: Bearer <token>
```

**Request:**
```json
{
  "fase": 1,
  "tipo": "exame_upload",
  "descricao": "Enviar Raio-X de tórax",
  "obrigatorio": false
}
```

**Response (201):** Item adicionado

---

### 8.6 Upload de Documento

```http
POST /cards/{card_id}/documentos
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `file`: arquivo (PDF, imagem)
- `tipo`: exame, documento, outro
- `exame_tipo`: (se tipo=exame) Hemograma, Raio-X, etc
- `exame_data`: (se tipo=exame) YYYY-MM-DD
- `exame_laboratorio`: (se tipo=exame) nome do lab
- `exame_solicitado_id`: (se tipo=exame) UUID do exame solicitado

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "nome": "hemograma.pdf",
    "tipo": "exame",
    "exame_tipo": "Hemograma",
    "match_status": "matched",
    "storage_path": "cards/uuid/documentos/hemograma.pdf"
  }
}
```

---

### 8.7 Histórico do Card

```http
GET /cards/{card_id}/historico
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "acao": "moveu_coluna",
      "fase_anterior": 1,
      "fase_nova": 1,
      "coluna_anterior": "pendente_anamnese",
      "coluna_nova": "pronto",
      "alterado_por": "Sistema",
      "created_at": "2024-01-18T10:00:00Z"
    },
    ...
  ]
}
```

---

## 9. Prontuário

**⚠️ IMPORTANTE:** Todos os endpoints de prontuário exigem `is_medico = true`

### 9.1 Obter Consulta

```http
GET /prontuario/consultas/{consulta_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "paciente": {
      "id": "uuid",
      "nome": "José da Silva",
      "idade": 44,
      "sexo": "M",
      "tipo_sanguineo": "O+",
      "alergias": [ ... ],
      "medicamentos": [ ... ]
    },
    "medico": {
      "id": "uuid",
      "nome": "Dr. João Silva",
      "crm": "123456-SP"
    },
    "agendamento": { ... },
    "iniciada_em": "2024-01-20T08:05:00Z",
    "finalizada_em": null,
    "status": "em_andamento",
    "tipo": "presencial",
    "anamnese": { ... },
    "soap": null,
    "transcricao": null,
    "receitas": [],
    "atestados": [],
    "exames_solicitados": [],
    "encaminhamentos": []
  }
}
```

---

### 9.2 Briefing do Paciente

```http
GET /prontuario/consultas/{consulta_id}/briefing
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "paciente": {
      "nome": "José da Silva",
      "idade": 44,
      "sexo": "M"
    },
    "alertas": [
      {
        "tipo": "alergia",
        "gravidade": "grave",
        "mensagem": "ALERGIA A PENICILINA - Anafilaxia"
      }
    ],
    "medicamentos_uso_continuo": [
      "Losartana 50mg - 1x manhã",
      "Metformina 850mg - 2x dia"
    ],
    "ultima_consulta": {
      "data": "2024-01-10",
      "medico": "Dr. João Silva",
      "queixa": "Check-up anual",
      "diagnosticos": ["Hipertensão controlada", "DM2 controlada"]
    },
    "anamnese_atual": {
      "queixa_principal": "Dor de cabeça há 3 dias",
      "duracao": "3 dias",
      "medicamentos_informados": "Paracetamol sem melhora"
    },
    "exames_pendentes": [
      {
        "nome": "Hemograma",
        "solicitado_em": "2024-01-10",
        "status": "resultado_anexado"
      }
    ]
  }
}
```

---

### 9.3 Iniciar Transcrição

```http
POST /prontuario/consultas/{consulta_id}/transcricao/iniciar
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `audio`: arquivo de áudio (mp3, wav, m4a)

**Response (202):**
```json
{
  "data": {
    "transcricao_id": "uuid",
    "status": "processando",
    "message": "Transcrição iniciada. Você será notificado quando concluir."
  }
}
```

---

### 9.4 Obter Transcrição

```http
GET /prontuario/consultas/{consulta_id}/transcricao
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "concluida",
    "audio_duracao_segundos": 1200,
    "transcricao_bruta": "...",
    "transcricao_revisada": "...",
    "modelo_whisper": "whisper-1",
    "created_at": "2024-01-20T08:10:00Z"
  }
}
```

---

### 9.5 Gerar SOAP com IA

```http
POST /prontuario/consultas/{consulta_id}/soap/gerar
Authorization: Bearer <token>
```

**Request (opcional):**
```json
{
  "transcricao_id": "uuid",
  "instrucoes_adicionais": "Foco em cefaleia"
}
```

**Response (202):**
```json
{
  "data": {
    "soap_id": "uuid",
    "status": "processando",
    "message": "SOAP sendo gerado. Você será notificado quando concluir."
  }
}
```

---

### 9.6 Obter/Atualizar SOAP

```http
GET /prontuario/consultas/{consulta_id}/soap
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "subjetivo": "Paciente refere cefaleia frontal há 3 dias...",
    "objetivo": "PA: 130/85 mmHg. FC: 72 bpm...",
    "avaliacao": "Cefaleia tensional",
    "plano": "1. Analgésico SOS\n2. Orientações...",
    "exame_fisico": {
      "sinais_vitais": {
        "pressao_arterial": "130/85",
        "frequencia_cardiaca": 72,
        "temperatura": 36.2
      }
    },
    "cids": [
      { "codigo": "G44.2", "descricao": "Cefaleia tensional", "tipo": "principal" }
    ],
    "gerado_por_ia": true,
    "revisado_por_medico": false,
    "assinado": false
  }
}
```

```http
PATCH /prontuario/consultas/{consulta_id}/soap
Authorization: Bearer <token>
```

**Request:**
```json
{
  "subjetivo": "Texto revisado...",
  "cids": [
    { "codigo": "G44.2", "descricao": "Cefaleia tensional", "tipo": "principal" }
  ],
  "revisado_por_medico": true
}
```

---

### 9.7 Assinar SOAP

```http
POST /prontuario/consultas/{consulta_id}/soap/assinar
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "assinado": true,
    "assinado_em": "2024-01-20T08:30:00Z",
    "assinado_por": "Dr. João Silva - CRM 123456-SP"
  }
}
```

---

### 9.8 Criar Receita

```http
POST /prontuario/consultas/{consulta_id}/receitas
Authorization: Bearer <token>
```

**Request:**
```json
{
  "tipo": "simples",
  "itens": [
    {
      "medicamento": "Paracetamol",
      "concentracao": "750mg",
      "forma_farmaceutica": "comprimido",
      "quantidade": 10,
      "posologia": "1 comprimido de 6/6h se dor",
      "duracao": "5 dias"
    }
  ]
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "tipo": "simples",
    "status": "rascunho",
    "itens": [ ... ]
  }
}
```

---

### 9.9 Emitir Receita (Gerar PDF)

```http
POST /prontuario/consultas/{consulta_id}/receitas/{receita_id}/emitir
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "status": "emitida",
    "pdf_url": "https://storage.../receita_uuid.pdf",
    "assinatura_digital": true
  }
}
```

---

### 9.10 Enviar Receita ao Paciente

```http
POST /prontuario/consultas/{consulta_id}/receitas/{receita_id}/enviar
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "enviada_paciente": true,
    "enviada_em": "2024-01-20T08:35:00Z",
    "meio": "whatsapp"
  }
}
```

---

### 9.11 Criar Atestado

```http
POST /prontuario/consultas/{consulta_id}/atestados
Authorization: Bearer <token>
```

**Request:**
```json
{
  "tipo": "afastamento",
  "data_inicio": "2024-01-20",
  "data_fim": "2024-01-22",
  "dias_afastamento": 3,
  "cid_codigo": "G44.2",
  "incluir_cid": false
}
```

**Response (201):** Atestado criado

---

### 9.12 Solicitar Exame

```http
POST /prontuario/consultas/{consulta_id}/exames
Authorization: Bearer <token>
```

**Request:**
```json
{
  "codigo_tuss": "40304361",
  "nome": "Hemograma completo",
  "tipo": "laboratorial",
  "indicacao_clinica": "Investigação de anemia",
  "cid_codigo": "D50",
  "urgente": false,
  "para_retorno": true,
  "prazo_dias": 30
}
```

**Response (201):** Exame solicitado

---

### 9.13 Criar Encaminhamento

```http
POST /prontuario/consultas/{consulta_id}/encaminhamentos
Authorization: Bearer <token>
```

**Request:**
```json
{
  "especialidade": "Neurologia",
  "profissional_nome": "Dr. Carlos Neuro",
  "motivo": "Investigação de cefaleia crônica refratária",
  "cid_codigo": "G44.2",
  "urgente": false
}
```

**Response (201):** Encaminhamento criado

---

### 9.14 Criar Card de Retorno

```http
POST /prontuario/consultas/{consulta_id}/retorno
Authorization: Bearer <token>
```

**Request:**
```json
{
  "prazo_dias": 30,
  "exames_ids": ["uuid-exame-1", "uuid-exame-2"],
  "observacoes": "Retorno com exames"
}
```

**Response (201):**
```json
{
  "data": {
    "card_derivado_id": "uuid",
    "agendamento_id": "uuid",
    "data_prevista": "2024-02-19",
    "checklist_exames": [
      { "exame": "Hemograma", "status": "pendente" },
      { "exame": "Glicemia", "status": "pendente" }
    ]
  }
}
```

---

## 10. Financeiro

### 10.1 Dashboard Financeiro

```http
GET /financeiro/dashboard
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "saldo_atual": 45000.00,
    "a_receber_hoje": 2500.00,
    "a_pagar_hoje": 1200.00,
    "a_receber_atrasado": 800.00,
    "a_pagar_atrasado": 0.00,
    "receita_mes": 85000.00,
    "despesa_mes": 42000.00,
    "lucro_mes": 43000.00
  }
}
```

---

### 10.2 Fluxo de Caixa

```http
GET /financeiro/fluxo-caixa
Authorization: Bearer <token>
```

**Query params:**
- `data_inicio`: YYYY-MM-DD (default hoje)
- `data_fim`: YYYY-MM-DD (default +30 dias)

**Response (200):**
```json
{
  "data": [
    {
      "data": "2024-01-20",
      "entradas": 3500.00,
      "saidas": 1200.00,
      "saldo_dia": 2300.00,
      "saldo_acumulado": 47300.00
    },
    ...
  ]
}
```

---

### 10.3 DRE

```http
GET /financeiro/dre
Authorization: Bearer <token>
```

**Query params:**
- `mes`: 1-12
- `ano`: YYYY

**Response (200):**
```json
{
  "data": [
    { "descricao": "(+) Consultas Particulares", "valor": 45000.00, "percentual": 52.9 },
    { "descricao": "(+) Consultas Convênio", "valor": 35000.00, "percentual": 41.2 },
    { "descricao": "(+) Procedimentos", "valor": 5000.00, "percentual": 5.9 },
    { "descricao": "= RECEITA BRUTA", "valor": 85000.00, "percentual": 100.0 },
    { "descricao": "(-) Salários", "valor": 25000.00, "percentual": 29.4 },
    { "descricao": "(-) Aluguel", "valor": 8000.00, "percentual": 9.4 },
    { "descricao": "(-) Impostos", "valor": 5000.00, "percentual": 5.9 },
    { "descricao": "(-) Outros", "valor": 4000.00, "percentual": 4.7 },
    { "descricao": "= LUCRO OPERACIONAL", "valor": 43000.00, "percentual": 50.6 }
  ]
}
```

---

### 10.4 Listar Contas a Pagar

```http
GET /financeiro/contas-pagar
Authorization: Bearer <token>
```

**Query params:**
- `status`: rascunho, pendente, aprovado, pago, atrasado, cancelado
- `fornecedor_id`: UUID
- `categoria_id`: UUID
- `data_vencimento_gte`: YYYY-MM-DD
- `data_vencimento_lte`: YYYY-MM-DD

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "descricao": "Aluguel Janeiro",
      "fornecedor": {
        "id": "uuid",
        "nome": "Imobiliária XYZ"
      },
      "categoria": {
        "id": "uuid",
        "nome": "Aluguel"
      },
      "valor": 8000.00,
      "data_vencimento": "2024-01-25",
      "status": "pendente",
      "requer_aprovacao": false,
      "documento_tipo": "boleto",
      "tem_evidencia": true
    },
    ...
  ],
  "meta": { "total": 25 }
}
```

---

### 10.5 Criar Conta a Pagar

```http
POST /financeiro/contas-pagar
Authorization: Bearer <token>
```

**Request:**
```json
{
  "descricao": "Material médico",
  "fornecedor_id": "uuid",
  "categoria_id": "uuid",
  "valor": 1500.00,
  "data_vencimento": "2024-02-10",
  "documento_tipo": "nf",
  "codigo_barras": "12345.67890..."
}
```

**Response (201):** Conta criada

---

### 10.6 Upload de Documento (Conta a Pagar)

```http
POST /financeiro/contas-pagar/{conta_id}/documento
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `file`: arquivo (PDF, imagem)
- `tipo`: nf, boleto, recibo

**Response (200):**
```json
{
  "data": {
    "documento_storage_path": "financeiro/contas-pagar/uuid/nf.pdf",
    "dados_ia": {
      "fornecedor_detectado": "Fornecedor ABC",
      "valor_detectado": 1500.00,
      "vencimento_detectado": "2024-02-10",
      "confianca": 0.95
    }
  }
}
```

---

### 10.7 Aprovar Conta a Pagar

```http
POST /financeiro/contas-pagar/{conta_id}/aprovar
Authorization: Bearer <token>
```

**Permissão:** Depende do valor (ver regras de aprovação)

**Request (opcional):**
```json
{
  "comentario": "Aprovado conforme orçamento"
}
```

**Response (200):**
```json
{
  "data": {
    "status": "aprovado",
    "aprovado_por": "Maria Admin",
    "aprovado_em": "2024-01-20T10:00:00Z"
  }
}
```

---

### 10.8 Pagar Conta

```http
POST /financeiro/contas-pagar/{conta_id}/pagar
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `comprovante`: arquivo (PDF, imagem)
- `forma_pagamento`: boleto, pix, transferencia, dinheiro
- `data_pagamento`: YYYY-MM-DD
- `valor_pago`: decimal (se diferente do valor)

**Response (200):**
```json
{
  "data": {
    "status": "pago",
    "data_pagamento": "2024-01-20",
    "valor_pago": 8000.00
  }
}
```

---

### 10.9 Listar Contas a Receber

```http
GET /financeiro/contas-receber
Authorization: Bearer <token>
```

**Query params:**
- `status`: pendente, parcial, pago, atrasado, glosado, cancelado
- `origem`: consulta, convenio, procedimento, outro
- `paciente_id`: UUID
- `convenio_id`: UUID

**Response (200):** Similar a contas a pagar

---

### 10.10 Registrar Recebimento

```http
POST /financeiro/contas-receber/{conta_id}/receber
Authorization: Bearer <token>
```

**Request:**
```json
{
  "valor_recebido": 250.00,
  "forma_pagamento": "pix",
  "data_recebimento": "2024-01-20"
}
```

**Response (200):** Recebimento registrado

---

### 10.11 Listar Contas Bancárias

```http
GET /financeiro/contas-bancarias
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "banco_nome": "Itaú",
      "agencia": "1234",
      "conta": "56789-0",
      "tipo": "corrente",
      "apelido": "Conta Principal",
      "saldo_atual": 45000.00,
      "saldo_atualizado_em": "2024-01-20T06:00:00Z",
      "principal": true
    },
    ...
  ]
}
```

---

### 10.12 Importar Extrato (OFX)

```http
POST /financeiro/contas-bancarias/{conta_id}/importar
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `file`: arquivo OFX

**Response (200):**
```json
{
  "data": {
    "importados": 45,
    "duplicados_ignorados": 3,
    "sugestoes_conciliacao": 12
  }
}
```

---

### 10.13 Listar Extrato

```http
GET /financeiro/contas-bancarias/{conta_id}/extrato
Authorization: Bearer <token>
```

**Query params:**
- `data_inicio`: YYYY-MM-DD
- `data_fim`: YYYY-MM-DD
- `conciliado`: true/false

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "data": "2024-01-20",
      "descricao": "PIX RECEBIDO - JOSE DA SILVA",
      "tipo": "credito",
      "valor": 250.00,
      "conciliado": false,
      "sugestao": {
        "tipo": "conta_receber",
        "conta_receber_id": "uuid",
        "descricao": "Consulta - José da Silva",
        "confianca": 0.95
      }
    },
    ...
  ]
}
```

---

### 10.14 Conciliar Transação

```http
POST /financeiro/extrato/{extrato_id}/conciliar
Authorization: Bearer <token>
```

**Request:**
```json
{
  "conta_pagar_id": "uuid",
  "observacao": "Pagamento de energia"
}
```

ou

```json
{
  "conta_receber_id": "uuid"
}
```

ou

```json
{
  "tipo": "tarifa",
  "categoria_id": "uuid-categoria-tarifa"
}
```

**Response (200):**
```json
{
  "data": {
    "conciliacao_id": "uuid",
    "tipo": "manual",
    "conciliado_em": "2024-01-20T10:00:00Z"
  }
}
```

---

## 11. Evidências

### 11.1 Listar Evidências

```http
GET /evidencias
Authorization: Bearer <token>
```

**Query params:**
- `entidade`: contas_pagar, receitas, etc
- `entidade_id`: UUID
- `tipo`: nota_fiscal, comprovante, etc
- `categoria`: documento, api_response, etc
- `status`: ativo, substituido, invalido

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "entidade": "contas_pagar",
      "entidade_id": "uuid",
      "tipo": "nota_fiscal",
      "categoria": "documento",
      "descricao": "NF de material médico",
      "arquivo_nome": "nf_12345.pdf",
      "arquivo_url": "https://storage.../evidencias/...",
      "validado": true,
      "validado_por": "Maria Admin",
      "origem": "usuario",
      "created_at": "2024-01-15T10:00:00Z"
    },
    ...
  ]
}
```

---

### 11.2 Upload de Evidência

```http
POST /evidencias
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form data:**
- `file`: arquivo
- `entidade`: nome da tabela
- `entidade_id`: UUID
- `tipo`: tipo da evidência
- `descricao`: descrição (opcional)

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "arquivo_nome": "comprovante.pdf",
    "arquivo_hash": "sha256...",
    "status": "ativo"
  }
}
```

---

### 11.3 Validar Evidência

```http
POST /evidencias/{evidencia_id}/validar
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "data": {
    "validado": true,
    "validado_por": "Dr. João Silva",
    "validado_em": "2024-01-20T10:00:00Z"
  }
}
```

---

### 11.4 Verificar Evidências Obrigatórias

```http
GET /evidencias/verificar
Authorization: Bearer <token>
```

**Query params:**
- `entidade`: contas_pagar
- `entidade_id`: UUID
- `acao`: pagar

**Response (200):**
```json
{
  "data": {
    "pode_executar": false,
    "evidencias_faltando": ["comprovante_pagamento"],
    "mensagem": "É necessário anexar comprovante de pagamento"
  }
}
```

---

## 12. Webhooks

### 12.1 Webhook WhatsApp (Evolution API)

```http
POST /webhooks/whatsapp
X-Webhook-Secret: <secret>
```

**Payload (mensagem recebida):**
```json
{
  "event": "messages.upsert",
  "instance": "clinica-saude",
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "message-id"
    },
    "message": {
      "conversation": "Confirmo minha consulta"
    },
    "messageTimestamp": 1705750000
  }
}
```

**Response (200):**
```json
{
  "status": "processed"
}
```

---

### 12.2 Webhook Kestra (Callback)

```http
POST /webhooks/kestra
X-Webhook-Secret: <secret>
```

**Payload (transcrição concluída):**
```json
{
  "workflow": "transcricao-audio",
  "execution_id": "uuid",
  "status": "SUCCESS",
  "outputs": {
    "transcricao_id": "uuid",
    "texto": "...",
    "duracao_segundos": 1200
  }
}
```

**Response (200):**
```json
{
  "status": "processed"
}
```

---

### 12.3 Webhook Convênio (Elegibilidade)

```http
POST /webhooks/convenio/elegibilidade
X-Webhook-Secret: <secret>
```

**Payload:**
```json
{
  "protocolo": "123456",
  "paciente_carteirinha": "987654321",
  "status": "ELEGIVEL",
  "plano": "Especial",
  "cobertura": {
    "consulta": true,
    "exames": true,
    "procedimentos": ["10101012", "10101020"]
  }
}
```

---

## 13. Schemas

### 13.1 Schemas Comuns

#### PaginationMeta
```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

#### Error
```json
{
  "code": "string",
  "message": "string",
  "details": [
    {
      "field": "string",
      "message": "string"
    }
  ]
}
```

#### Timestamp
```
"2024-01-20T10:30:00Z"  // ISO 8601, UTC
```

#### UUID
```
"550e8400-e29b-41d4-a716-446655440000"
```

---

### 13.2 Enums

#### StatusAgendamento
```
agendado | confirmado | aguardando | em_atendimento | atendido | faltou | cancelado | remarcado
```

#### StatusCard
```
ativo | concluido | cancelado
```

#### FaseCard
```
0 | 1 | 2 | 3
```

#### ColunaCard
```
# Fase 0
agendado

# Fase 1
pendente_anamnese | pendente_confirmacao | pronto

# Fase 2
aguardando_checkin | em_espera | em_atendimento | finalizado

# Fase 3
pendente_documentos | pendente_pagamento | concluido
```

#### TipoReceita
```
simples | especial | antimicrobiano
```

#### TipoAtestado
```
comparecimento | afastamento | aptidao | acompanhante
```

#### StatusContaPagar
```
rascunho | pendente | aprovado | pago | atrasado | cancelado
```

#### StatusContaReceber
```
pendente | parcial | pago | atrasado | glosado | cancelado
```

#### CategoriaEvidencia
```
documento | api_response | assinatura | comprovante | log_sistema | mensagem | formulario
```

---

## Apêndice: Códigos de Erro

| Código | HTTP | Descrição |
|--------|------|-----------|
| `token_invalid` | 401 | Token inválido ou expirado |
| `token_missing` | 401 | Token não fornecido |
| `invalid_credentials` | 401 | Email ou senha incorretos |
| `user_blocked` | 401 | Usuário bloqueado |
| `too_many_attempts` | 429 | Muitas tentativas de login |
| `permission_denied` | 403 | Sem permissão |
| `clinica_mismatch` | 403 | Recurso de outra clínica |
| `not_found` | 404 | Recurso não encontrado |
| `validation_error` | 422 | Erro de validação |
| `slot_unavailable` | 409 | Horário não disponível |
| `evidence_required` | 422 | Evidência obrigatória faltando |
| `invalid_status_transition` | 422 | Transição de status inválida |
| `rate_limit_exceeded` | 429 | Rate limit excedido |
| `internal_error` | 500 | Erro interno |

---

**Documento gerado em:** Janeiro 2026  
**Versão:** 1.0
