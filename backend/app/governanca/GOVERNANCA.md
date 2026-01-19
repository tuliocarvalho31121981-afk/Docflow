# Sistema de Governança - Documentação

## Conceito Central

A **governança** transforma a recepcionista em **supervisora do sistema automatizado**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ANTES                              DEPOIS                                 │
│   ─────                              ──────                                 │
│                                                                             │
│   Recepcionista FAZ tudo    →    Recepcionista VALIDA tudo                 │
│   (operacional)                  (governança)                               │
│                                                                             │
│   - Atende telefone              - Valida agendamentos                     │
│   - Agenda consulta              - Verifica evidências                      │
│   - Confirma paciente            - Corrige erros do sistema                │
│   - Faz check-in                 - Treina a IA (feedback)                  │
│   - Move Kanban                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Arquitetura: Kanban + Evidências + Governança

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              KANBAN                                         │
│                           (Backbone)                                        │
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │  FASE 0  │───►│  FASE 1  │───►│  FASE 2  │───►│  FASE 3  │            │
│   │ Agendado │    │Pré-Consul│    │Dia Consul│    │Pós-Consul│            │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘            │
│        │               │               │               │                   │
│        ▼               ▼               ▼               ▼                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ TAREFAS  │    │ TAREFAS  │    │ TAREFAS  │    │ TAREFAS  │            │
│   │ Checklist│    │ Checklist│    │ Checklist│    │ Checklist│            │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘            │
│        │               │               │               │                   │
│        ▼               ▼               ▼               ▼                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │EVIDÊNCIAS│    │EVIDÊNCIAS│    │EVIDÊNCIAS│    │EVIDÊNCIAS│            │
│   │ Logs     │    │ Logs     │    │ Logs     │    │ Logs     │            │
│   │ Docs     │    │ Docs     │    │ Docs     │    │ Docs     │            │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘            │
│        │               │               │               │                   │
│        └───────────────┴───────────────┴───────────────┘                   │
│                                    │                                        │
│                                    ▼                                        │
│                           ┌──────────────┐                                  │
│                           │  GOVERNANÇA  │                                  │
│                           │              │                                  │
│                           │  Validação   │                                  │
│                           │  por Trigger │                                  │
│                           └──────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Os 3 Triggers de Validação

### TRIGGER 1: Mensagem WhatsApp Processada

```
QUANDO: Sistema processa mensagem do paciente

O QUE VERIFICA:
├── Paciente identificado/criado corretamente?
├── Intenção interpretada corretamente?
├── Resposta enviada foi adequada?
└── Ação executada foi correta?

EVIDÊNCIAS:
├── Log: Mensagem recebida (texto, timestamp)
├── Log: Paciente ID (existente ou criado)
├── Log: Intenção detectada (com confiança %)
├── Log: Ação executada
└── Log: Resposta enviada (message_id)

EXEMPLO NA TELA:
┌─────────────────────────────────────────────────────────────────┐
│ 💬 Mensagem WhatsApp                                            │
│                                                                 │
│ "quero remarcar pra semana que vem"                            │
│ → Interpretado: REMARCAR (85% confiança)                       │
│ → Paciente: Maria Silva (ID: pac_123)                          │
│ → Ação: Listou horários disponíveis                            │
│                                                                 │
│ EVIDÊNCIAS:                                                     │
│ ✅ Log: Mensagem recebida - 15/01 10:30:22                     │
│ ✅ Log: Paciente identificado - pac_123                        │
│ ✅ Log: Intenção: remarcar (0.85)                              │
│ ✅ Log: Resposta enviada - msg_456                             │
│                                                                 │
│ [✅ Aprovar]  [✏️ Corrigir]  [❌ Rejeitar]                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### TRIGGER 2: Card Criado

```
QUANDO: Sistema cria card no Kanban (após agendamento)

O QUE VERIFICA:
├── Paciente verificado/criado corretamente?
├── Horário reservado existe e está livre?
├── Médico correto associado?
├── Confirmação enviada ao paciente?
└── Card criado na fase correta?

EVIDÊNCIAS:
├── Log: Paciente ID + dados básicos
├── Log: Slot ID + data/hora
├── Log: Médico ID + especialidade
├── Log: Message ID da confirmação
└── Log: Card ID + fase inicial

EXEMPLO NA TELA:
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Card Criado                                                  │
│                                                                 │
│ João Santos - Consulta 22/01 09:00                             │
│ Dr. Carlos - Cardiologia                                        │
│                                                                 │
│ CHECKLIST FASE 0:                                               │
│ ✅ Paciente verificado    Log: pac_789 (existente)             │
│ ✅ Horário reservado      Log: slot_456, 22/01 09:00           │
│ ✅ Confirmação enviada    Log: msg_789                         │
│ ⏳ Paciente confirmou     Aguardando resposta                  │
│                                                                 │
│ 3/4 tarefas completas                                          │
│                                                                 │
│ [✅ Aprovar]  [✏️ Corrigir]  [❌ Rejeitar]                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### TRIGGER 3: Mudança de Fase

```
QUANDO: Card muda de uma fase para outra

O QUE VERIFICA:
├── TODAS as tarefas obrigatórias da fase anterior completas?
├── Evidências de cada tarefa presentes?
├── Documentos necessários anexados?
└── Transição faz sentido no contexto?

EVIDÊNCIAS:
├── Logs de cada tarefa automática
├── Documentos enviados pelo paciente
├── Documentos gerados pelo sistema
└── Timestamps de cada ação

EXEMPLO NA TELA:
┌─────────────────────────────────────────────────────────────────┐
│ ➡️ Mudança de Fase: 1 → 2                                       │
│                                                                 │
│ Maria Silva - Consulta 20/01 15:00                             │
│                                                                 │
│ CHECKLIST FASE 1 (Pré-Consulta):                               │
│                                                                 │
│ ✅ Anamnese enviada                                            │
│    └─ 📝 Log: msg_123 - 17/01 10:03                           │
│                                                                 │
│ ✅ Anamnese preenchida                                         │
│    └─ 📄 anamnese_maria.pdf - 17/01 14:45                     │
│       [Abrir documento]                                        │
│                                                                 │
│ ✅ Carteirinha convênio (opcional)                             │
│    └─ 🖼️ carteirinha.jpg - 18/01 09:12                        │
│       [Ver imagem]                                             │
│                                                                 │
│ ✅ Exames recebidos (opcional)                                 │
│    └─ 📄 hemograma.pdf - 19/01 11:30                          │
│    └─ 📄 glicemia.pdf - 19/01 11:32                           │
│       [Ver exames]                                             │
│                                                                 │
│ ✅ Lembrete D-1 enviado                                        │
│    └─ 📝 Log: msg_456 - 19/01 18:00                           │
│                                                                 │
│ 5/5 obrigatórias completas ✓                                   │
│                                                                 │
│ [✅ Aprovar Transição]  [✏️ Corrigir]  [❌ Bloquear]          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tipos de Evidência

### LOG (automático)
```
Exemplos:
- Mensagem enviada (message_id, timestamp)
- Paciente identificado (paciente_id, método)
- Slot reservado (slot_id, data, hora)
- Ação executada (tipo, resultado)
- Confirmação recebida (resposta, timestamp)

Características:
- Gerado automaticamente pelo sistema
- Não requer ação do paciente
- Imutável após criação
- Sempre tem timestamp
```

### DOCUMENTO (upload/gerado)
```
Exemplos:
- Anamnese preenchida (PDF/JSON)
- Documento de identidade (imagem)
- Carteirinha do convênio (imagem)
- Exames enviados (PDF/imagem)
- SOAP gerado (JSON)
- Receita emitida (PDF)

Características:
- Pode ser enviado pelo paciente (WhatsApp)
- Pode ser gerado pelo sistema (SOAP, receita)
- Tem arquivo associado no Storage
- Pode ser visualizado pela governadora
```

---

## Período de Implantação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  DIAS 1-30: IMPLANTAÇÃO                                                    │
│  ══════════════════════                                                     │
│                                                                             │
│  Taxa de validação: 100%                                                    │
│                                                                             │
│  - TODO trigger gera validação                                              │
│  - Governadora vê TODAS as ações                                            │
│  - Sistema APRENDE com cada validação                                       │
│  - Performance é calculada por fase/trigger                                 │
│                                                                             │
│  Objetivo: Treinar o sistema com feedback real                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIA 31+: MODO ADAPTATIVO                                                  │
│  ════════════════════════                                                   │
│                                                                             │
│  Taxa de validação: Baseada em PERFORMANCE                                 │
│                                                                             │
│  Performance = aprovados / total                                            │
│                                                                             │
│  ┌────────────────┬──────────────────┬─────────────────────────┐           │
│  │ Performance    │ Modo             │ Taxa de Validação       │           │
│  ├────────────────┼──────────────────┼─────────────────────────┤           │
│  │ < 90%          │ Retreino         │ 100% (volta ao início)  │           │
│  │ 90% - 95%      │ Obrigatório      │ 100%                    │           │
│  │ 95% - 98%      │ Amostragem       │ 30%                     │           │
│  │ > 98%          │ Auditoria        │ 5%                      │           │
│  └────────────────┴──────────────────┴─────────────────────────┘           │
│                                                                             │
│  Calculado POR:                                                            │
│  - Fase (0, 1, 2, 3)                                                       │
│  - Tipo de trigger                                                         │
│  - Combinação fase + trigger                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo Completo

```
PACIENTE                SISTEMA                 GOVERNANÇA              RESULTADO
    │                      │                        │                      │
    │  Envia mensagem      │                        │                      │
    │ ────────────────────►│                        │                      │
    │                      │                        │                      │
    │                      │ Processa mensagem      │                      │
    │                      │ Cria evidências (logs) │                      │
    │                      │                        │                      │
    │                      │ ══════════════════════►│                      │
    │                      │ TRIGGER 1: Mensagem    │                      │
    │                      │ + Evidências           │                      │
    │                      │                        │                      │
    │                      │                        │ Valida               │
    │                      │                        │ ✅ Aprova            │
    │                      │                        │────────────────────► │
    │                      │                        │                      │ Performance +
    │                      │                        │                      │
    │  [...agendamento...] │                        │                      │
    │                      │                        │                      │
    │                      │ Cria card              │                      │
    │                      │ Cria evidências        │                      │
    │                      │                        │                      │
    │                      │ ══════════════════════►│                      │
    │                      │ TRIGGER 2: Card criado │                      │
    │                      │ + Evidências           │                      │
    │                      │                        │                      │
    │                      │                        │ Valida               │
    │                      │                        │ ✏️ Corrige           │
    │                      │                        │────────────────────► │
    │                      │                        │                      │ Performance -
    │                      │◄═════════════════════ │                      │
    │                      │ Aplica correção        │                      │
    │                      │                        │                      │
    │  [...pré-consulta...│                        │                      │
    │                      │                        │                      │
    │                      │ Move fase 1 → 2       │                      │
    │                      │ Coleta evidências      │                      │
    │                      │                        │                      │
    │                      │ ══════════════════════►│                      │
    │                      │ TRIGGER 3: Mudança     │                      │
    │                      │ + Checklist            │                      │
    │                      │ + Todas evidências     │                      │
    │                      │                        │                      │
    │                      │                        │ Valida               │
    │                      │                        │ Vê documentos        │
    │                      │                        │ ✅ Aprova            │
    │                      │                        │────────────────────► │
    │                      │                        │                      │ Performance +
    │                      │                        │                      │
```

---

## Tabelas do Banco

### clinica_governanca
```sql
CREATE TABLE clinica_governanca (
    id UUID PRIMARY KEY,
    clinica_id UUID REFERENCES clinicas(id),
    ativado_em TIMESTAMP,           -- Quando ativou governança
    dias_implantacao INTEGER,       -- Dias de implantação (default 30)
    configuracoes JSONB             -- Config específica da clínica
);
```

### governanca_stats
```sql
CREATE TABLE governanca_stats (
    id UUID PRIMARY KEY,
    clinica_id UUID REFERENCES clinicas(id),
    trigger VARCHAR(50),            -- mensagem_whatsapp, card_criado, mudanca_fase
    fase INTEGER,                   -- 0, 1, 2, 3 ou NULL
    total INTEGER DEFAULT 0,
    aprovados INTEGER DEFAULT 0,
    corrigidos INTEGER DEFAULT 0,
    rejeitados INTEGER DEFAULT 0,
    ultima_atualizacao TIMESTAMP
);
```

### validacoes_pendentes
```sql
CREATE TABLE validacoes_pendentes (
    id UUID PRIMARY KEY,
    clinica_id UUID REFERENCES clinicas(id),
    trigger VARCHAR(50),
    resumo TEXT,
    contexto JSONB,                 -- Dados do contexto
    evidencias JSONB,               -- Lista de evidências
    tarefas JSONB,                  -- Checklist com status
    referencia_tipo VARCHAR(50),    -- card, agendamento, etc
    referencia_id UUID,
    prioridade VARCHAR(20),
    status VARCHAR(20),
    expira_em TIMESTAMP,
    validado_por UUID,
    validado_em TIMESTAMP,
    correcoes JSONB,
    observacao TEXT,
    created_at TIMESTAMP
);
```

---

## Resumo

| Componente | Função |
|------------|--------|
| **Kanban** | Backbone - organiza o fluxo e as fases |
| **Tarefas** | Checklist por fase - o que precisa acontecer |
| **Evidências** | Prova de execução - logs e documentos |
| **Governança** | Validação humana - supervisão com taxa adaptativa |
| **Triggers** | Quando validar - 3 momentos chave |
| **Performance** | Métrica - determina taxa de validação |

**Resultado:** Sistema que começa 100% supervisionado e evolui para 95% autônomo conforme prova confiabilidade.
