# CLINIC OS (DOCFLOW) - CLAUDE.md

> **Sistema Operacional para Clínicas Médicas**
> **Versão:** 1.4.0 | **Sprint Atual:** 6 (Cockpit do Médico)
> **Última atualização:** Janeiro 2026

---

## VISÃO GERAL

### O que é
Sistema SaaS de gestão para consultórios médicos de cardiologia que **automatiza o atendimento via WhatsApp com supervisão humana (governança)**. O sistema aprende com correções e aumenta a precisão ao longo do tempo.

### Problema que resolve
| ANTES | DEPOIS |
|-------|--------|
| Recepcionista faz tudo manualmente | Sistema faz 90% automaticamente |
| 1 recepcionista = 1 clínica | 1 recepcionista governa N clínicas |
| Esquecimentos e falhas humanas | Automação com supervisão inteligente |

### Diferenciais
- **Governança**: Humano no loop sempre - valida ações do sistema
- **Trust Score**: Sistema ganha confiança conforme acerta
- **Evidências**: Toda ação tem prova rastreável
- **Mobile-first**: Interface estilo smartphone (Liquid Glass)
- **Aprendizado**: Sistema melhora com correções

---

## STACK TÉCNICA

### Backend
| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.12 | Linguagem |
| FastAPI | 0.109 | Framework web |
| Pydantic | 2.5 | Validação de dados |
| LangGraph | - | Agente de conversa (estado persistente) |

### Frontend
| Tecnologia | Função |
|------------|--------|
| Next.js | 14 | Framework React |
| Tailwind CSS | Estilização |
| Zustand | Estado global |
| dnd-kit | Drag & drop (Kanban) |

### Database & Infra
| Tecnologia | Função |
|------------|--------|
| Supabase | PostgreSQL + Auth + Storage |
| Kestra | Orquestração de workflows assíncronos |

### Integrações IA
| Serviço | Uso | Custo |
|---------|-----|-------|
| **Groq** (LLaMA 3.1 70B) | Chat/WhatsApp | GRÁTIS |
| **OpenRouter** (Claude Sonnet) | Chat avançado | PAGO |
| **Whisper** (OpenAI) | Transcrição de consultas | PAGO |
| **Claude** (Anthropic) | SOAP, análise de documentos | PAGO |
| **Google Vision** | OCR de carteirinhas | PAGO |

---

## ARQUITETURA

### Estrutura de Pastas

```
📁 SISTEMA GESTAO CONSULTORIOS MEDICOS/
│
├── 📁 backend/                    # API FastAPI
│   ├── app/
│   │   ├── main.py               # Entry point da aplicação
│   │   ├── core/                 # Núcleo compartilhado
│   │   │   ├── config.py         # Configurações (env vars)
│   │   │   ├── database.py       # Cliente Supabase
│   │   │   ├── security.py       # Auth e permissões
│   │   │   ├── exceptions.py     # Exceções customizadas
│   │   │   └── schemas.py        # Schemas base
│   │   │
│   │   ├── auth/                 # Autenticação
│   │   ├── clinicas/             # Multi-tenant
│   │   ├── usuarios/             # Funcionários
│   │   ├── pacientes/            # Clientes da clínica
│   │   ├── agenda/               # Agendamentos
│   │   ├── cards/                # Kanban básico
│   │   ├── kanban/               # Kanban avançado (fases)
│   │   ├── governanca/           # Validação humana
│   │   ├── evidencias/           # Documentos comprobatórios
│   │   │
│   │   ├── chat_langgraph/       # 🆕 Agente LangGraph
│   │   │   ├── agent.py          # Classe do agente
│   │   │   ├── graph.py          # Grafo de estados
│   │   │   ├── tools.py          # Ferramentas disponíveis
│   │   │   ├── states.py         # Definição de estados
│   │   │   ├── nodes.py          # Nós do grafo
│   │   │   ├── llm_providers.py  # Conectores LLM
│   │   │   └── router.py         # Endpoints /chat
│   │   │
│   │   ├── integracoes/          # Clientes externos
│   │   │   ├── whatsapp/         # Evolution API
│   │   │   ├── groq/             # LLM gratuito
│   │   │   └── openrouter/       # LLM alternativo
│   │   │
│   │   └── webhooks/             # Callbacks externos
│   │
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📁 frontend/                   # Next.js 14
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Landing
│   │   │   ├── layout.tsx        # Layout global
│   │   │   └── dashboard/
│   │   │       ├── page.tsx      # Dashboard principal
│   │   │       ├── kanban/       # Kanban visual
│   │   │       ├── cards/        # Gestão de cards
│   │   │       ├── pacientes/    # Lista pacientes
│   │   │       ├── agenda/       # Calendário
│   │   │       ├── governanca/   # Validação
│   │   │       └── chat/         # Simulador de chat
│   │   │
│   │   ├── components/
│   │   │   └── cards/
│   │   │       └── CardModal.tsx
│   │   │
│   │   └── lib/
│   │       ├── api.ts            # Cliente HTTP
│   │       ├── store.ts          # Zustand store
│   │       └── utils.ts          # Utilitários
│   │
│   └── package.json
│
├── 📁 BANCO DE DADOS/             # Schemas SQL (7 fases)
│   ├── schema-fase1-fundacao.sql    # Clínicas, usuários, pacientes
│   ├── schema-fase2-agenda.sql      # Agendamentos, slots
│   ├── schema-fase3-cards.sql       # Kanban, cards, checklist
│   ├── schema-fase4-prontuario.sql  # Consultas, SOAP, receitas
│   ├── schema-fase5-financeiro.sql  # Contas, extrato
│   ├── schema-fase6-auditoria.sql   # Logs, auditoria
│   └── schema-fase7-evidencias.sql  # Documentos comprobatórios
│
├── 📁 kestra/                     # Workflows assíncronos
│   └── workflows/
│       ├── 01-confirmacao-consulta.yml
│       ├── 02-lembrete-d1.yml
│       ├── 03-processar-mensagem-whatsapp.yml
│       ├── 04-transcrever-audio.yml
│       ├── 05-gerar-soap.yml
│       └── ... (12 workflows)
│
├── 📁 API/                        # Documentação da API
│   └── api-documentation.md
│
├── 📁 IDEIAS DO PROETO/           # Specs detalhadas (11 pilares)
│
├── .cursorrules                   # Regras para Cursor AI
├── Makefile                       # Comandos úteis
└── CLAUDE.md                      # Este arquivo
```

### Fluxo de Dados Principal

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│   FastAPI       │────▶│   Supabase      │
│   (Evolution)   │     │   + LangGraph   │     │   (PostgreSQL)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     Kestra      │
                        │   (Workflows)   │
                        └─────────────────┘
```

---

## FLUXO KANBAN DE PACIENTES

### As 4 Fases da Jornada

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FASE 0    │ →  │   FASE 1    │ →  │   FASE 2    │ →  │   FASE 3    │
│    Pré-     │    │    Pré-     │    │   Dia da    │    │    Pós-     │
│ Agendamento │    │  Consulta   │    │  Consulta   │    │  Consulta   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Detalhes de Cada Fase

| Fase | Objetivo | Colunas Kanban |
|------|----------|----------------|
| **0** | Contato → Agendamento | `pre_agendamento`, `reativacao_1`, `reativacao_2`, `perdido` |
| **1** | Preparar paciente | `pendente_anamnese`, `pendente_confirmacao`, `pronto` |
| **2** | Gerenciar atendimento | `aguardando_checkin`, `em_espera`, `em_atendimento`, `finalizado` |
| **3** | Finalizar jornada | `pendente_documentos`, `pendente_pagamento`, `concluido` |

### Como Pacientes Avançam

1. **Fase 0 → Fase 1**: Quando consulta é agendada
2. **Fase 1 → Fase 2**: No dia da consulta
3. **Fase 2 → Fase 3**: Após checkout
4. **Card Derivado**: Se indicado retorno, cria novo card aguardando agendamento

### Eventos que Movem Cards

| Evento | Ação |
|--------|------|
| `CONSULTA_AGENDADA` | Card vai para Fase 1 |
| `PACIENTE_CHECKIN` | Move para `em_espera` |
| `PACIENTE_CHAMADO` | Move para `em_atendimento` |
| `CONSULTA_FINALIZADA` | Move para Fase 3 |
| `NO_SHOW` | Volta para reativação (Fase 0) |

---

## AGENTES LANGGRAPH

### Configuração do Agente

O agente está em `backend/app/chat_langgraph/agent.py`. É a "Ana", assistente virtual da clínica.

```python
# Fluxo básico
1. Recebe mensagem
2. Chama verificar_cliente (SEMPRE primeiro)
3. Identifica contexto (novo, cadastrado, com consulta)
4. Executa ferramentas conforme necessário
5. Responde naturalmente
```

### Ferramentas Disponíveis

| Ferramenta | Quando Usar |
|------------|-------------|
| `verificar_cliente` | SEMPRE no início de toda conversa |
| `cadastrar_cliente` | Após coletar todos os dados (nome, CPF, nascimento, convênio) |
| `atualizar_rascunho` | A cada dado que o cliente informar (preenche formulário em memória) |
| `ver_horarios` | Cliente quer agendar e já está cadastrado |
| `agendar_consulta` | Cliente escolheu data/hora |
| `ver_consulta` | Verificar consulta existente |
| `gerenciar_consulta` | Confirmar, cancelar ou remarcar consulta |
| `ver_info_clinica` | Cliente pergunta preço, convênios ou endereço |
| `atualizar_card` | Registrar intenção, mover card, etc |

### Modelo LLM Configurado

O provedor LLM é definido em `backend/app/core/config.py`:

```python
llm_provider: str = "groq"  # groq | deepseek | openai | openrouter
openrouter_model: str = "anthropic/claude-sonnet-4.5"
groq_model: str = "llama-3.1-70b-versatile"
```

### Estado do Agente (State)

```python
{
    "clinica_id": str,
    "telefone": str,
    "cliente_id": str | None,
    "cliente_existe": bool,
    "dados_cliente": dict,
    "consulta_agendada": dict | None,
    "card_id": str | None,
    "rascunho_cadastro": dict,  # Formulário em memória
    "mensagem_atual": str,
    "historico_mensagens": list,
    "resposta": str,
    "acoes_executadas": list
}
```

---

## INTEGRAÇÕES

### Supabase

**Projeto:** `Saas de Gestão Medica`
**ID:** `xljxypybaiolztdgoxio`
**Região:** `us-east-1`

**Tabelas Principais:**
- `clinicas` - Tenants (multi-tenant)
- `users` - Funcionários (integrado com auth.users)
- `perfis` - Permissões CLEX por módulo
- `pacientes` - Clientes da clínica
- `pacientes_alergias` - Alergias (dado crítico)
- `pacientes_medicamentos` - Uso contínuo
- `agendamentos` - Consultas marcadas
- `cards` - Kanban por fase

**RLS (Row Level Security):** Habilitado em todas as tabelas. Usuário só vê dados da sua clínica.

### Kestra (Workflows Assíncronos)

**Regra de Ouro:**
- **LangGraph** = Conversa síncrona (paciente → sistema)
- **Kestra** = Automação assíncrona (sistema → paciente)

**Workflows Implementados:**
1. `confirmacao-consulta` - Envia WhatsApp após agendamento
2. `lembrete-d1` - Lembrete D-1
3. `processar-mensagem-whatsapp` - Processa resposta do paciente
4. `transcrever-audio` - Whisper API
5. `gerar-soap` - Claude API
6. `processar-documento-financeiro` - OCR + análise
7. `conciliar-extrato` - Match automático
8. `alertas-vencimento` - Notifica contas vencendo
9. `processar-exame-whatsapp` - Extrai dados de exames
10. `anamnese-pendente` - Cobra preenchimento
11. `pesquisa-satisfacao` - Envia NPS
12. `marcar-falta` - No-show automático

### WhatsApp (Evolution API)

Arquivo: `backend/app/integracoes/whatsapp/client.py`

**Funcionalidades:**
- Enviar texto, templates, documentos
- Receber mensagens via webhook

---

## GOVERNANÇA E TRUST SCORE

### Sistema de Validação por Amostragem

O sistema executa tarefas automaticamente, mas humano valida % delas.

**Evolução da Confiança:**

| Fase | Taxa Validação | Critério para Avançar |
|------|----------------|----------------------|
| Calibração | 50% | - |
| Aprendizado | 30-40% | Erro < 5% por 2 semanas |
| Confiança | 15-25% | Erro < 3% por 4 semanas |
| Maturidade | 5-15% | Erro < 2% por 4 semanas |

**Taxa por Criticidade:**

| Tarefa | Taxa Inicial | Taxa Mínima |
|--------|--------------|-------------|
| Validar convênio | 70% | 20% |
| Agendar consulta | 50% | 15% |
| Enviar lembrete | 30% | 5% |

---

## COMANDOS IMPORTANTES

### Backend

```bash
# Entrar no diretório
cd backend

# Ativar ambiente virtual
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Rodar em desenvolvimento
uvicorn app.main:app --reload --port 8000

# Ou via Docker
docker-compose up -d
```

### Frontend

```bash
# Entrar no diretório
cd frontend

# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build
npm run build
```

### Makefile (na raiz)

```bash
make backend    # Roda backend
make frontend   # Roda frontend
make dev        # Roda ambos
make test       # Testes
```

---

## CONVENÇÕES DE CÓDIGO

### Nomenclatura

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Módulo | snake_case | `pacientes/` |
| Arquivo | snake_case | `service.py` |
| Classe | PascalCase | `PacienteService` |
| Função | snake_case | `get_paciente()` |
| Constante | UPPER_SNAKE | `MAX_UPLOAD_SIZE` |
| Schema Request | PascalCase + verbo | `PacienteCreate` |
| Schema Response | PascalCase + Response | `PacienteResponse` |

### Estrutura de um Módulo Backend

```
modulo/
├── __init__.py      # Exports públicos
├── schemas.py       # Pydantic models
├── service.py       # Lógica de negócio
└── router.py        # Endpoints FastAPI
```

### Padrão de Commits

```
feat: adiciona endpoint de receitas
fix: corrige validação de CPF
refactor: extrai lógica para service
docs: atualiza README
test: adiciona testes de agenda
```

---

## VARIÁVEIS DE AMBIENTE

### Backend (.env)

```bash
# App
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=change-me-in-production

# API
API_HOST=0.0.0.0
API_PORT=8000

# Supabase (OBRIGATÓRIO)
SUPABASE_URL=https://xljxypybaiolztdgoxio.supabase.co
SUPABASE_KEY=eyJ...                    # anon key
SUPABASE_SERVICE_KEY=eyJ...            # service_role key
SUPABASE_DB_URL=postgresql://...       # Connection string (opcional)

# JWT
JWT_SECRET=sua-chave-secreta-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# LLM Providers
LLM_PROVIDER=groq                      # groq | deepseek | openai | openrouter
GROQ_API_KEY=gsk_...                   # https://console.groq.com
OPENROUTER_API_KEY=sk-or-...           # https://openrouter.ai
OPENAI_API_KEY=sk-...                  # https://platform.openai.com

# Clínica padrão (dev)
DEFAULT_CLINICA_ID=uuid-da-clinica
```

### Onde Conseguir

| Variável | Onde |
|----------|------|
| `SUPABASE_*` | Dashboard Supabase → Settings → API |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |

---

## URLS DE DESENVOLVIMENTO

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Supabase Studio | https://supabase.com/dashboard |

---

## REFERÊNCIAS

### Documentação Detalhada no Basic Memory

Mais contexto e decisões técnicas estão documentadas no **Basic Memory** (projeto: `meu-projeto`).

Documentos disponíveis em `memory://projetos-em-implantacao/docflow/`:

| Categoria | Documentos |
|-----------|------------|
| **01-Fundamentos** | Visão Geral, Arquitetura Técnica, Governança e Trust Score |
| **02-Jornada-do-Paciente** | Fluxo Completo, Fase 0, Fase 1, Fase 2, Fase 3 |
| **03-Módulos** | Cockpit do Médico, Prontuário e IA, Agenda, Cadastro, Convênios, Materiais, Financeiro, Relatórios, Usuários |
| **04-Técnico** | Eventos e Workflows |

### Para Consultar no Claude Code

```
# Buscar no Basic Memory
mcp__basic-memory__read_note(identifier="projetos-em-implantacao/docflow/01-fundamentos/visao-geral")

# Listar projetos
mcp__supabase__list_projects()

# Ver tabelas
mcp__supabase__list_tables(project_id="xljxypybaiolztdgoxio")
```

---

## COCKPIT DO MÉDICO

### Visão Geral

O Cockpit do Médico (`/dashboard/cockpit`) é a tela principal de atendimento, com layout de **4 colunas colapsáveis** + **painel inferior expansível**.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Header: Paciente selecionado + Data/Hora                                │
├──────────┬─────────────────┬─────────────────┬─────────────────────────┤
│  Fila    │    Histórico    │  Prontuário     │     Transcrição         │
│  de      │    do           │  SOAP           │     da Consulta         │
│  Atend.  │    Paciente     │                 │                         │
│          │                 │  - Subjetivo    │     [Gravar]            │
│  [w-72]  │    [flex-1]     │  - Objetivo     │                         │
│  fixo    │    expande      │  - Avaliação    │     [flex-1]            │
│          │                 │  - Plano        │     expande             │
│          │    ← → colapsa  │                 │                         │
│          │    lateralmente │  [flex-1]       │     ← → colapsa         │
│          │                 │  expande        │     lateralmente        │
├──────────┴─────────────────┴─────────────────┴─────────────────────────┤
│  Exame Físico / Sinais Vitais                    ↑↓ expande vertical   │
│  PA: 120/80 | FC: 72 | T: 36.5°C | SpO2: 98%                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Colunas Colapsáveis

| Coluna | Largura Expandida | Comportamento |
|--------|-------------------|---------------|
| **Fila de Atendimento** | `w-72` (fixa) | Lista pacientes do dia |
| **Histórico do Paciente** | `flex-1` (expande) | Dados + validação obrigatória |
| **Prontuário SOAP** | `flex-1` (expande) | Edição do SOAP |
| **Transcrição** | `flex-1` (expande) | Gravação + texto |

Quando colapsada, cada coluna mostra apenas **ícone + tooltip** no hover.

### Sistema de Validação Obrigatória

O médico **deve confirmar** que revisou as seguintes seções antes de finalizar a consulta:

| Seção | Editável | Validação | Ícone quando pendente |
|-------|----------|-----------|----------------------|
| **Alergias** | ✅ | ✅ Obrigatória | ⚠️ Amarelo |
| **Anamnese** | ✅ | ✅ Obrigatória | ⚠️ Amarelo |
| **Medicamentos em Uso** | ✅ | ✅ Obrigatória | ⚠️ Amarelo |
| **Antecedentes** | ✅ | ✅ Obrigatória | ⚠️ Amarelo |

**Fluxo:**
1. Médico revisa cada seção
2. Clica no botão ✓ para marcar como "Conferido"
3. Ícone muda de ⚠️ amarelo para ✅ verde
4. Só pode finalizar consulta após validar todas as seções

### Modal de Edição

Cada seção editável abre um modal para alteração:
- **Alergias**: Lista separada por vírgula
- **Medicamentos**: Um por linha
- **Antecedentes**: Texto livre
- **Anamnese**: Queixa principal + observações do médico

### Estrutura de Arquivos (Refatorado - Sprint 6)

```
frontend/src/app/dashboard/cockpit/
├── page.tsx                      # Página principal (790 linhas, orquestra tudo)
├── types.ts                      # Interfaces TypeScript
├── styles.ts                     # Estilos Liquid Glass compartilhados
├── mocks.ts                      # Dados mock para desenvolvimento
├── components/
│   ├── index.ts                  # Exports centralizados
│   ├── ColunaColapsavel.tsx      # Wrapper reutilizável com expansão lateral
│   ├── PainelPreparado.tsx       # Coluna 2: Histórico + validações obrigatórias
│   ├── PainelSOAP.tsx            # Coluna 3: Editor SOAP editável
│   ├── PainelExameFisicoInferior.tsx  # Painel inferior: Sinais vitais
│   ├── ModalEdicao.tsx           # Modal genérico para editar seções
│   ├── ModalHistoricoConsulta.tsx # Modal para ver consulta anterior
│   └── Toolbar.tsx               # Barra inferior: Receita, Atestado, etc
└── hooks/
    ├── index.ts                  # Exports centralizados
    └── useTranscricao.ts         # Lógica de gravação de áudio
```

### Componentes Principais

| Componente | Arquivo | Função |
|------------|---------|--------|
| `ColunaColapsavel` | `components/ColunaColapsavel.tsx` | Wrapper com expansão lateral + tooltip |
| `PainelPreparado` | `components/PainelPreparado.tsx` | Histórico + validações obrigatórias (Anamnese, Alergias, etc) |
| `PainelSOAP` | `components/PainelSOAP.tsx` | Editor SOAP com campos editáveis (S, O, A, P) |
| `PainelExameFisicoInferior` | `components/PainelExameFisicoInferior.tsx` | Sinais vitais com expansão vertical |
| `ModalEdicao` | `components/ModalEdicao.tsx` | Modal genérico para edição de seções |
| `ModalHistoricoConsulta` | `components/ModalHistoricoConsulta.tsx` | Visualização de consulta anterior |
| `Toolbar` | `components/Toolbar.tsx` | Botões: Receita, Atestado, Exames, Finalizar |

### Hooks Customizados

| Hook | Arquivo | Função |
|------|---------|--------|
| `useTranscricao` | `hooks/useTranscricao.ts` | Gerencia gravação de áudio, timer, toggle |

**Nota:** A Fila de Atendimento e Transcrição estão inline no `page.tsx` (não foram extraídos para componentes separados).

### Estados de Validação

```typescript
// hooks/useCockpitState.ts
const [validacoes, setValidacoes] = useState({
  anamnese: false,
  antecedentes: false,
  medicamentos: false,
  alergias: false,
});

// Verificar se pode finalizar
const todasValidacoes = Object.values(validacoes).every(v => v);
```

---

## STATUS DO PROJETO

### Sprints Concluídas (1-6)
- [x] Backend completo (auth, clínicas, pacientes, agenda, kanban, governança)
- [x] Frontend com Design Liquid Glass
- [x] Chat simulador com Groq API
- [x] Sistema de cards/kanban
- [x] Chat LangGraph implementado
- [x] Ferramentas do agente
- [x] Cockpit do Médico (layout, validações, modais)

### Sprint Atual (8) - Transcrição de Consultas (Whisper)
- [x] Endpoint `POST /prontuario/transcricoes/upload` - Upload de áudio
- [x] Endpoint `POST /prontuario/transcricoes/audio-chunk` - Streaming de chunks
- [x] Service com lógica de transcrição via Groq Whisper
- [x] Config `groq_model_whisper = whisper-large-v3`
- [x] Integração com GroqClient existente (GRÁTIS)
- [ ] Integrar frontend cockpit com API de transcrição
- [ ] Enviar áudio gravado para backend
- [ ] Exibir transcrição em tempo real

### Próximas Sprints
- Sprint 7: Integração WhatsApp real (Evolution API)
- Sprint 9: SOAP automático (Claude)

---

**Cliente Piloto:** DAG Serviços Médicos (Tulio Carvalho)
