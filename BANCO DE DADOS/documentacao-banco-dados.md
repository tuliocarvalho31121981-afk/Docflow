# Documentação do Banco de Dados
## Sistema de Gestão de Clínicas Médicas

**Versão:** 1.0  
**Data:** Janeiro 2026  
**Tecnologia:** PostgreSQL 15+ (Supabase)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Convenções](#3-convenções)
4. [Fase 1: Fundação](#4-fase-1-fundação)
5. [Fase 2: Agenda](#5-fase-2-agenda)
6. [Fase 3: Cards (Kanban)](#6-fase-3-cards-kanban)
7. [Fase 4: Prontuário](#7-fase-4-prontuário)
8. [Fase 5: Financeiro](#8-fase-5-financeiro)
9. [Fase 6: Auditoria](#9-fase-6-auditoria)
10. [Fase 7: Evidências](#10-fase-7-evidências)
11. [Triggers e Automações](#11-triggers-e-automações)
12. [Functions](#12-functions)
13. [Row Level Security (RLS)](#13-row-level-security-rls)
14. [Índices](#14-índices)
15. [Integrações Externas](#15-integrações-externas)
16. [Retenção de Dados](#16-retenção-de-dados)

---

## 1. Visão Geral

### 1.1 Propósito

Sistema completo de gestão de clínicas médicas com:

- Gestão de pacientes e prontuários
- Agendamento e jornada do paciente (Kanban)
- Financeiro (contas a pagar/receber, conciliação)
- Auditoria e conformidade (LGPD, CFM, ANS)
- Evidências documentais

### 1.2 Atores do Sistema

| Ator | Descrição | Acesso |
|------|-----------|--------|
| **users** | Funcionários da clínica | Login no sistema (Supabase Auth) |
| **pacientes** | Clientes externos | Via WhatsApp/links públicos, SEM login |
| **sistema** | Automações | Triggers, cron jobs, IA |

### 1.3 Rastreio de Ações

Todas as tabelas que registram ações incluem:

```sql
created_by_user UUID        -- Se funcionário fez
created_by_paciente BOOLEAN -- Se paciente fez via WhatsApp
created_by_sistema BOOLEAN  -- Se foi automático
```

---

## 2. Arquitetura

### 2.1 Stack Tecnológico

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│              React + Vite + TailwindCSS                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    SUPABASE                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │  Auth   │  │Database │  │ Storage │  │Realtime │    │
│  │  2FA    │  │PostgreSQL│ │  Files  │  │  WS     │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 BACKEND AUXILIAR                         │
│                    (FastAPI)                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Whisper │  │ Claude  │  │WhatsApp │  │   OCR   │    │
│  │  (STT)  │  │  (IA)   │  │Evolution│  │ Vision  │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Multi-Tenancy

Todas as tabelas incluem `clinica_id` para isolamento de dados:

```sql
clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE
```

Row Level Security (RLS) garante que usuários só vejam dados da sua clínica.

---

## 3. Convenções

### 3.1 Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Tabelas | snake_case, plural | `pacientes`, `contas_pagar` |
| Colunas | snake_case | `data_nascimento`, `created_at` |
| Primary Key | `id` (UUID) | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| Foreign Key | `{tabela}_id` | `paciente_id`, `medico_id` |
| Timestamps | `created_at`, `updated_at` | Automáticos via trigger |
| Status | ENUM como VARCHAR + CHECK | `status VARCHAR(30) CHECK (...)` |

### 3.2 Tipos de Dados

| Tipo | Uso |
|------|-----|
| `UUID` | IDs (gen_random_uuid()) |
| `VARCHAR(n)` | Strings com limite |
| `TEXT` | Strings sem limite |
| `DECIMAL(10,2)` | Valores monetários |
| `DATE` | Datas |
| `TIME` | Horários |
| `TIMESTAMP WITH TIME ZONE` | Data/hora com fuso |
| `JSONB` | Dados flexíveis |
| `TEXT[]` | Arrays de strings |
| `BOOLEAN` | Flags |
| `INTEGER` | Números inteiros |
| `INET` | Endereços IP |

### 3.3 Campos Padrão

Toda tabela principal inclui:

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

---

## 4. Fase 1: Fundação

### 4.1 clinicas

Tenant principal do sistema. Todos os dados pertencem a uma clínica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| nome | VARCHAR(255) | Nome da clínica |
| cnpj | VARCHAR(14) | CNPJ (único) |
| telefone | VARCHAR(20) | Telefone principal |
| email | VARCHAR(255) | Email principal |
| endereco | VARCHAR(255) | Logradouro |
| cidade | VARCHAR(100) | Cidade |
| uf | CHAR(2) | Estado |
| cep | VARCHAR(8) | CEP |
| fuso_horario | VARCHAR(50) | Ex: 'America/Sao_Paulo' |
| logo_url | TEXT | URL do logo |
| saldo_minimo_alerta | DECIMAL(10,2) | Alerta de saldo baixo |
| ativo | BOOLEAN | Status |

**Triggers:**
- `on_clinica_created`: Cria perfis, tipos de consulta e categorias padrão

---

### 4.2 perfis

Define permissões por tipo de usuário.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(100) | Nome do perfil |
| descricao | TEXT | Descrição |
| permissoes | JSONB | Matriz de permissões |
| is_admin | BOOLEAN | É administrador? |
| is_medico | BOOLEAN | Acesso a prontuário? |
| is_sistema | BOOLEAN | Perfil de sistema? |

**Estrutura de permissões:**

```json
{
  "agenda": "CLEX",
  "pacientes": "CLE",
  "prontuario": "CLE",
  "financeiro": "L",
  "configuracoes": ""
}
```

Onde: C=Create, L=List/Read, E=Edit, X=Delete

**Perfis padrão criados automaticamente:**

| Perfil | Admin | Médico | Permissões |
|--------|-------|--------|------------|
| Administrador | ✅ | ❌ | Tudo |
| Médico | ❌ | ✅ | Agenda, Pacientes, Prontuário |
| Enfermagem | ❌ | ✅ | Agenda, Pacientes, Prontuário (sem receita) |
| Secretária | ❌ | ❌ | Agenda, Pacientes (básico) |
| Financeiro | ❌ | ❌ | Financeiro |
| Recepção | ❌ | ❌ | Agenda (somente leitura) |

---

### 4.3 users

Funcionários da clínica (integrado com Supabase Auth).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK (mesmo ID do Supabase Auth) |
| clinica_id | UUID | FK → clinicas |
| perfil_id | UUID | FK → perfis |
| nome | VARCHAR(255) | Nome completo |
| email | VARCHAR(255) | Email (único) |
| telefone | VARCHAR(20) | Telefone |
| crm | VARCHAR(20) | CRM (se médico) |
| coren | VARCHAR(20) | COREN (se enfermagem) |
| especialidade | VARCHAR(100) | Especialidade médica |
| horario_acesso | JSONB | Restrição de horário |
| dias_acesso | JSONB | Restrição de dias |
| status | VARCHAR(20) | ativo, inativo, bloqueado |

---

### 4.4 pacientes

Clientes da clínica (SEM login no sistema).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(255) | Nome completo |
| cpf | VARCHAR(11) | CPF (único por clínica) |
| data_nascimento | DATE | Data de nascimento |
| sexo | VARCHAR(1) | M, F, O |
| telefone | VARCHAR(20) | WhatsApp principal |
| email | VARCHAR(255) | Email |
| endereco | VARCHAR(255) | Logradouro |
| cidade | VARCHAR(100) | Cidade |
| uf | CHAR(2) | Estado |
| cep | VARCHAR(8) | CEP |
| tipo_sanguineo | VARCHAR(5) | A+, O-, etc |
| emergencia_contato | VARCHAR(255) | Contato de emergência |
| como_conheceu | VARCHAR(100) | Origem do paciente |
| indicado_por | UUID | FK → pacientes (indicação) |
| status | VARCHAR(20) | ativo, inativo, bloqueado |

---

### 4.5 pacientes_alergias

Alergias do paciente (dado CRÍTICO - visível em todas as telas).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| paciente_id | UUID | FK → pacientes |
| substancia | VARCHAR(255) | Substância alergênica |
| tipo | VARCHAR(50) | medicamento, alimento, ambiente, outro |
| gravidade | VARCHAR(20) | leve, moderada, grave, anafilaxia |
| reacao | TEXT | Descrição da reação |
| confirmada | BOOLEAN | Confirmada por médico? |
| confirmada_por | UUID | FK → users (médico) |

---

### 4.6 pacientes_medicamentos

Medicamentos de uso contínuo (dado ALTO).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| paciente_id | UUID | FK → pacientes |
| nome | VARCHAR(255) | Nome comercial |
| principio_ativo | VARCHAR(255) | Princípio ativo |
| dosagem | VARCHAR(50) | Ex: "50mg" |
| posologia | VARCHAR(255) | Ex: "1x ao dia, manhã" |
| motivo | TEXT | Por que usa |
| uso_continuo | BOOLEAN | É uso contínuo? |

---

## 5. Fase 2: Agenda

### 5.1 tipos_consulta

Define tipos de atendimento disponíveis.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(100) | Ex: "Consulta", "Retorno" |
| duracao_minutos | INTEGER | Duração padrão |
| valor_particular | DECIMAL(10,2) | Valor para particular |
| cor | VARCHAR(7) | Cor no calendário (#RRGGBB) |
| permite_encaixe | BOOLEAN | Permite encaixe? |
| antecedencia_minima | INTEGER | Mínimo de horas para agendar |
| antecedencia_maxima | INTEGER | Máximo de dias para agendar |
| ativo | BOOLEAN | Status |

**Tipos padrão:**
- Consulta (30min)
- Retorno (20min)
- Check-up (60min)
- Urgência (15min)
- Procedimento (45min)

---

### 5.2 horarios_disponiveis

Template semanal de disponibilidade do médico.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| medico_id | UUID | FK → users |
| dia_semana | INTEGER | 0=Dom, 1=Seg, ..., 6=Sáb |
| hora_inicio | TIME | Início do período |
| hora_fim | TIME | Fim do período |
| intervalo_minutos | INTEGER | Intervalo entre slots |
| vagas_por_horario | INTEGER | Vagas simultâneas |
| ativo | BOOLEAN | Status |

---

### 5.3 bloqueios_agenda

Exceções na agenda (férias, feriados, compromissos).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| medico_id | UUID | FK → users (NULL = toda clínica) |
| data_inicio | DATE | Data inicial |
| data_fim | DATE | Data final |
| hora_inicio | TIME | Hora inicial (NULL = dia todo) |
| hora_fim | TIME | Hora final |
| motivo | TEXT | Descrição |
| tipo | VARCHAR(30) | ferias, feriado, pessoal, manutencao |
| recorrente_anual | BOOLEAN | Repete todo ano? |

---

### 5.4 convenios

Convênios aceitos pela clínica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(255) | Nome do convênio |
| codigo_ans | VARCHAR(20) | Código ANS |
| telefone | VARCHAR(20) | Telefone de contato |
| prazo_envio_guias_dias | INTEGER | Prazo para enviar guias |
| prazo_pagamento_dias | INTEGER | Prazo de pagamento |
| valor_consulta | DECIMAL(10,2) | Valor da consulta |
| ativo | BOOLEAN | Status |

---

### 5.5 pacientes_convenios

Carteirinhas do paciente.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| paciente_id | UUID | FK → pacientes |
| convenio_id | UUID | FK → convenios |
| numero_carteirinha | VARCHAR(50) | Número da carteirinha |
| plano | VARCHAR(100) | Nome do plano |
| data_validade | DATE | Validade |
| principal | BOOLEAN | É o principal? |

---

### 5.6 agendamentos

Consultas marcadas (coração da agenda).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| tipo_consulta_id | UUID | FK → tipos_consulta |
| convenio_id | UUID | FK → convenios (se convênio) |
| data | DATE | Data da consulta |
| hora_inicio | TIME | Hora de início |
| hora_fim | TIME | Hora de fim |
| forma_pagamento | VARCHAR(20) | particular, convenio |
| valor_previsto | DECIMAL(10,2) | Valor previsto |
| status | VARCHAR(30) | Ver tabela abaixo |
| confirmado_em | TIMESTAMP | CHECK-IN: Confirmação |
| checkin_em | TIMESTAMP | CHECK-IN: Chegada na clínica |
| chamado_em | TIMESTAMP | CHECK-IN: Chamado pelo médico |
| finalizado_em | TIMESTAMP | CHECK-OUT: Fim da consulta |
| observacoes | TEXT | Observações |
| created_by_user | UUID | FK → users (quem agendou) |
| created_by_paciente | BOOLEAN | Paciente agendou? |

**Status do agendamento:**

| Status | Descrição | Checkpoint |
|--------|-----------|------------|
| agendado | Recém criado | - |
| confirmado | Paciente confirmou | confirmado_em |
| aguardando | Paciente chegou | checkin_em |
| em_atendimento | Médico chamou | chamado_em |
| atendido | Consulta finalizada | finalizado_em |
| faltou | Paciente não compareceu | - |
| cancelado | Cancelado | - |
| remarcado | Foi remarcado | - |

---

### 5.7 agendamentos_historico

Log de mudanças de status (auditoria).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| agendamento_id | UUID | FK → agendamentos |
| status_anterior | VARCHAR(30) | Status antes |
| status_novo | VARCHAR(30) | Status depois |
| alterado_por | UUID | FK → users |
| motivo | TEXT | Motivo da mudança |
| created_at | TIMESTAMP | Quando |

---

## 6. Fase 3: Cards (Kanban)

### 6.1 cards

Objeto central do Kanban. Cada agendamento gera um card.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| agendamento_id | UUID | FK → agendamentos |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| fase | INTEGER | 0, 1, 2 ou 3 |
| coluna | VARCHAR(50) | Coluna atual |
| posicao | INTEGER | Posição na coluna |
| status | VARCHAR(30) | ativo, concluido, cancelado |
| fase0_em | TIMESTAMP | Quando entrou fase 0 |
| fase1_em | TIMESTAMP | Quando entrou fase 1 |
| fase2_em | TIMESTAMP | Quando entrou fase 2 |
| fase3_em | TIMESTAMP | Quando entrou fase 3 |
| concluido_em | TIMESTAMP | Quando concluiu |
| is_derivado | BOOLEAN | É card de retorno? |
| card_origem_id | UUID | FK → cards (origem) |
| card_derivado_id | UUID | FK → cards (derivado) |
| paciente_nome | VARCHAR(255) | Cache do nome |
| paciente_telefone | VARCHAR(20) | Cache do telefone |
| data_agendamento | DATE | Cache da data |

**Fases e colunas:**

| Fase | Nome | Colunas |
|------|------|---------|
| 0 | Agendado | agendado |
| 1 | Pré-Consulta (D-3) | pendente_anamnese, pendente_confirmacao, pronto |
| 2 | Dia da Consulta | aguardando_checkin, em_espera, em_atendimento, finalizado |
| 3 | Pós-Consulta | pendente_documentos, pendente_pagamento, concluido |

---

### 6.2 cards_checklist

Itens pendentes por fase.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| card_id | UUID | FK → cards |
| fase | INTEGER | Fase do item |
| tipo | VARCHAR(50) | Tipo do item |
| descricao | VARCHAR(255) | Descrição |
| obrigatorio | BOOLEAN | É obrigatório? |
| concluido | BOOLEAN | Foi concluído? |
| concluido_em | TIMESTAMP | Quando |
| concluido_por | UUID | FK → users |
| referencia_tipo | VARCHAR(50) | Tipo da referência |
| referencia_id | UUID | ID da referência |

**Tipos de checklist por fase:**

| Fase | Tipo | Descrição |
|------|------|-----------|
| 0 | confirmacao | Confirmar presença |
| 1 | anamnese | Preencher anamnese |
| 1 | exame_upload | Enviar exame |
| 1 | documento | Enviar documento |
| 2 | checkin | Check-in na clínica |
| 2 | pagamento_previo | Pagamento antecipado |
| 3 | documento_envio | Enviar documento ao paciente |
| 3 | pagamento | Pagamento |
| 3 | guia_convenio | Enviar guia ao convênio |
| 3 | retorno | Agendar retorno |
| 3 | exame_cobranca | Cobrar exame |

---

### 6.3 cards_documentos

Arquivos anexados ao card.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| card_id | UUID | FK → cards |
| tipo | VARCHAR(50) | Tipo do documento |
| nome | VARCHAR(255) | Nome do arquivo |
| storage_path | TEXT | Caminho no Storage |
| mime_type | VARCHAR(100) | Tipo MIME |
| tamanho_bytes | INTEGER | Tamanho |
| exame_tipo | VARCHAR(100) | Se exame: tipo |
| exame_data | DATE | Se exame: data |
| exame_laboratorio | VARCHAR(255) | Se exame: laboratório |
| exame_solicitado_id | UUID | FK → exames_solicitados |
| match_status | VARCHAR(20) | pendente, matched, extra |

---

### 6.4 cards_mensagens

Histórico de mensagens WhatsApp do card.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| card_id | UUID | FK → cards |
| direcao | VARCHAR(10) | enviada, recebida |
| tipo | VARCHAR(30) | texto, template, midia, audio |
| conteudo | TEXT | Conteúdo |
| template_nome | VARCHAR(100) | Nome do template |
| status_entrega | VARCHAR(20) | enviada, entregue, lida, falhou |

---

### 6.5 cards_historico

Log de movimentações no Kanban.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| card_id | UUID | FK → cards |
| acao | VARCHAR(50) | Tipo de ação |
| fase_anterior | INTEGER | Fase antes |
| fase_nova | INTEGER | Fase depois |
| coluna_anterior | VARCHAR(50) | Coluna antes |
| coluna_nova | VARCHAR(50) | Coluna depois |
| status_anterior | VARCHAR(30) | Status antes |
| status_novo | VARCHAR(30) | Status depois |
| detalhes | JSONB | Detalhes extras |
| alterado_por | UUID | FK → users |

---

### 6.6 anamneses

Questionário pré-consulta.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| card_id | UUID | FK → cards |
| paciente_id | UUID | FK → pacientes |
| queixa_principal | TEXT | Queixa principal |
| duracao_sintomas | VARCHAR(100) | Há quanto tempo |
| doencas_cronicas | TEXT | Doenças crônicas |
| cirurgias_previas | TEXT | Cirurgias anteriores |
| historico_familiar | JSONB | Histórico familiar |
| fumante | BOOLEAN | É fumante? |
| etilista | BOOLEAN | Consome álcool? |
| atividade_fisica | VARCHAR(50) | Frequência |
| medicamentos_atuais | TEXT | Medicamentos em uso |

---

## 7. Fase 4: Prontuário

### 7.1 consultas

Registro principal do atendimento.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| agendamento_id | UUID | FK → agendamentos |
| card_id | UUID | FK → cards |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| iniciada_em | TIMESTAMP | Início da consulta |
| finalizada_em | TIMESTAMP | Fim da consulta |
| duracao_minutos | INTEGER | Duração calculada |
| status | VARCHAR(20) | em_andamento, finalizada, cancelada |
| tipo | VARCHAR(20) | presencial, telemedicina |
| resumo | TEXT | Resumo executivo |

**Sigilo médico (RLS especial):**
- Apenas usuários com `perfil.is_medico = true` podem acessar
- Administradores NÃO têm acesso (CFM 2217/2018)

---

### 7.2 transcricoes

Áudio transcrito (Whisper API).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| consulta_id | UUID | FK → consultas |
| audio_storage_path | TEXT | Caminho do áudio |
| audio_duracao_segundos | INTEGER | Duração |
| transcricao_bruta | TEXT | Texto bruto do Whisper |
| transcricao_revisada | TEXT | Texto revisado |
| status | VARCHAR(20) | processando, concluida, erro |
| modelo_whisper | VARCHAR(50) | Modelo usado |
| idioma | VARCHAR(10) | Idioma detectado |

---

### 7.3 prontuarios_soap

Prontuário estruturado (S-O-A-P).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| subjetivo | TEXT | S - Queixa do paciente |
| objetivo | TEXT | O - Exame físico |
| avaliacao | TEXT | A - Diagnóstico |
| plano | TEXT | P - Conduta |
| exame_fisico | JSONB | Dados estruturados |
| cids | JSONB | Lista de CIDs |
| gerado_por_ia | BOOLEAN | IA gerou? |
| revisado_por_medico | BOOLEAN | Médico revisou? |
| assinado | BOOLEAN | Assinado digitalmente? |
| assinado_em | TIMESTAMP | Quando assinou |

**Estrutura exame_fisico:**

```json
{
  "sinais_vitais": {
    "pressao_arterial": "120/80",
    "frequencia_cardiaca": 72,
    "frequencia_respiratoria": 16,
    "temperatura": 36.5,
    "saturacao": 98,
    "peso": 70.5,
    "altura": 1.75
  },
  "ausculta_cardiaca": "BRNF em 2T, sem sopros",
  "ausculta_pulmonar": "MV+ bilateral, sem RA",
  "abdome": "Plano, RHA+, indolor",
  "extremidades": "Sem edemas"
}
```

**Estrutura cids:**

```json
[
  { "codigo": "I10", "descricao": "Hipertensão essencial", "tipo": "principal" },
  { "codigo": "E11", "descricao": "DM tipo 2", "tipo": "secundario" }
]
```

---

### 7.4 receitas

Prescrições médicas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| tipo | VARCHAR(20) | simples, especial, antimicrobiano |
| itens | JSONB | Lista de medicamentos |
| status | VARCHAR(20) | rascunho, emitida, cancelada |
| assinatura_digital | BOOLEAN | Assinada digitalmente? |
| pdf_storage_path | TEXT | Caminho do PDF |
| enviada_paciente | BOOLEAN | Enviada ao paciente? |

**Estrutura itens:**

```json
[
  {
    "medicamento": "Losartana",
    "concentracao": "50mg",
    "forma_farmaceutica": "comprimido",
    "quantidade": 30,
    "posologia": "1 comprimido pela manhã",
    "duracao": "uso contínuo",
    "observacoes": "Tomar em jejum"
  }
]
```

---

### 7.5 atestados

Atestados médicos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| tipo | VARCHAR(30) | comparecimento, afastamento, aptidao, acompanhante |
| texto | TEXT | Texto do atestado |
| data_inicio | DATE | Data inicial |
| data_fim | DATE | Data final |
| dias_afastamento | INTEGER | Dias de afastamento |
| cid_codigo | VARCHAR(10) | CID (opcional) |
| incluir_cid | BOOLEAN | Incluir CID no atestado? |
| status | VARCHAR(20) | rascunho, emitido, cancelado |
| pdf_storage_path | TEXT | Caminho do PDF |

---

### 7.6 exames_solicitados

Exames pedidos pelo médico.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| codigo_tuss | VARCHAR(20) | Código TUSS |
| nome | VARCHAR(255) | Nome do exame |
| tipo | VARCHAR(50) | laboratorial, imagem, outros |
| indicacao_clinica | TEXT | Indicação clínica |
| cid_codigo | VARCHAR(10) | CID relacionado |
| urgente | BOOLEAN | É urgente? |
| para_retorno | BOOLEAN | Para retorno? |
| prazo_dias | INTEGER | Prazo para resultado |
| status | VARCHAR(30) | Ver tabela abaixo |
| documento_id | UUID | FK → cards_documentos (resultado) |

**Status do exame:**

| Status | Descrição |
|--------|-----------|
| solicitado | Recém pedido |
| guia_emitida | Guia SADT gerada |
| agendado | Paciente agendou |
| realizado | Exame feito |
| resultado_anexado | Resultado recebido |

---

### 7.7 encaminhamentos

Encaminhamento para especialistas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| medico_id | UUID | FK → users |
| especialidade | VARCHAR(100) | Especialidade destino |
| profissional_nome | VARCHAR(255) | Nome do profissional |
| motivo | TEXT | Motivo do encaminhamento |
| cid_codigo | VARCHAR(10) | CID relacionado |
| urgente | BOOLEAN | É urgente? |

---

## 8. Fase 5: Financeiro

### 8.1 categorias_financeiras

Classificação de receitas e despesas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(100) | Nome da categoria |
| tipo | VARCHAR(20) | receita, despesa |
| categoria_pai_id | UUID | FK → categorias_financeiras |
| grupo_dre | VARCHAR(50) | Grupo no DRE |
| cor | VARCHAR(7) | Cor (#RRGGBB) |
| ativo | BOOLEAN | Status |
| is_sistema | BOOLEAN | Categoria padrão? |

**Categorias padrão:**

| Tipo | Categoria | Grupo DRE |
|------|-----------|-----------|
| Receita | Consultas Particulares | receita_operacional |
| Receita | Consultas Convênio | receita_operacional |
| Receita | Procedimentos | receita_operacional |
| Despesa | Aluguel | custo_fixo |
| Despesa | Salários | pessoal |
| Despesa | Material Médico | custo_variavel |
| Despesa | Impostos (DAS) | impostos |
| Despesa | Marketing | operacional |

---

### 8.2 fornecedores

Cadastro de fornecedores.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| nome | VARCHAR(255) | Razão social |
| nome_fantasia | VARCHAR(255) | Nome fantasia |
| tipo_pessoa | VARCHAR(2) | PF, PJ |
| cpf_cnpj | VARCHAR(14) | CPF ou CNPJ |
| telefone | VARCHAR(20) | Telefone |
| email | VARCHAR(255) | Email |
| banco | VARCHAR(100) | Banco |
| agencia | VARCHAR(20) | Agência |
| conta | VARCHAR(30) | Conta |
| pix | VARCHAR(100) | Chave PIX |
| categoria_padrao_id | UUID | FK → categorias_financeiras |
| ativo | BOOLEAN | Status |

---

### 8.3 contas_pagar

Despesas da clínica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| descricao | VARCHAR(255) | Descrição |
| fornecedor_id | UUID | FK → fornecedores |
| categoria_id | UUID | FK → categorias_financeiras |
| valor | DECIMAL(10,2) | Valor total |
| valor_pago | DECIMAL(10,2) | Valor pago |
| data_emissao | DATE | Data de emissão |
| data_vencimento | DATE | Data de vencimento |
| data_pagamento | DATE | Data do pagamento |
| recorrente | BOOLEAN | É recorrente? |
| recorrencia_tipo | VARCHAR(20) | mensal, anual, semanal |
| documento_tipo | VARCHAR(30) | boleto, nf, recibo, guia |
| documento_storage_path | TEXT | Caminho do documento |
| codigo_barras | VARCHAR(100) | Código de barras |
| dados_ia | JSONB | Dados extraídos por OCR/IA |
| status | VARCHAR(30) | Ver tabela abaixo |
| requer_aprovacao | BOOLEAN | Precisa aprovação? |
| aprovado_por | UUID | FK → users |
| aprovado_em | TIMESTAMP | Quando aprovou |
| forma_pagamento | VARCHAR(30) | boleto, pix, transferencia |
| comprovante_storage_path | TEXT | Comprovante de pagamento |
| conciliado | BOOLEAN | Conciliado com extrato? |

**Status:**

| Status | Descrição |
|--------|-----------|
| rascunho | Criado mas não confirmado |
| pendente | Aguardando aprovação/pagamento |
| aprovado | Aprovado, aguardando pagamento |
| pago | Pago |
| atrasado | Vencido e não pago |
| cancelado | Cancelado |

**Regras de aprovação:**

| Valor | Aprovação |
|-------|-----------|
| Até R$ 500 | Automática |
| R$ 500 - R$ 2.000 | Gestor |
| Acima de R$ 2.000 | Dupla aprovação |
| Fornecedor novo | Sempre aprova |

---

### 8.4 contas_receber

Receitas da clínica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| origem | VARCHAR(30) | consulta, convenio, procedimento, outro |
| consulta_id | UUID | FK → consultas |
| paciente_id | UUID | FK → pacientes |
| convenio_id | UUID | FK → convenios |
| descricao | VARCHAR(255) | Descrição |
| categoria_id | UUID | FK → categorias_financeiras |
| valor | DECIMAL(10,2) | Valor total |
| valor_recebido | DECIMAL(10,2) | Valor recebido |
| desconto | DECIMAL(10,2) | Desconto aplicado |
| data_emissao | DATE | Data de emissão |
| data_vencimento | DATE | Data de vencimento |
| data_recebimento | DATE | Data do recebimento |
| guia_numero | VARCHAR(50) | Número da guia (convênio) |
| status | VARCHAR(30) | pendente, parcial, pago, atrasado, glosado, cancelado |
| forma_pagamento | VARCHAR(30) | pix, cartao_credito, cartao_debito, dinheiro, convenio |
| cobranca_enviada | BOOLEAN | Cobrança enviada? |
| cobranca_quantidade | INTEGER | Quantas cobranças |
| conciliado | BOOLEAN | Conciliado? |

---

### 8.5 contas_bancarias

Contas bancárias da clínica.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| banco_codigo | VARCHAR(10) | Código do banco |
| banco_nome | VARCHAR(100) | Nome do banco |
| agencia | VARCHAR(20) | Agência |
| conta | VARCHAR(30) | Conta |
| tipo | VARCHAR(20) | corrente, poupanca |
| apelido | VARCHAR(100) | Nome amigável |
| saldo_atual | DECIMAL(12,2) | Saldo atual |
| saldo_atualizado_em | TIMESTAMP | Última atualização |
| integracao_ativa | BOOLEAN | Importa OFX? |
| principal | BOOLEAN | É a principal? |
| ativo | BOOLEAN | Status |

---

### 8.6 extrato_bancario

Lançamentos importados do banco.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| conta_bancaria_id | UUID | FK → contas_bancarias |
| data | DATE | Data da transação |
| descricao | VARCHAR(255) | Descrição |
| tipo | VARCHAR(20) | credito, debito |
| valor | DECIMAL(10,2) | Valor |
| id_transacao_banco | VARCHAR(100) | ID único do banco |
| conciliado | BOOLEAN | Conciliado? |
| conta_pagar_id | UUID | FK → contas_pagar |
| conta_receber_id | UUID | FK → contas_receber |
| categoria_sugerida_id | UUID | FK → categorias_financeiras |

---

### 8.7 conciliacoes

Registro de conciliações.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| extrato_id | UUID | FK → extrato_bancario |
| conta_pagar_id | UUID | FK → contas_pagar |
| conta_receber_id | UUID | FK → contas_receber |
| tipo | VARCHAR(30) | automatica, manual, tarifa, transferencia |
| conciliado_por | UUID | FK → users |
| conciliado_em | TIMESTAMP | Quando |
| observacao | TEXT | Observações |

---

## 9. Fase 6: Auditoria

### 9.1 audit_logs

Registro imutável de todas as ações.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | ID da clínica (sem FK) |
| user_id | UUID | Quem fez |
| user_nome | VARCHAR(255) | Snapshot do nome |
| user_perfil | VARCHAR(100) | Snapshot do perfil |
| paciente_id | UUID | Se ação do paciente |
| ip_address | INET | IP de origem |
| user_agent | TEXT | User agent |
| acao | VARCHAR(50) | create, read, update, delete, login, export |
| modulo | VARCHAR(50) | prontuario, agenda, financeiro, etc |
| entidade | VARCHAR(50) | Nome da tabela |
| entidade_id | UUID | ID do registro |
| dados_anteriores | JSONB | Estado antes |
| dados_novos | JSONB | Estado depois |
| campos_alterados | TEXT[] | Campos que mudaram |
| descricao | TEXT | Descrição legível |
| sensibilidade | VARCHAR(20) | baixa, normal, alta, critica |
| retencao_ate | DATE | Até quando manter |

**Imutabilidade:**
- Triggers impedem UPDATE e DELETE
- Logs são append-only

**Retenção:**

| Módulo | Retenção |
|--------|----------|
| prontuario, receita, atestado | 20 anos (CFM) |
| financeiro, convenio | 10 anos (ANS) |
| outros | 5 anos |

---

### 9.2 audit_logs_alertas

Alertas de segurança gerados automaticamente.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| audit_log_id | UUID | FK → audit_logs |
| tipo | VARCHAR(50) | acesso_negado, tentativas_login, export_massa |
| severidade | VARCHAR(20) | baixa, media, alta, critica |
| titulo | VARCHAR(255) | Título do alerta |
| descricao | TEXT | Descrição |
| status | VARCHAR(20) | pendente, visto, resolvido, ignorado |
| resolvido_por | UUID | FK → users |
| resolvido_em | TIMESTAMP | Quando resolveu |

**Alertas automáticos:**

| Situação | Severidade |
|----------|------------|
| Acesso a prontuário fora do horário (22h-6h) | Alta |
| Export em massa (>50 registros) | Crítica |
| 5+ tentativas de login falhas | Alta |

---

### 9.3 consentimentos

Registro de consentimentos LGPD.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| paciente_id | UUID | FK → pacientes |
| tipo | VARCHAR(50) | Ver lista abaixo |
| aceito | BOOLEAN | Aceitou? |
| versao_termo | VARCHAR(20) | Versão do termo |
| texto_termo | TEXT | Snapshot do termo |
| meio | VARCHAR(30) | whatsapp, presencial, app, email |
| evidencia_tipo | VARCHAR(30) | mensagem, assinatura, checkbox |
| evidencia_storage_path | TEXT | Caminho da evidência |
| ip_address | INET | IP (se online) |
| valido_ate | DATE | Validade |
| revogado | BOOLEAN | Foi revogado? |
| revogado_em | TIMESTAMP | Quando revogou |

**Tipos de consentimento:**

| Tipo | Obrigatório | Descrição |
|------|-------------|-----------|
| tratamento_dados | ✅ | Tratamento de dados pessoais |
| comunicacao_whatsapp | ✅ | Comunicação via WhatsApp |
| compartilhar_convenio | ✅ | Compartilhar com convênio |
| marketing | ❌ | Receber promoções |
| pesquisa | ❌ | Uso para pesquisa |
| compartilhar_terceiros | ❌ | Compartilhar com parceiros |

---

### 9.4 notificacoes

Notificações para usuários.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| user_id | UUID | FK → users (destinatário) |
| perfil_destino | VARCHAR(100) | Se para todo perfil |
| titulo | VARCHAR(255) | Título |
| mensagem | TEXT | Mensagem |
| tipo | VARCHAR(30) | info, alerta, erro, sucesso, tarefa |
| prioridade | VARCHAR(20) | baixa, normal, alta, urgente |
| link_tipo | VARCHAR(50) | Tipo do link |
| link_id | UUID | ID do link |
| lida | BOOLEAN | Foi lida? |
| lida_em | TIMESTAMP | Quando leu |
| expira_em | TIMESTAMP | Expiração |

---

### 9.5 sessoes

Registro de sessões de usuário.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| clinica_id | UUID | FK → clinicas |
| token_hash | VARCHAR(255) | Hash do token |
| ip_address | INET | IP |
| user_agent | TEXT | User agent |
| dispositivo | VARCHAR(100) | Ex: "Chrome/Windows" |
| cidade | VARCHAR(100) | Cidade (aproximada) |
| pais | VARCHAR(100) | País |
| ativa | BOOLEAN | Sessão ativa? |
| iniciada_em | TIMESTAMP | Início |
| ultimo_acesso | TIMESTAMP | Último acesso |
| encerrada_em | TIMESTAMP | Quando encerrou |
| encerrada_por | VARCHAR(30) | logout, expiracao, admin, seguranca |

---

### 9.6 tentativas_login

Registro de tentativas de login.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| email | VARCHAR(255) | Email tentado |
| user_id | UUID | FK → users (se existe) |
| sucesso | BOOLEAN | Login bem sucedido? |
| motivo_falha | VARCHAR(50) | senha_incorreta, usuario_inexistente, bloqueado, 2fa_falhou |
| ip_address | INET | IP |
| user_agent | TEXT | User agent |

**Bloqueio:**
- 5 tentativas falhas em 30 minutos = bloqueio temporário

---

## 10. Fase 7: Evidências

### 10.1 evidencias

Provas documentais de ações.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| clinica_id | UUID | FK → clinicas |
| entidade | VARCHAR(50) | Tabela de origem |
| entidade_id | UUID | ID do registro |
| tipo | VARCHAR(50) | Tipo da evidência |
| categoria | VARCHAR(30) | documento, api_response, assinatura, comprovante, log_sistema, mensagem, formulario |
| descricao | VARCHAR(255) | Descrição |
| arquivo_nome | VARCHAR(255) | Nome do arquivo |
| arquivo_path | TEXT | Caminho no Storage |
| arquivo_mime_type | VARCHAR(100) | Tipo MIME |
| arquivo_tamanho_bytes | INTEGER | Tamanho |
| arquivo_hash | VARCHAR(64) | SHA-256 |
| dados | JSONB | Dados estruturados |
| origem | VARCHAR(50) | usuario, paciente, sistema, api_externa, ia |
| validado | BOOLEAN | Foi validado? |
| validado_por | UUID | FK → users |
| validado_em | TIMESTAMP | Quando validou |
| status | VARCHAR(20) | ativo, substituido, invalido |
| substituido_por | UUID | FK → evidencias |
| audit_log_id | UUID | FK → audit_logs |
| retencao_ate | DATE | Até quando manter |

**Tipos de evidência por entidade:**

| Entidade | Tipo | Descrição |
|----------|------|-----------|
| agendamentos | elegibilidade_convenio | Resposta API convênio |
| agendamentos | confirmacao_paciente | Confirmação WhatsApp |
| contas_pagar | nota_fiscal | NF (PDF/XML) |
| contas_pagar | boleto | Boleto bancário |
| contas_pagar | comprovante_pagamento | Comprovante |
| contas_pagar | aprovacao | Log de aprovação |
| receitas | pdf_assinado | PDF da receita |
| atestados | pdf_assinado | PDF do atestado |
| consentimentos | termo_aceito | Registro do aceite |

---

### 10.2 evidencias_obrigatorias

Regras de evidências obrigatórias.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| entidade | VARCHAR(50) | Tabela |
| acao | VARCHAR(50) | Ação |
| tipos_evidencia | TEXT[] | Tipos necessários |
| quantidade_minima | INTEGER | Mínimo necessário |
| logica | VARCHAR(10) | AND, OR |
| excecao_perfis | TEXT[] | Perfis que não precisam |
| excecao_valor_ate | DECIMAL(10,2) | Valor de exceção |
| mensagem_erro | VARCHAR(255) | Mensagem de erro |
| ativo | BOOLEAN | Status |

**Regras padrão:**

| Entidade | Ação | Evidências | Lógica |
|----------|------|------------|--------|
| contas_pagar | criar | NF, boleto, recibo | OR |
| contas_pagar | pagar | comprovante | AND |
| contas_pagar | aprovar | log aprovação | AND |
| contas_receber | receber | comprovante | AND |
| agendamentos | confirmar_convenio | elegibilidade | AND |
| receitas | emitir | PDF assinado | AND |
| atestados | emitir | PDF assinado | AND |
| consentimentos | registrar | termo, assinatura ou WhatsApp | OR |

---

## 11. Triggers e Automações

### 11.1 Triggers de updated_at

Todas as tabelas com `updated_at` têm trigger automático:

```sql
CREATE TRIGGER trigger_{tabela}_updated_at
    BEFORE UPDATE ON {tabela}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### 11.2 Triggers de Negócio

| Trigger | Tabela | Evento | Ação |
|---------|--------|--------|------|
| on_clinica_created | clinicas | INSERT | Cria perfis, tipos_consulta, categorias padrão |
| on_agendamento_status_change | agendamentos | UPDATE | Registra histórico |
| on_agendamento_created | agendamentos | INSERT | Cria card |
| on_card_created | cards | INSERT | Cria checklist padrão |
| on_agendamento_status_change_update_card | agendamentos | UPDATE | Sincroniza card |
| on_agendamento_em_atendimento | agendamentos | UPDATE | Cria consulta |
| on_agendamento_atendido | agendamentos | UPDATE | Finaliza consulta |
| on_consulta_finalizada_criar_conta | consultas | UPDATE | Cria conta a receber |
| verificar_aprovacao_conta_pagar | contas_pagar | INSERT | Define aprovação necessária |
| on_receita_emitida | receitas | UPDATE | Registra evidência |
| on_atestado_emitido | atestados | UPDATE | Registra evidência |
| on_conta_pagar_aprovada | contas_pagar | UPDATE | Registra evidência |
| on_conta_pagar_paga | contas_pagar | UPDATE | Registra evidência |
| audit_prontuario | consultas, prontuarios_soap, receitas, atestados | INSERT/UPDATE | Registra audit_log |
| detectar_acesso_suspeito | audit_logs | INSERT | Gera alertas |
| verificar_tentativas_login | tentativas_login | INSERT | Verifica bloqueio |
| prevent_audit_modification | audit_logs | UPDATE/DELETE | Impede alteração |

### 11.3 Jobs Agendados (Cron)

| Job | Frequência | Ação |
|-----|------------|------|
| mover_cards_para_pre_consulta | Diário 00:00 | Move cards D-3 para fase 1 |
| mover_cards_para_dia_consulta | Diário 00:00 | Move cards do dia para fase 2 |
| atualizar_contas_atrasadas | Diário 00:00 | Marca contas vencidas |

---

## 12. Functions

### 12.1 Functions de Consulta

| Function | Parâmetros | Retorno | Descrição |
|----------|------------|---------|-----------|
| get_slots_disponiveis | clinica_id, medico_id, data | TABLE | Horários livres |
| get_metricas_dia | clinica_id, data | TABLE | Métricas do dia |
| get_cards_kanban | clinica_id, fase | TABLE | Cards com checklist |
| get_historico_paciente | paciente_id | TABLE | Consultas anteriores |
| get_ultima_consulta | paciente_id | RECORD | Última consulta |
| get_fluxo_caixa | clinica_id, data_inicio, data_fim | TABLE | Fluxo de caixa |
| get_dre_simplificado | clinica_id, mes, ano | TABLE | DRE mensal |
| get_resumo_financeiro | clinica_id | RECORD | Dashboard financeiro |
| get_audit_report | clinica_id, data_inicio, data_fim | TABLE | Relatório de auditoria |
| get_evidencias | entidade, entidade_id | TABLE | Evidências da entidade |

### 12.2 Functions de Ação

| Function | Parâmetros | Retorno | Descrição |
|----------|------------|---------|-----------|
| criar_perfis_padrao | clinica_id | void | Cria perfis padrão |
| criar_tipos_consulta_padrao | clinica_id | void | Cria tipos de consulta |
| criar_categorias_padrao | clinica_id | void | Cria categorias financeiras |
| criar_card_derivado | card_origem_id, exames[], prazo_dias | UUID | Cria card de retorno |
| registrar_audit_log | ... | UUID | Registra log de auditoria |
| registrar_evidencia | ... | UUID | Registra evidência |
| gerar_alerta_seguranca | ... | UUID | Gera alerta de segurança |

### 12.3 Functions de Validação

| Function | Parâmetros | Retorno | Descrição |
|----------|------------|---------|-----------|
| verificar_bloqueio_login | email | TABLE | Verifica bloqueio |
| verificar_consentimento | paciente_id, tipo | BOOLEAN | Verifica consentimento |
| verificar_evidencias | entidade, entidade_id, acao | TABLE | Valida evidências |
| verificar_integridade_evidencia | evidencia_id | TABLE | Verifica hash |

---

## 13. Row Level Security (RLS)

### 13.1 Policy Padrão

Todas as tabelas têm RLS habilitado com policy básica:

```sql
CREATE POLICY "{tabela}_clinica" ON {tabela}
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );
```

### 13.2 Policies Especiais

**Prontuário (sigilo médico):**

```sql
-- Apenas médicos acessam
CREATE POLICY "prontuario_medico" ON consultas
    FOR ALL USING (
        clinica_id IN (
            SELECT u.clinica_id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_medico = true
        )
    );
```

**Audit Logs (apenas admin):**

```sql
CREATE POLICY "audit_admin" ON audit_logs
    FOR SELECT USING (
        clinica_id IN (
            SELECT u.clinica_id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
    );
```

**Notificações (usuário ou perfil):**

```sql
CREATE POLICY "notificacoes_usuario" ON notificacoes
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        AND (
            user_id = auth.uid()
            OR perfil_destino IN (
                SELECT p.nome FROM users u
                JOIN perfis p ON p.id = u.perfil_id
                WHERE u.id = auth.uid()
            )
        )
    );
```

---

## 14. Índices

### 14.1 Índices Principais

Todas as tabelas têm índice em:
- `clinica_id` (multi-tenant)
- `created_at` (ordenação temporal)
- Foreign keys relevantes

### 14.2 Índices Compostos

| Tabela | Índice | Colunas | Filtro |
|--------|--------|---------|--------|
| agendamentos | idx_agendamentos_busca | clinica_id, medico_id, data, status | - |
| cards | idx_cards_kanban | clinica_id, fase, coluna | status = 'ativo' |
| contas_pagar | idx_contas_pagar_atrasadas | data_vencimento, status | status IN ('pendente', 'aprovado') |
| contas_receber | idx_contas_receber_cobranca | status, data_vencimento | status IN ('pendente', 'atrasado') |
| evidencias | idx_evidencias_entidade_ativa | entidade, entidade_id, status | status = 'ativo' |

### 14.3 Índices Únicos

| Tabela | Índice | Colunas |
|--------|--------|---------|
| clinicas | idx_clinicas_cnpj | cnpj |
| users | idx_users_email | email |
| pacientes | idx_pacientes_cpf_clinica | clinica_id, cpf |
| extrato_bancario | idx_extrato_unico | conta_bancaria_id, id_transacao_banco |

---

## 15. Integrações Externas

### 15.1 APIs Externas

| Serviço | Propósito | Dados |
|---------|-----------|-------|
| Whisper API | Transcrição de áudio | transcricoes |
| Claude/DeepSeek | IA para SOAP | prontuarios_soap |
| Evolution API | WhatsApp | cards_mensagens |
| Google Vision | OCR de documentos | contas_pagar.dados_ia |

### 15.2 Webhooks

| Evento | Origem | Destino |
|--------|--------|---------|
| Mensagem recebida | WhatsApp | cards_mensagens |
| Transcrição concluída | Whisper | transcricoes |
| SOAP gerado | Claude | prontuarios_soap |

---

## 16. Retenção de Dados

### 16.1 Períodos de Retenção

| Tipo de Dado | Período | Base Legal |
|--------------|---------|------------|
| Prontuário médico | 20 anos | CFM 1821/2007 |
| Receitas e atestados | 20 anos | CFM 1821/2007 |
| Documentos financeiros | 10 anos | ANS RN 389/2015 |
| Audit logs | Variável por módulo | LGPD Art. 37 |
| Consentimentos | 10 anos após revogação | LGPD Art. 8 |
| Outros | 5 anos | Padrão |

### 16.2 Exclusão de Dados

- Dados pessoais: Paciente pode solicitar exclusão (LGPD Art. 18)
- Prontuário: NÃO pode ser excluído (sigilo médico)
- Audit logs: NUNCA são excluídos
- Evidências: Arquivadas após período de retenção

---

## Apêndice A: Diagrama ER

Ver arquivo `diagrama-er.mermaid`

## Apêndice B: Scripts SQL

- `schema-fase1-fundacao.sql`
- `schema-fase2-agenda.sql`
- `schema-fase3-cards.sql`
- `schema-fase4-prontuario.sql`
- `schema-fase5-financeiro.sql`
- `schema-fase6-auditoria.sql`
- `schema-fase7-evidencias.sql`

---

**Documento gerado em:** Janeiro 2026  
**Versão:** 1.0
