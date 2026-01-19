# CLINIC OS - DOCUMENTO MESTRE DO SISTEMA

> **Última atualização:** 16 de Janeiro de 2026
> **Versão:** 1.0.0
> **Status:** Em desenvolvimento

---

## ÍNDICE

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Modelo de Negócio](#2-modelo-de-negócio)
3. [Arquitetura Técnica](#3-arquitetura-técnica)
4. [Estrutura de Diretórios](#4-estrutura-de-diretórios)
5. [Fluxos do Sistema](#5-fluxos-do-sistema)
6. [Sprints de Implantação](#6-sprints-de-implantação)
7. [Como Continuar o Desenvolvimento](#7-como-continuar-o-desenvolvimento)

---

# 1. VISÃO GERAL DO SISTEMA

## 1.1 O Que É

Clinic OS é um sistema operacional para clínicas médicas que automatiza o atendimento via WhatsApp com supervisão humana (governança). O sistema aprende com correções e aumenta a precisão ao longo do tempo.

## 1.2 Proposta de Valor

```
ANTES:                              DEPOIS:
═══════                             ════════
Recepcionista faz tudo manualmente  Sistema faz 90% automaticamente
1 recepcionista = 1 clínica         1 recepcionista governa N clínicas
Presa na recepção                   Supervisão pelo celular
Sem rastreabilidade                 Tudo com evidências
```

## 1.3 Diferenciais

| Diferencial | Descrição |
|-------------|-----------|
| **Governança** | Humano no loop sempre - valida ações do sistema |
| **Trust Score** | Sistema ganha confiança conforme acerta |
| **Evidências** | Toda ação tem prova rastreável |
| **Mobile-first** | Interface estilo smartphone (Liquid Glass) |
| **Aprendizado** | Sistema melhora com correções |

## 1.4 Fases do Sistema

```
FASE 1: SIMULADOR (ATUAL)
═════════════════════════
- Chat simulado (desenvolvedor faz papel do paciente)
- Testa toda a lógica sem WhatsApp real
- Valida fluxos end-to-end

FASE 2: WHATSAPP BUSINESS
═════════════════════════
- Conecta Evolution API
- Troca simulador por webhook real
- Mesma lógica, só muda a entrada

FASE 3: PRODUÇÃO
════════════════
- 30 dias de teste grátis (100% validação)
- Mede precisão
- Libera quando atingir 90%+
```

---

# 2. MODELO DE NEGÓCIO

## 2.1 Como Funciona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   VOCÊ VENDE: LICENÇA DE SOFTWARE                                          │
│                                                                             │
│   Cliente paga mensalidade → Recebe o sistema                              │
│                                                                             │
│   Recepcionista DO CLIENTE:                                                │
│   ├── Supervisiona o sistema (governança)                                  │
│   ├── Corrige quando erra                                                  │
│   ├── Assume se sistema falhar                                             │
│   └── Fica LIVRE quando sistema atinge 90%+                                │
│                                                                             │
│   VOCÊ NÃO fornece recepcionista, apenas o software.                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Período de Implantação

```
30 DIAS GRÁTIS:
├── Sistema roda em produção real
├── 100% das ações são validadas
├── Mede precisão continuamente
└── Prova que funciona (ou não)

APÓS 30 DIAS:
├── Atingiu 90%+ → Sistema liberado para uso autônomo
├── Não atingiu → Continua em validação até atingir
└── Cliente paga mensalidade
```

## 2.3 Ganho do Cliente

```
HOJE:                           COM O SISTEMA (90%+):
═════                           ═════════════════════
Recepcionista 100% ocupada      Recepcionista 10% ocupada
Capacidade: X pacientes         Capacidade: 3-5X pacientes
Presa na recepção               Livre para outras tarefas
1 pessoa = 1 unidade            1 pessoa = N unidades
```

---

# 3. ARQUITETURA TÉCNICA

## 3.1 Stack

| Camada | Tecnologia |
|--------|------------|
| **Frontend** | Next.js 14, React, Tailwind CSS, Zustand |
| **Backend** | FastAPI (Python), Supabase (PostgreSQL) |
| **Automação** | Kestra (workflows) |
| **WhatsApp** | Evolution API (futuro) |
| **IA Chat** | Groq API (LLaMA 3.1 70B) - GRÁTIS |
| **IA Complexa** | Claude API (SOAP, documentos) - PAGO |

## 3.2 Estratégia de LLMs (Inteligência Artificial)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ESTRATÉGIA DE LLMs                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GROQ API (GRÁTIS)                      CLAUDE API (PAGO)                  │
│  ════════════════                       ═══════════════                    │
│  Modelo: LLaMA 3.1 70B                  Modelo: Claude Sonnet              │
│  Custo: $0                              Custo: ~$0.003/request             │
│  Limite: 14,400 req/dia                 Limite: Por crédito                │
│  Velocidade: ~500 tok/s                 Velocidade: ~100 tok/s             │
│                                                                             │
│  USA PARA:                              USA PARA:                          │
│  ├── Interpretar mensagens WhatsApp     ├── Gerar SOAP (prontuário)        │
│  ├── Classificar intenção               ├── Análise de documentos          │
│  ├── Extrair dados (data, hora, nome)   ├── Raciocínio médico complexo     │
│  ├── Gerar respostas ao paciente        └── Tarefas que exigem qualidade   │
│  └── Qualquer tarefa de chat                                               │
│                                                                             │
│  REGRA: Se é chat/WhatsApp → Groq. Se é médico/complexo → Claude.          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

FLUXO DE DECISÃO:
                    ┌─────────────────┐
                    │  Tarefa de IA   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  É chat/WhatsApp │
                    │  ou classificação?│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ SIM                         │ NÃO
              ▼                             ▼
     ┌────────────────┐           ┌────────────────┐
     │   GROQ API     │           │  CLAUDE API    │
     │   (GRÁTIS)     │           │  (PAGO)        │
     │                │           │                │
     │ LLaMA 3.1 70B  │           │ Claude Sonnet  │
     └────────────────┘           └────────────────┘
```

**Por que essa divisão?**

| Critério | Groq | Claude |
|----------|------|--------|
| Custo | GRÁTIS | ~$3/1000 requests |
| Qualidade para chat | ✅ Suficiente | ⚠️ Overkill |
| Qualidade para SOAP | ❌ Insuficiente | ✅ Excelente |
| Velocidade | ⚡ 500 tok/s | 🐢 100 tok/s |
| Limite diário | 14,400 | Por crédito |

**Configuração necessária (.env):**
```env
# Groq (chat/whatsapp) - GRÁTIS
GROQ_API_KEY=gsk_xxx

# Claude (SOAP/documentos) - PAGO, usar com moderação
ANTHROPIC_API_KEY=sk-ant-xxx
```

## 3.2 Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLINIC OS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  FRONTEND   │    │   BACKEND   │    │  DATABASE   │                     │
│  │  (Next.js)  │◄──►│  (FastAPI)  │◄──►│ (Supabase)  │                     │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                     │
│                            │                                                │
│                            ▼                                                │
│                    ┌───────────────┐                                        │
│                    │   KESTRA      │                                        │
│                    │  (Workflows)  │                                        │
│                    └───────┬───────┘                                        │
│                            │                                                │
│         ┌──────────────────┼──────────────────┐                            │
│         ▼                  ▼                  ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  SIMULADOR  │    │  WHATSAPP   │    │  CLAUDE AI  │                     │
│  │  (dev/test) │    │ (Evolution) │    │(interpretar)│                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.3 Fluxo de Dados

```
ENTRADA (WhatsApp ou Simulador)
          │
          ▼
┌─────────────────────┐
│  1. RECEBE MENSAGEM │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. INTERPRETA (IA) │  ← Claude API analisa intenção
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. EXECUTA AÇÃO    │  ← Agenda, confirma, check-in, etc.
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. REGISTRA        │  ← Evidência + Validação pendente
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  5. RESPONDE        │  ← Mensagem de volta ao paciente
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  6. GOVERNANÇA      │  ← Recepcionista valida
└─────────────────────┘
```

---

# 4. ESTRUTURA DE DIRETÓRIOS

## 4.1 Visão Geral

```
SISTEMA GESTAO CONSULTORIOS MEDICOS/
│
├── backend/                    # API FastAPI
│   └── app/                    # Código principal
│
├── frontend/                   # Interface Next.js
│   └── src/                    # Código principal
│
├── workflows/                  # Automações Kestra
│
├── docs/                       # Documentação
│
└── infra/                      # Docker, deploy (futuro)
```

## 4.2 Backend Detalhado

```
backend/app/
│
├── main.py                     # Ponto de entrada da API
├── requirements.txt            # Dependências Python
├── README.md                   # Documentação do backend
├── SECURITY.md                 # Notas de segurança
│
├── core/                       # Núcleo do sistema
│   ├── __init__.py
│   ├── config.py              # Configurações (env vars)
│   ├── database.py            # Conexão Supabase
│   ├── security.py            # JWT, hash de senhas
│   ├── exceptions.py          # Exceções customizadas
│   ├── schemas.py             # Schemas base
│   └── utils.py               # Utilitários gerais
│
├── auth/                       # Autenticação
│   ├── __init__.py
│   ├── router.py              # POST /auth/login, GET /auth/me
│   ├── service.py             # Lógica de login, JWT
│   └── schemas.py             # LoginRequest, TokenResponse
│
├── clinicas/                   # Gestão de clínicas
│   ├── __init__.py
│   ├── router.py              # CRUD /clinicas
│   ├── service.py             # Lógica de clínicas
│   └── schemas.py             # ClinicaCreate, ClinicaResponse
│
├── pacientes/                  # Gestão de pacientes
│   ├── __init__.py
│   ├── router.py              # CRUD /pacientes
│   ├── service.py             # Lógica de pacientes
│   └── schemas.py             # PacienteCreate, PacienteResponse
│
├── agenda/                     # Agendamentos
│   ├── __init__.py
│   ├── router.py              # CRUD /agenda
│   ├── service.py             # Lógica de agendamentos
│   │   └── Principais funções:
│   │       - criar_agendamento()
│   │       - listar_agendamentos()
│   │       - cancelar_agendamento()
│   │       - confirmar_agendamento()
│   └── schemas.py             # AgendamentoCreate, etc.
│
├── kanban/                     # Quadro Kanban
│   ├── __init__.py
│   ├── router.py              # /kanban/cards, /kanban/fases
│   ├── service.py             # Lógica do Kanban
│   │   └── Principais funções:
│   │       - criar_card()
│   │       - mover_card()
│   │       - atualizar_checklist()
│   │       - get_cards_por_fase()
│   └── schemas.py             # CardCreate, FaseEnum, etc.
│
├── cards/                      # Gestão detalhada de cards
│   ├── __init__.py
│   ├── router.py              # CRUD /cards
│   ├── service.py             # Lógica de cards
│   └── schemas.py             # CardDetail, ChecklistItem
│
├── evidencias/                 # Registro de evidências
│   ├── __init__.py
│   ├── router.py              # POST /evidencias
│   ├── service.py             # Lógica de evidências
│   │   └── Principais funções:
│   │       - registrar_evidencia()
│   │       - listar_evidencias()
│   │       - validar_evidencia()
│   └── schemas.py             # EvidenciaCreate, TipoEvidencia
│
├── governanca/                 # Sistema de governança
│   ├── __init__.py
│   ├── router.py              # /governanca/validacoes, /governanca/dashboard
│   ├── service.py             # Lógica principal de governança
│   │   └── Principais funções:
│   │       - trigger_mensagem_whatsapp()
│   │       - trigger_card_criado()
│   │       - trigger_mudanca_fase()
│   │       - processar_validacao()
│   │       - get_dashboard()
│   │       - calcular_trust_score()
│   ├── verificacao_router.py  # Endpoints de verificação
│   ├── verificacao_service.py # Lógica de verificação
│   ├── GOVERNANCA.md          # Documentação detalhada
│   └── README_EVIDENCIAS.md   # Doc de evidências
│
├── usuarios/                   # ✅ CRIADO - Gestão de Usuários
│   ├── __init__.py            # Exports e documentação
│   ├── router.py              # CRUD /usuarios + /usuarios/me
│   ├── service.py             # Lógica de negócio
│   │   └── Principais funções:
│   │       - list() - Lista usuários da clínica
│   │       - get() - Detalhes do usuário
│   │       - create() - Cria no Auth + tabela
│   │       - update() - Atualiza dados
│   │       - delete() - Soft delete (desativa)
│   │       - reativar() - Reativa usuário
│   └── schemas.py             # UsuarioCreate, UsuarioResponse, etc
│
├── chat/                       # ✅ CRIADO - Chat/Simulador
│   ├── __init__.py            # Exports e documentação
│   ├── router.py              # POST /chat/mensagem, GET /chat/conversas
│   ├── service.py             # Processa mensagens, executa ações
│   ├── interpreter.py         # Groq API (LLaMA 3.1) interpreta intenção
│   ├── llm_providers.py       # Abstração Groq/DeepSeek/OpenAI
│   └── schemas.py             # MensagemIn, MensagemOut, Interpretacao
│
├── whatsapp/                   # 🚧 FUTURO - Integração WhatsApp
│   ├── __init__.py
│   ├── evolution.py           # Conector Evolution API
│   └── webhook.py             # Recebe mensagens
│
├── migrations/                 # Scripts SQL
│   ├── 003_governanca.sql     # Tabelas de governança
│   └── 004_verificacao_evidencias.sql
│
└── frontend/                   # Componentes React legados
    └── GovernancaDashboard.jsx
```

### ⚠️ NOTA: Configurações de Desenvolvimento vs Produção

**Módulo `chat/router.py` - Decisão Temporária:**

Durante o desenvolvimento, os endpoints de chat permitem acesso sem autenticação
usando `get_current_user_optional` e um `DEFAULT_CLINICA_ID`.

| Configuração | Desenvolvimento | Produção |
|--------------|-----------------|----------|
| Auth obrigatório | ❌ Opcional | ✅ Obrigatório |
| DEFAULT_CLINICA_ID | Usado como fallback | ❌ Remover |
| get_current_user_optional | ✅ Usado | Trocar por `get_current_user` |

**Ação necessária para produção:**
```python
# TROCAR ISSO:
current_user: Optional[dict] = Depends(get_current_user_optional)
clinica_id = current_user.get("clinica_id") if current_user else DEFAULT_CLINICA_ID

# POR ISSO:
current_user: dict = Depends(get_current_user)
clinica_id = current_user.get("clinica_id")
```

## 4.3 Frontend Detalhado

```
frontend/
│
├── package.json               # Dependências npm
├── next.config.js             # Configuração Next.js
├── tailwind.config.js         # Configuração Tailwind
├── tsconfig.json              # Configuração TypeScript
├── postcss.config.js          # PostCSS
├── .env.example               # Variáveis de ambiente
├── README.md                  # Documentação
│
├── public/                    # Assets estáticos
│   └── (favicon, imagens)
│
└── src/
    │
    ├── app/                   # Next.js App Router
    │   │
    │   ├── layout.tsx         # Layout raiz (html, body, fonts)
    │   │
    │   ├── page.tsx           # PÁGINA DE LOGIN
    │   │   └── Funcionalidades:
    │   │       - Form de login (email, senha, clínica)
    │   │       - Animações gradient background
    │   │       - Glass effect
    │   │       - Redirect para /dashboard
    │   │
    │   └── dashboard/         # ÁREA LOGADA
    │       │
    │       ├── layout.tsx     # Layout do dashboard
    │       │   └── Funcionalidades:
    │       │       - Dock inferior (apps)
    │       │       - Wallpaper personalizável
    │       │       - Settings panel
    │       │       - Verifica autenticação
    │       │
    │       ├── page.tsx       # HOME DO DASHBOARD
    │       │   └── Funcionalidades:
    │       │       - Stats (consultas, precisão, pendentes)
    │       │       - Próximas consultas
    │       │       - Últimas mensagens
    │       │       - Grid de módulos (apps)
    │       │       - Resumo governança
    │       │
    │       ├── kanban/
    │       │   └── page.tsx   # MÓDULO KANBAN (placeholder)
    │       │
    │       ├── governanca/
    │       │   └── page.tsx   # MÓDULO GOVERNANÇA
    │       │       └── Funcionalidades:
    │       │           - Progress bar (dia X de 30)
    │       │           - Stats (pendentes, aprovadas, etc)
    │       │           - Lista de validações
    │       │           - Botões aprovar/corrigir/rejeitar
    │       │
    │       ├── agenda/
    │       │   └── page.tsx   # MÓDULO AGENDA (placeholder)
    │       │
    │       ├── chat/
    │       │   └── page.tsx   # ✅ SIMULADOR IMPLEMENTADO
    │       │       └── Visão dupla, interpretação LLM, ações, governança
    │       │
    │       ├── pacientes/
    │       │   └── page.tsx   # MÓDULO PACIENTES (placeholder)
    │       │
    │       └── (outros módulos: soap, prontuario, financeiro, config, relatorios)
    │
    ├── components/            # Componentes reutilizáveis
    │   ├── ui/               # Componentes base (Button, Input, etc)
    │   ├── modules/          # Componentes de módulos
    │   └── layout/           # Componentes de layout
    │
    ├── lib/                   # Utilitários
    │   │
    │   ├── store.ts          # ZUSTAND STORE
    │   │   └── Estado global:
    │   │       - isDark (tema)
    │   │       - wallpaper (fundo)
    │   │       - user (usuário logado)
    │   │       - showSettings
    │   │       - activeModule
    │   │
    │   ├── api.ts            # CLIENTE API
    │   │   └── Métodos:
    │   │       - login()
    │   │       - getKanbanCards()
    │   │       - getValidacoesPendentes()
    │   │       - processarValidacao()
    │   │       - etc.
    │   │
    │   └── utils.ts          # HELPERS
    │       └── Funções:
    │           - cn() - merge de classes
    │           - getGlassStyles() - estilos glass
    │           - getTextStyles() - cores de texto
    │           - formatDate(), formatTime()
    │           - getGreeting()
    │           - statusColors
    │
    ├── hooks/                 # React hooks customizados
    │
    └── styles/
        └── globals.css        # Tailwind + estilos globais
            └── Classes customizadas:
                - .glass, .glass-strong, .glass-solid
                - .text-gradient
                - .glow-violet, .glow-blue
                - .animate-slide-in, .animate-fade-in
```

## 4.4 Workflows (Kestra)

```
workflows/
│
├── 00-agendamento-whatsapp.yml    # Fluxo de novo agendamento
├── 01-confirmacao.yml             # Fluxo de confirmação
├── 02-checkin.yml                 # Fluxo de check-in
├── 03-pos-consulta.yml            # Fluxo pós-consulta
└── (outros workflows)
```

---

# 5. FLUXOS DO SISTEMA

## 5.1 Fluxo de Agendamento (Simulador)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SIMULADOR DE CHAT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Desenvolvedor digita como paciente]                                       │
│  "Oi, quero marcar uma consulta para segunda às 14h"                       │
│                                                                             │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────┐                       │
│  │  POST /chat/mensagem                            │                       │
│  │  {                                              │                       │
│  │    "telefone": "11999887766",                   │                       │
│  │    "mensagem": "Oi, quero marcar...",           │                       │
│  │    "simulado": true                             │                       │
│  │  }                                              │                       │
│  └─────────────────────────────────────────────────┘                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────┐                       │
│  │  chat/interpreter.py                            │                       │
│  │                                                 │                       │
│  │  GROQ API (LLaMA 3.1 70B) analisa:             │                       │
│  │  - Intenção: AGENDAR                           │                       │
│  │  - Data: segunda-feira                          │                       │
│  │  - Hora: 14:00                                  │                       │
│  │  - Confiança: 94%                               │                       │
│  │                                                 │                       │
│  │  Custo: GRÁTIS                                  │                       │
│  └─────────────────────────────────────────────────┘                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────┐                       │
│  │  chat/service.py                                │                       │
│  │                                                 │                       │
│  │  1. Busca/cria paciente pelo telefone           │                       │
│  │  2. Chama agenda/service.criar_agendamento()    │                       │
│  │  3. Chama kanban/service.criar_card()           │                       │
│  │  4. Chama governanca/service.trigger_whatsapp() │                       │
│  │  5. Gera resposta para o paciente               │                       │
│  └─────────────────────────────────────────────────┘                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────┐                       │
│  │  RESULTADO                                      │                       │
│  │                                                 │                       │
│  │  ✓ Paciente criado/encontrado                   │                       │
│  │  ✓ Agendamento criado                           │                       │
│  │  ✓ Card criado no Kanban (fase 0)               │                       │
│  │  ✓ Validação pendente na Governança             │                       │
│  │  ✓ Resposta: "Confirmado! Segunda 14h..."       │                       │
│  └─────────────────────────────────────────────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Fluxo de Governança

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DASHBOARD GOVERNANÇA                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Validação Pendente:                                                        │
│  ┌─────────────────────────────────────────────────┐                       │
│  │  💬 WhatsApp                                    │                       │
│  │  "quero marcar consulta segunda às 14h"         │                       │
│  │                                                 │                       │
│  │  Interpretação: AGENDAR (94%)                   │                       │
│  │  Ação tomada: Criou agendamento                 │                       │
│  │                                                 │                       │
│  │  [✓ Aprovar]  [✏️ Corrigir]  [✗ Rejeitar]      │                       │
│  └─────────────────────────────────────────────────┘                       │
│                                                                             │
│         │                                                                   │
│         ▼                                                                   │
│                                                                             │
│  SE APROVAR:                    SE CORRIGIR:           SE REJEITAR:        │
│  ├── Trust score +2             ├── Trust score -5     ├── Trust score -15 │
│  └── Próxima validação          ├── Aplica correção    ├── Reverte ação    │
│                                 └── Sistema aprende    └── Sistema aprende │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.3 Jornada do Paciente no Kanban

```
FASE 0: AGENDADO          FASE 1: PRÉ-CONSULTA      FASE 2: DIA           FASE 3: PÓS
════════════════          ════════════════════      ═══════════           ═══════════

┌─────────────┐           ┌─────────────┐           ┌─────────────┐       ┌─────────────┐
│ Maria Silva │           │             │           │             │       │             │
│ Seg 14:00   │──────────►│             │──────────►│             │──────►│             │
│             │           │             │           │             │       │             │
│ □ Confirmar │           │ □ Anamnese  │           │ □ Check-in  │       │ □ SOAP      │
│ □ Check-in  │           │ □ Exames    │           │ □ Consulta  │       │ □ Aprovação │
└─────────────┘           └─────────────┘           └─────────────┘       └─────────────┘

TRIGGERS DE MOVIMENTO:
- Fase 0 → 1: Todas tarefas da fase 0 completas
- Fase 1 → 2: Dia da consulta chegou + pré-consulta ok
- Fase 2 → 3: Consulta realizada
- Fase 3 → FIM: SOAP aprovado pelo médico
```

---

# 6. SPRINTS DE IMPLANTAÇÃO

## 6.1 Sprints Finalizados

### ✅ SPRINT 0: Fundação do Backend
**Período:** Janeiro 2026 (primeiras sessões)
**Status:** ✅ CONCLUÍDO

**O que foi feito:**
- [x] Estrutura do projeto FastAPI
- [x] Módulo `core/` (database, config, security)
- [x] Módulo `auth/` (login, JWT)
- [x] Módulo `clinicas/` (CRUD)
- [x] Módulo `pacientes/` (CRUD)
- [x] Módulo `agenda/` (agendamentos)
- [x] Conexão com Supabase

**Arquivos criados:**
- `app/main.py`
- `app/core/*`
- `app/auth/*`
- `app/clinicas/*`
- `app/pacientes/*`
- `app/agenda/*`

---

### ✅ SPRINT 1: Kanban e Cards
**Período:** Janeiro 2026
**Status:** ✅ CONCLUÍDO

**O que foi feito:**
- [x] Módulo `kanban/` com fases
- [x] Módulo `cards/` com checklist
- [x] Lógica de movimento entre fases
- [x] Validação de checklist antes de mover

**Arquivos criados:**
- `app/kanban/*`
- `app/cards/*`

---

### ✅ SPRINT 2: Governança e Evidências
**Período:** Janeiro 2026
**Status:** ✅ CONCLUÍDO

**O que foi feito:**
- [x] Módulo `evidencias/` (registro de provas)
- [x] Módulo `governanca/` completo
- [x] Sistema de Trust Score
- [x] 3 Triggers (WhatsApp, Card Criado, Mudança Fase)
- [x] Dashboard de governança
- [x] Período de implantação (30 dias)
- [x] Migrations SQL

**Arquivos criados:**
- `app/evidencias/*`
- `app/governanca/*`
- `app/migrations/003_governanca.sql`
- `app/migrations/004_verificacao_evidencias.sql`

---

### ✅ SPRINT 3: Frontend Base
**Período:** 16 de Janeiro de 2026
**Status:** ✅ CONCLUÍDO

**O que foi feito:**
- [x] Projeto Next.js configurado
- [x] Design System Liquid Glass
- [x] Página de Login
- [x] Dashboard Home
- [x] Layout com Dock
- [x] Sistema de wallpapers
- [x] Dark mode
- [x] Zustand store
- [x] Cliente API preparado
- [x] Módulo Governança (básico)
- [x] Placeholders para outros módulos

**Arquivos criados:**
- `frontend/` (estrutura completa)
- `frontend/src/app/page.tsx` (login)
- `frontend/src/app/dashboard/*`
- `frontend/src/lib/*`
- `frontend/src/styles/globals.css`

---

## 6.2 Sprints em Andamento

### 🔄 SPRINT 4: Chat Simulador + Usuários
**Status:** 🔄 EM FINALIZAÇÃO (95%)
**Período:** 16 de Janeiro de 2026
**Prioridade:** ALTA

**Backend Chat:** ✅ CONCLUÍDO
- [x] Criar `app/chat/__init__.py`
- [x] Criar `app/chat/schemas.py`
  - MensagemIn (telefone, mensagem, simulado)
  - MensagemOut (resposta, interpretacao, acoes)
  - ConversaResponse
- [x] Criar `app/chat/llm_providers.py` - **ABSTRAÇÃO PARA TROCAR LLM**
  - Suporta: Groq (grátis), DeepSeek (barato), OpenAI (premium)
  - Trocar provedor = 1 variável de ambiente
  - **IMPORTANTE:** Usar modelo `llama-3.3-70b-versatile` (não 3.1!)
- [x] Criar `app/chat/interpreter.py`
  - interpretar_mensagem() - USA GROQ API (GRÁTIS)
  - Modelo: LLaMA 3.3 70B
  - Fallback local se LLM falhar
- [x] Criar `app/chat/service.py`
  - processar_mensagem()
  - buscar_ou_criar_paciente()
  - executar_acao() - AGENDAR, CONFIRMAR, CANCELAR, CHECK_IN, REMARCAR
  - gerar_resposta()
  - criar_validacao_governanca()
- [x] Criar `app/chat/router.py`
  - POST /chat/mensagem
  - GET /chat/conversas
  - GET /chat/conversas/{telefone}
  - GET /chat/config
  - POST /chat/teste-interpretacao
- [x] Registrar router em main.py
- [x] Migration 005_chat_conversas.sql
- [x] Atualizar .env.example com GROQ_API_KEY

**Backend Usuários:** ✅ CONCLUÍDO
- [x] Criar `app/usuarios/__init__.py`
- [x] Criar `app/usuarios/schemas.py`
  - UsuarioCreate, UsuarioUpdate, UsuarioResponse
  - TipoUsuario enum (admin, medico, recepcionista, etc)
- [x] Criar `app/usuarios/service.py`
  - CRUD completo com integração Supabase Auth
  - Soft delete (desativar/reativar)
- [x] Criar `app/usuarios/router.py`
  - GET /usuarios (listar)
  - GET /usuarios/me (próprio usuário)
  - GET /usuarios/{id} (detalhes)
  - POST /usuarios (criar)
  - PATCH /usuarios/{id} (atualizar)
  - DELETE /usuarios/{id} (desativar)
  - POST /usuarios/{id}/reativar
- [x] Registrar router em main.py

**Correções de Integração:** ✅ CONCLUÍDO
- [x] Fix: `get_current_user` como FastAPI dependency
- [x] Fix: `get_supabase_client` alias no database.py
- [x] Fix: Variáveis LLM no config.py (pydantic_settings)
- [x] Fix: Modelo Groq `llama-3.1` → `llama-3.3-70b-versatile`
- [x] Fix: Mapeamento de colunas (ver seção abaixo)

**Frontend:** ✅ CONCLUÍDO
- [x] Criar tela de simulador (`/dashboard/chat`)
  - Visão dupla: paciente (esquerda) + sistema (direita)
  - Seletor de pacientes simulados
  - Criar novo paciente
  - Chat com mensagens em tempo real
  - Sugestões de mensagens rápidas
  - Exibição de interpretação do LLM
  - Exibição de ações executadas
  - Status de governança
  - Link para página de governança
  - Indicador de provedor LLM ativo
- [x] Atualizar api.ts com endpoints do chat
  - enviarMensagemSimulador()
  - getConversas()
  - getConversa()
  - testarInterpretacao()
  - getLLMConfig()
- [x] Types para ChatResponse, ConversaDetalhe, etc

**Testes Realizados:** ✅
- [x] Groq API funcionando (`/chat/config` retorna ok)
- [x] Interpretação funcionando (SAUDACAO 100%, AGENDAR 95%)
- [x] Resposta do LLM gerada corretamente
- [x] Dados extraídos (data, hora, nome)

**Pendente:** ⏳
- [ ] Testar criação de agendamento (após fix de colunas)
- [ ] Verificar card aparece no Kanban
- [ ] Verificar validação aparece na Governança

#### Mapeamento de Colunas (Schema Real vs Código)

Durante a integração, foram corrigidas diferenças entre o código e o schema real do banco:

| Tabela | Código Original | Schema Real |
|--------|-----------------|-------------|
| pacientes | `criado_em` | `created_at` |
| pacientes | `origem` | `como_conheceu` |
| agendamentos | `hora` | `hora_inicio` |
| agendamentos | `como_conheceu` | (não existe) |
| cards | `cards_kanban` | `cards` |
| cards | `titulo` | `paciente_nome` + `data_agendamento` + `hora_agendamento` |

---

## 6.3 Próximos Passos Imediatos

**Para finalizar Sprint 4:**
1. ✅ Extrair `chat_service_fix3.zip` (correção de colunas)
2. ⏳ Reiniciar backend e testar agendamento
3. ⏳ Verificar se card aparece no Kanban
4. ⏳ Verificar se evidência aparece na Governança
5. ⏳ Se der erro de coluna em `evidencias`, mapear também

**Se tudo funcionar:**
- Sprint 4 pode ser marcado como ✅ CONCLUÍDO
- Próximo: Sprint 5 (Kanban Frontend) ou Sprint 7 (WhatsApp Real)

---

## 6.4 Sprints Pendentes

### 📋 SPRINT 5: Kanban Frontend
**Status:** ⏳ PENDENTE
**Prioridade:** ALTA

**O que precisa ser feito:**
- [ ] Implementar quadro Kanban visual
- [ ] Drag & drop entre colunas
- [ ] Card detail modal
- [ ] Checklist interativo
- [ ] Filtros (médico, data, status)
- [ ] Conectar ao backend

---

### 📋 SPRINT 6: Agenda Frontend
**Status:** ⏳ PENDENTE
**Prioridade:** MÉDIA

**O que precisa ser feito:**
- [ ] Calendário visual
- [ ] Criar novo agendamento
- [ ] Visualização por dia/semana/mês
- [ ] Slots de horário
- [ ] Conectar ao backend

---

### 📋 SPRINT 7: WhatsApp Real
**Status:** ⏳ PENDENTE
**Prioridade:** MÉDIA (após simulador funcionar)

**O que precisa ser feito:**
- [ ] Criar `app/whatsapp/evolution.py`
  - Conector Evolution API
  - enviar_mensagem()
  - receber_mensagem()
- [ ] Criar `app/whatsapp/webhook.py`
  - POST /webhook/whatsapp
  - Processa mensagens reais
- [ ] Configurar Evolution API
- [ ] Testar com número real
- [ ] Documentar configuração

---

### 📋 SPRINT 8: SOAP e Transcrição
**Status:** ⏳ PENDENTE
**Prioridade:** BAIXA

**O que precisa ser feito:**
- [ ] Gravação de áudio
- [ ] Transcrição via Whisper
- [ ] Geração de SOAP via Claude
- [ ] Tela de revisão do médico
- [ ] Assinatura digital

---

### 📋 SPRINT 9: PWA e Mobile
**Status:** ⏳ PENDENTE
**Prioridade:** BAIXA

**O que precisa ser feito:**
- [ ] Configurar PWA (manifest, service worker)
- [ ] Push notifications
- [ ] Funcionamento offline
- [ ] Otimizar para mobile

---

### 📋 SPRINT 10: Deploy e Produção
**Status:** ⏳ PENDENTE
**Prioridade:** BAIXA (após tudo funcionar)

**O que precisa ser feito:**
- [ ] Docker compose completo
- [ ] CI/CD pipeline
- [ ] Monitoramento
- [ ] Backup automático
- [ ] Documentação de deploy

---

# 7. COMO CONTINUAR O DESENVOLVIMENTO

## 7.1 Se Iniciar Nova Sessão

1. **Compartilhe este documento** com a nova sessão
2. **Informe o sprint atual** (ex: "Estamos no Sprint 4 - Chat Simulador")
3. **Descreva o que já foi feito** do sprint atual
4. **Peça para continuar** de onde parou

## 7.2 Comandos Úteis

```bash
# Backend
cd backend
pip install -r app/requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Ver estrutura
tree -L 3 --dirsfirst
```

## 7.3 URLs Importantes

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Supabase | (configurar em .env) |

## 7.4 Arquivos de Configuração

**Backend (.env):**
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
JWT_SECRET=xxx

# Groq API (chat/whatsapp) - GRÁTIS
GROQ_API_KEY=gsk_xxx

# Claude API (SOAP/documentos) - PAGO, usar só quando necessário
ANTHROPIC_API_KEY=sk-ant-xxx
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8080/v1
NEXT_PUBLIC_APP_NAME=Clinic OS
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**IMPORTANTE:** A porta do backend é `8080`, não `8000`. E o path é `/v1`, não `/api/v1`.

---

# 8. DADOS REAIS DO SISTEMA (DESENVOLVIMENTO)

## 8.1 Clínica Cadastrada

| Campo | Valor |
|-------|-------|
| **ID** | `a9a6f406-3b46-4dab-b810-6c25d62f743b` |
| **Nome** | DAG Serviços Médicos |
| **CNPJ** | 07.175.153/0001-19 |
| **WhatsApp** | 5521999967727 |
| **Endereço** | Rua Conde de Bonfim, 297 - Tijuca, RJ |
| **CEP** | 20520-053 |
| **Fuso** | America/Sao_Paulo |
| **Plano** | basic |

## 8.2 Usuário Admin

| Campo | Valor |
|-------|-------|
| **ID** | `be548ecb-a729-4b19-b771-26ce2ad894f2` |
| **Nome** | Tulio Carvalho |
| **Email** | tuliocarvalho31121981@gmail.com |
| **Tipo** | admin |
| **Perfil** | Administrador (CLEX total) |

## 8.3 Perfis Cadastrados

| Perfil | Permissões | Sistema |
|--------|------------|---------|
| **Administrador** | CLEX em tudo | Sim |
| **Médico** | Prontuário CLEX, Agenda CLE | Sim |
| **Recepcionista** | Agenda CLEX, Pacientes CLE | Sim |
| **Financeiro** | Financeiro CLEX, Estoque CLEX | Sim |

**Legenda CLEX:** C=Criar, L=Ler, E=Editar, X=Excluir

## 8.4 Configuração .env para Desenvolvimento

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx

# JWT
JWT_SECRET=xxx

# Groq (chat/whatsapp) - GRÁTIS
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
LLM_PROVIDER=groq

# Clinica padrão para testes sem auth
DEFAULT_CLINICA_ID=a9a6f406-3b46-4dab-b810-6c25d62f743b
```

---

# CHANGELOG

| Data | Versão | Alterações |
|------|--------|------------|
| 16/01/2026 | 1.2.0 | Sprint 4 em finalização: Chat funcionando com Groq, correções de schema, módulo usuarios |
| 16/01/2026 | 1.1.0 | Adicionado módulo usuarios/, dados reais, notas dev vs prod |
| 16/01/2026 | 1.0.0 | Documento inicial criado |

---

# LIÇÕES APRENDIDAS

## Integração Backend ↔ Banco

1. **Sempre verificar schema real antes de criar código**
   - O código foi escrito esperando colunas que não existem
   - Usar: `SELECT column_name FROM information_schema.columns WHERE table_name = 'xxx'`

2. **pydantic_settings não carrega variáveis automaticamente**
   - Variáveis precisam estar definidas na classe Settings
   - `os.getenv()` não funciona para .env, só para variáveis do sistema

3. **Modelos de LLM mudam**
   - Groq descontinuou `llama-3.1-70b-versatile`
   - Usar `llama-3.3-70b-versatile` (atual)

4. **Portas e paths importam**
   - Backend: `http://localhost:8080/v1` (não 8000, não /api/v1)
   - Frontend: `http://localhost:3000`

---

**FIM DO DOCUMENTO**
