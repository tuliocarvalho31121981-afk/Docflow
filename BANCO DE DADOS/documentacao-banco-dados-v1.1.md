# Documentação do Banco de Dados
## Sistema de Gestão de Clínicas Médicas

**Versão:** 1.1  
**Data:** Janeiro 2026  
**Tecnologia:** PostgreSQL 15+ (Supabase)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Convenções](#3-convenções)
4. [Tabelas Existentes](#4-tabelas-existentes)
5. [Row Level Security (RLS)](#5-row-level-security-rls)
6. [Integrações com Backend](#6-integrações-com-backend)

---

## 1. Visão Geral

### 1.1 Propósito

Sistema completo de gestão de clínicas médicas com:

- Gestão de pacientes e prontuários
- Agendamento e jornada do paciente (Kanban)
- Financeiro (contas a pagar/receber)
- Multi-tenant com RLS

### 1.2 Atores do Sistema

| Ator | Descrição | Acesso |
|------|-----------|--------|
| **users** | Funcionários da clínica | Login via Supabase Auth |
| **pacientes** | Clientes externos | Via WhatsApp/links públicos |
| **sistema** | Automações | Triggers, cron jobs |

---

## 2. Arquitetura

### 2.1 Multi-Tenancy com RLS

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUPABASE + RLS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Usuário faz login → Recebe JWT token                           │
│                           │                                      │
│                           ▼                                      │
│  Backend usa token em todas as queries                          │
│                           │                                      │
│                           ▼                                      │
│  RLS Policy verifica: auth.uid() → users → clinica_id           │
│                           │                                      │
│                           ▼                                      │
│  Query automaticamente filtrada pela clínica do usuário         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Stack

| Componente | Tecnologia |
|------------|------------|
| Banco | PostgreSQL 15 |
| Autenticação | Supabase Auth |
| Segurança | Row Level Security |
| API | FastAPI + supabase-py |

---

## 3. Convenções

### 3.1 Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Tabelas | snake_case, plural | `pacientes`, `contas_pagar` |
| Colunas | snake_case | `data_nascimento`, `created_at` |
| Primary Key | `id` (UUID) | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| Foreign Key | `{tabela}_id` | `paciente_id`, `medico_id` |
| Timestamps | `created_at`, `updated_at` | Automáticos |

### 3.2 Campos Padrão

Toda tabela principal inclui:

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
clinica_id UUID NOT NULL REFERENCES clinicas(id),
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

---

## 4. Tabelas Existentes

### 4.1 Lista Completa

| Tabela | Módulo | Descrição |
|--------|--------|-----------|
| `clinicas` | Core | Tenant principal |
| `perfis` | Core | Perfis de acesso |
| `users` | Core | Usuários do sistema |
| `pacientes` | Pacientes | Cadastro de pacientes |
| `pacientes_alergias` | Pacientes | Alergias dos pacientes |
| `pacientes_medicamentos` | Pacientes | Medicamentos em uso |
| `pacientes_convenios` | Pacientes | Convênios do paciente |
| `convenios` | Convênios | Cadastro de convênios |
| `tipos_consulta` | Agenda | Tipos de consulta |
| `horarios_disponiveis` | Agenda | Grade de horários |
| `agendamentos` | Agenda | Agendamentos |
| `agendamentos_historico` | Agenda | Histórico de mudanças |
| `bloqueios_agenda` | Agenda | Bloqueios de agenda |
| `cards` | Kanban | Cards do kanban |
| `cards_checklist` | Kanban | Itens de checklist |
| `cards_historico` | Kanban | Histórico do card |
| `cards_documentos` | Kanban | Documentos anexados |
| `cards_mensagens` | Kanban | Mensagens (WhatsApp) |
| `consultas` | Prontuário | Registro de consultas |
| `prontuarios_soap` | Prontuário | SOAP das consultas |
| `anamneses` | Prontuário | Anamneses |
| `receitas` | Prontuário | Receitas médicas |
| `atestados` | Prontuário | Atestados |
| `exames_solicitados` | Prontuário | Exames solicitados |
| `encaminhamentos` | Prontuário | Encaminhamentos |
| `transcricoes` | Prontuário | Transcrições de áudio |
| `categorias_financeiras` | Financeiro | Categorias |
| `fornecedores` | Financeiro | Fornecedores |
| `contas_pagar` | Financeiro | Contas a pagar |
| `contas_pagar_aprovacoes` | Financeiro | Aprovações |
| `contas_receber` | Financeiro | Contas a receber |
| `contas_bancarias` | Financeiro | Contas bancárias |
| `extrato_bancario` | Financeiro | Extratos |
| `conciliacoes` | Financeiro | Conciliações |

### 4.2 Estruturas Principais

#### clinicas

```sql
CREATE TABLE clinicas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(255),
    endereco VARCHAR(255),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(8),
    fuso_horario VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    logo_url TEXT,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,  -- Mesmo ID do Supabase Auth
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    perfil_id UUID NOT NULL REFERENCES perfis(id),
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    crm VARCHAR(20),
    coren VARCHAR(20),
    especialidade VARCHAR(100),
    status VARCHAR(20) DEFAULT 'ativo',
    ultimo_acesso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### perfis

```sql
CREATE TABLE perfis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    permissoes JSONB NOT NULL DEFAULT '{}',
    is_admin BOOLEAN DEFAULT false,
    is_medico BOOLEAN DEFAULT false,
    is_sistema BOOLEAN DEFAULT false,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clinica_id, nome)
);
```

**Estrutura de permissões:**
```json
{
  "agenda": "CLEX",      // Create, List, Edit, eXclude
  "pacientes": "CLE",
  "prontuario": "CLE",
  "financeiro": "L",
  "configuracoes": "",
  "usuarios": "L"
}
```

#### pacientes

```sql
CREATE TABLE pacientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    nome VARCHAR(255) NOT NULL,
    nome_social VARCHAR(255),
    cpf VARCHAR(11),
    rg VARCHAR(20),
    data_nascimento DATE,
    sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'O')),
    telefone VARCHAR(20),
    telefone_secundario VARCHAR(20),
    email VARCHAR(255),
    aceita_whatsapp BOOLEAN DEFAULT true,
    aceita_email BOOLEAN DEFAULT true,
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(8),
    tipo_sanguineo VARCHAR(5),
    emergencia_nome VARCHAR(255),
    emergencia_telefone VARCHAR(20),
    emergencia_parentesco VARCHAR(50),
    como_conheceu VARCHAR(100),
    indicado_por UUID REFERENCES pacientes(id),
    status VARCHAR(20) DEFAULT 'ativo',
    motivo_bloqueio TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id),
    created_by_self BOOLEAN DEFAULT false,
    UNIQUE(clinica_id, cpf)
);
```

#### tipos_consulta

```sql
CREATE TABLE tipos_consulta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    cor VARCHAR(20),
    duracao_minutos INTEGER NOT NULL DEFAULT 30,
    valor_particular DECIMAL(10,2),
    permite_encaixe BOOLEAN DEFAULT true,
    antecedencia_minima_horas INTEGER DEFAULT 2,
    antecedencia_maxima_dias INTEGER DEFAULT 90,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### agendamentos

```sql
CREATE TABLE agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    tipo_consulta_id UUID NOT NULL REFERENCES tipos_consulta(id),
    data DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME,
    status VARCHAR(30) DEFAULT 'agendado',
    forma_pagamento VARCHAR(20) CHECK (forma_pagamento IN ('particular', 'convenio')),
    convenio_id UUID REFERENCES convenios(id),
    valor_previsto DECIMAL(10,2),
    observacoes TEXT,
    confirmado_em TIMESTAMPTZ,
    checkin_em TIMESTAMPTZ,
    chamado_em TIMESTAMPTZ,
    finalizado_em TIMESTAMPTZ,
    card_id UUID,
    consulta_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id)
);
```

#### bloqueios_agenda

```sql
CREATE TABLE bloqueios_agenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    medico_id UUID REFERENCES users(id),
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    hora_inicio TIME,
    hora_fim TIME,
    motivo VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) CHECK (tipo IN ('ferias', 'feriado', 'congresso', 'pessoal', 'outro')),
    recorrente_anual BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### cards

```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    agendamento_id UUID REFERENCES agendamentos(id),
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    fase INTEGER NOT NULL DEFAULT 0,
    coluna VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    prioridade VARCHAR(20) DEFAULT 'normal',
    cor_alerta VARCHAR(20),
    posicao INTEGER DEFAULT 0,
    paciente_nome VARCHAR(255),
    paciente_telefone VARCHAR(20),
    data_agendamento DATE,
    hora_agendamento TIME,
    tipo_consulta VARCHAR(100),
    observacoes TEXT,
    fase0_em TIMESTAMPTZ,
    fase1_em TIMESTAMPTZ,
    fase2_em TIMESTAMPTZ,
    fase3_em TIMESTAMPTZ,
    concluido_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Row Level Security (RLS)

### 5.1 Policy Padrão

Todas as tabelas têm RLS habilitado:

```sql
-- Habilita RLS
ALTER TABLE pacientes ENABLE ROW LEVEL SECURITY;

-- Policy: usuário só vê dados da sua clínica
CREATE POLICY "pacientes_clinica" ON pacientes
    FOR ALL USING (
        clinica_id IN (
            SELECT clinica_id FROM users WHERE id = auth.uid()
        )
    );
```

### 5.2 Como Funciona

1. Usuário faz login → Supabase Auth gera JWT
2. JWT contém `sub` (user ID)
3. `auth.uid()` retorna esse ID
4. Policy verifica: `users.clinica_id WHERE users.id = auth.uid()`
5. Query só retorna registros da clínica do usuário

### 5.3 Tabelas com RLS

| Tabela | RLS Habilitado |
|--------|---------------|
| clinicas | ✅ |
| perfis | ✅ |
| users | ✅ |
| pacientes | ✅ |
| agendamentos | ✅ |
| cards | ✅ |
| tipos_consulta | ✅ |
| bloqueios_agenda | ✅ |
| ... | ✅ |

---

## 6. Integrações com Backend

### 6.1 Cliente Autenticado

O backend usa o token do usuário para criar cliente Supabase:

```python
# backend/app/core/database.py

def get_db(access_token: str) -> SupabaseClient:
    """Cliente autenticado - RLS funciona automaticamente."""
    client = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {access_token}"}
        )
    )
    return SupabaseClient(client)
```

### 6.2 Uso no Service

```python
class PacienteService:
    async def list(self, current_user: CurrentUser):
        db = get_db(current_user.access_token)
        
        # Não precisa filtrar por clinica_id!
        # RLS faz isso automaticamente
        pacientes = await db.select("pacientes")
        
        return pacientes
```

### 6.3 Vantagens

| Aspecto | Descrição |
|---------|-----------|
| Segurança | Impossível vazamento entre clínicas |
| Simplicidade | Não precisa filtrar manualmente |
| Performance | Query otimizada pelo PostgreSQL |
| Manutenção | Regra centralizada no banco |

---

## Apêndice A: Tabelas Faltando

As seguintes tabelas estão documentadas mas **ainda não existem**:

| Tabela | Módulo | Status |
|--------|--------|--------|
| `evidencias` | Evidências | ❌ Não existe |
| `evidencias_regras` | Evidências | ❌ Não existe |
| `clinicas_configuracoes` | Clínicas | ❌ Não existe |
| `audit_logs` | Auditoria | ❌ Não existe |
| `alertas_seguranca` | Auditoria | ❌ Não existe |

### Workarounds implementados:

- **Configurações**: Retorna valores default hardcoded
- **Evidências**: Retorna listas vazias
- **Métricas**: Calculadas via query simples (sem RPC)

---

## Apêndice B: Funções RPC Não Implementadas

| Função | Uso Original | Workaround |
|--------|--------------|------------|
| `get_cards_kanban` | Buscar cards para Kanban | Query direta na tabela cards |
| `get_metricas_agenda` | Dashboard de métricas | Cálculo via COUNT/SUM |
| `verificar_evidencias` | Validar evidências | Retorna sempre OK |
| `get_bloqueios_dia` | Bloqueios do dia | Query direta |

---

**Documento atualizado em:** Janeiro 2026  
**Versão:** 1.1  
**Principais mudanças:**
- Documentadas tabelas reais existentes
- Identificadas tabelas faltando
- Explicado funcionamento do RLS com backend
- Removidas referências a funções RPC não implementadas
