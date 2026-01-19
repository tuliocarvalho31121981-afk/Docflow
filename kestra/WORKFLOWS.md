# Kestra Workflows Documentation
## Sistema de Gestão de Clínicas

**Versão:** 1.0  
**Namespace:** `clinica`  
**Total de Workflows:** 12

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Workflows por Categoria](#3-workflows-por-categoria)
4. [Detalhamento dos Workflows](#4-detalhamento-dos-workflows)
5. [Configuração](#5-configuração)
6. [Monitoramento](#6-monitoramento)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Visão Geral

### 1.1 O que é Kestra?

Kestra é uma plataforma de orquestração de workflows que permite:
- Automação de tarefas complexas
- Integração entre sistemas
- Execução agendada (cron)
- Execução sob demanda (webhook/API)
- Tratamento de erros e retry

### 1.2 Por que Kestra neste projeto?

| Alternativa | Problema |
|-------------|----------|
| Cron jobs | Difícil monitorar, sem UI |
| Celery | Complexo de configurar |
| AWS Step Functions | Vendor lock-in |
| **Kestra** | ✅ Open source, UI visual, fácil de usar |

### 1.3 Papel no Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     Trigger     ┌──────────┐                      │
│  │  FastAPI │ ───────────────►│  KESTRA  │                      │
│  └──────────┘                 └────┬─────┘                      │
│       ▲                            │                            │
│       │                            │ Executa                    │
│       │                            ▼                            │
│       │                    ┌───────────────┐                    │
│       │                    │   Workflows   │                    │
│       │                    │               │                    │
│       │                    │ • WhatsApp    │                    │
│       │                    │ • Whisper     │                    │
│       │                    │ • Claude      │                    │
│       │                    │ • OCR         │                    │
│       │                    └───────┬───────┘                    │
│       │                            │                            │
│       │         Callback           │                            │
│       └────────────────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura

### 2.1 Tipos de Trigger

| Tipo | Uso | Exemplo |
|------|-----|---------|
| **Webhook** | Sob demanda, disparado pela API | Transcrição de áudio |
| **Schedule** | Cron, execução periódica | Lembretes D-1 |
| **Flow** | Disparado por outro workflow | Subflows |

### 2.2 Padrão de Comunicação

```
1. API recebe request do usuário
         │
         ▼
2. API processa ação síncrona
         │
         ▼
3. API dispara workflow via HTTP
         │
         ▼
4. Kestra executa workflow async
         │
         ▼
5. Workflow chama APIs externas
         │
         ▼
6. Workflow faz callback para API
         │
         ▼
7. API notifica usuário (push/realtime)
```

### 2.3 Secrets

Todos os workflows usam secrets do Kestra:

| Secret | Descrição |
|--------|-----------|
| `API_URL` | URL da API FastAPI |
| `API_INTERNAL_TOKEN` | Token de serviço |
| `SUPABASE_URL` | URL do Supabase |
| `SUPABASE_SERVICE_KEY` | Chave de serviço |
| `EVOLUTION_API_URL` | URL da Evolution API |
| `EVOLUTION_API_KEY` | API key do WhatsApp |
| `EVOLUTION_INSTANCE` | Nome da instância |
| `OPENAI_API_KEY` | API key do Whisper |
| `ANTHROPIC_API_KEY` | API key do Claude |
| `GOOGLE_VISION_API_KEY` | API key do OCR |
| `WEBHOOK_SECRET` | Secret para callbacks |
| `FRONTEND_URL` | URL do frontend |

---

## 3. Workflows por Categoria

### 3.1 Comunicação (WhatsApp)

| ID | Nome | Trigger | Descrição |
|----|------|---------|-----------|
| 01 | `confirmacao-consulta` | Webhook | Envia confirmação ao agendar |
| 02 | `lembrete-d1` | Cron 18h | Lembra consulta do dia seguinte |
| 03 | `processar-mensagem-whatsapp` | Webhook | Processa resposta do paciente |
| 10 | `anamnese-pendente` | Cron 10h | Envia link de anamnese D-3 |
| 11 | `pesquisa-satisfacao` | Cron 19h | Envia NPS pós-consulta |

### 3.2 Inteligência Artificial

| ID | Nome | Trigger | Descrição |
|----|------|---------|-----------|
| 04 | `transcrever-audio` | Webhook | Whisper transcreve consulta |
| 05 | `gerar-soap` | Webhook | Claude gera nota SOAP |
| 06 | `processar-documento-financeiro` | Webhook | OCR + IA estrutura NF/boleto |
| 09 | `processar-exame-whatsapp` | Webhook | OCR identifica exame enviado |

### 3.3 Financeiro

| ID | Nome | Trigger | Descrição |
|----|------|---------|-----------|
| 07 | `conciliar-extrato` | Webhook | Match automático de transações |
| 08 | `alertas-vencimento` | Cron 8h | Alerta contas vencendo |

### 3.4 Operacional

| ID | Nome | Trigger | Descrição |
|----|------|---------|-----------|
| 12 | `marcar-falta` | Cron horário | Marca falta automaticamente |

---

## 4. Detalhamento dos Workflows

### 4.1 confirmacao-consulta

**Arquivo:** `01-confirmacao-consulta.yml`

**Trigger:** Webhook quando agendamento é criado

**Fluxo:**
```
1. Recebe dados do agendamento
         │
         ▼
2. Formata data para exibição
         │
         ▼
3. Envia WhatsApp via Evolution
         │
         ▼
4. Registra mensagem no banco
         │
         ▼
5. Atualiza checklist do card
```

**Inputs:**
| Nome | Tipo | Obrigatório |
|------|------|-------------|
| agendamento_id | STRING | Sim |
| paciente_telefone | STRING | Sim |
| paciente_nome | STRING | Sim |
| medico_nome | STRING | Sim |
| data | STRING | Sim |
| hora | STRING | Sim |
| clinica_id | STRING | Sim |

---

### 4.2 lembrete-d1

**Arquivo:** `02-lembrete-d1.yml`

**Trigger:** Cron `0 18 * * *` (18h todos os dias)

**Fluxo:**
```
1. Calcula data de amanhã
         │
         ▼
2. Busca agendamentos confirmados
         │
         ▼
3. Para cada agendamento:
   ├── Formata data
   ├── Envia WhatsApp
   └── Registra envio
         │
         ▼
4. Log de conclusão
```

---

### 4.3 processar-mensagem-whatsapp

**Arquivo:** `03-processar-mensagem-whatsapp.yml`

**Trigger:** Webhook quando Evolution recebe mensagem

**Fluxo:**
```
1. Busca paciente pelo telefone
         │
         ▼
2. Busca agendamento pendente
         │
         ▼
3. Decide ação baseado no conteúdo:
   │
   ├── "SIM" → Confirma agendamento
   ├── "CANCELAR" → Cancela agendamento
   ├── "REMARCAR" → Notifica equipe
   ├── Mídia → Dispara processar-exame
   └── Outro → Resposta padrão
         │
         ▼
4. Registra mensagem
```

**Decisões de ação:**
| Mensagem | Ação |
|----------|------|
| SIM, S, CONFIRMO, 1 | Confirmar |
| NAO, CANCELAR, 2 | Cancelar |
| REMARCAR, REAGENDAR, 3 | Remarcar |
| Imagem/PDF | Processar como exame |
| Outro | Resposta padrão |

---

### 4.4 transcrever-audio

**Arquivo:** `04-transcrever-audio.yml`

**Trigger:** Webhook quando médico envia áudio

**Fluxo:**
```
1. Busca contexto do paciente
         │
         ▼
2. Download do áudio do Storage
         │
         ▼
3. Prepara prompt contextualizado
         │
         ▼
4. Chama Whisper API
         │
         ▼
5. Processa resultado (segmentos)
         │
         ▼
6. Salva transcrição no banco
         │
         ▼
7. Notifica médico
         │
         ▼
8. Callback para API
```

**Contexto usado no prompt:**
- Queixa principal (da anamnese)
- Medicamentos em uso
- Alergias conhecidas

---

### 4.5 gerar-soap

**Arquivo:** `05-gerar-soap.yml`

**Trigger:** Webhook quando médico solicita

**Fluxo:**
```
1. Busca transcrição
         │
         ▼
2. Busca dados do paciente
         │
         ▼
3. Busca anamnese
         │
         ▼
4. Monta prompt completo
         │
         ▼
5. Chama Claude API
         │
         ▼
6. Processa resposta JSON
         │
         ▼
7. Salva SOAP no banco
         │
         ▼
8. Notifica médico
```

**Output do Claude:**
```json
{
  "subjetivo": "Texto do S",
  "objetivo": "Texto do O",
  "avaliacao": "Texto do A",
  "plano": "Texto do P",
  "exame_fisico": {
    "sinais_vitais": {...}
  },
  "cids_sugeridos": [
    {"codigo": "X00.0", "descricao": "...", "tipo": "principal"}
  ],
  "alertas": ["..."],
  "confianca": 0.85
}
```

---

### 4.6 processar-documento-financeiro

**Arquivo:** `06-processar-documento-financeiro.yml`

**Trigger:** Webhook quando upload de NF/boleto

**Fluxo:**
```
1. Download do documento
         │
         ▼
2. OCR com Google Vision
         │
         ▼
3. Extrai texto do OCR
         │
         ▼
4. Busca fornecedores cadastrados
         │
         ▼
5. Claude analisa e estrutura
         │
         ▼
6. Atualiza/cria conta a pagar
         │
         ▼
7. Atualiza documento
         │
         ▼
8. Notifica usuário
```

**Output do Claude:**
```json
{
  "tipo_documento": "nota_fiscal",
  "fornecedor": {
    "nome": "ABC Ltda",
    "cnpj": "12.345.678/0001-99",
    "match_id": "uuid-se-encontrou"
  },
  "valor": 1500.00,
  "data_emissao": "2024-01-15",
  "data_vencimento": "2024-02-15",
  "numero_documento": "12345",
  "codigo_barras": "...",
  "confianca": 0.95
}
```

---

### 4.7 conciliar-extrato

**Arquivo:** `07-conciliar-extrato.yml`

**Trigger:** Webhook após importação OFX

**Fluxo:**
```
1. Busca transações não conciliadas
         │
         ▼
2. Busca contas a pagar pendentes
         │
         ▼
3. Busca contas a receber pendentes
         │
         ▼
4. Algoritmo de matching:
   ├── Score por valor (40%)
   ├── Score por data (30%)
   └── Score por nome (30%)
         │
         ▼
5. Salva sugestões
         │
         ▼
6. Auto-concilia score >= 90%
         │
         ▼
7. Notifica resultado
```

**Algoritmo de Score:**
| Critério | Peso | Regra |
|----------|------|-------|
| Valor | 40% | Exato=40, ±1%=35, ±5%=20 |
| Data | 30% | Mesmo dia=30, ±3d=25, ±7d=15 |
| Nome | 30% | Similaridade de string |

---

### 4.8 alertas-vencimento

**Arquivo:** `08-alertas-vencimento.yml`

**Trigger:** Cron `0 8 * * *` (8h todos os dias)

**Fluxo:**
```
1. Lista clínicas ativas
         │
         ▼
2. Para cada clínica:
   ├── Busca contas vencendo hoje
   ├── Busca contas vencidas
   ├── Busca saldo atual
   │        │
   │        ▼
   ├── Gera alertas:
   │   ├── Vencimento hoje
   │   ├── Contas atrasadas
   │   └── Saldo baixo
   │        │
   │        ▼
   └── Envia notificações
```

---

### 4.9 processar-exame-whatsapp

**Arquivo:** `09-processar-exame-whatsapp.yml`

**Trigger:** Subflow do processar-mensagem-whatsapp

**Fluxo:**
```
1. Busca paciente
         │
         ▼
2. Busca card ativo
         │
         ▼
3. Download da mídia
         │
         ▼
4. Upload para Storage
         │
         ▼
5. OCR (se imagem/PDF)
         │
         ▼
6. Claude identifica tipo de exame
         │
         ▼
7. Registra documento
         │
         ▼
8. Atualiza checklist do card
         │
         ▼
9. Notifica equipe
```

---

### 4.10 anamnese-pendente

**Arquivo:** `10-anamnese-pendente.yml`

**Trigger:** Cron `0 10 * * *` (10h todos os dias)

**Fluxo:**
```
1. Calcula data D+3
         │
         ▼
2. Busca agendamentos sem anamnese
         │
         ▼
3. Para cada:
   ├── Gera token único
   ├── Envia WhatsApp com link
   ├── Registra envio
   └── Atualiza checklist
```

---

### 4.11 pesquisa-satisfacao

**Arquivo:** `11-pesquisa-satisfacao.yml`

**Trigger:** Cron `0 19 * * *` (19h todos os dias)

**Fluxo:**
```
1. Busca consultas finalizadas hoje
         │
         ▼
2. Para cada:
   ├── Gera token da pesquisa
   ├── Envia WhatsApp
   └── Marca como enviada
```

---

### 4.12 marcar-falta

**Arquivo:** `12-marcar-falta.yml`

**Trigger:** Cron `0 8-20 * * 1-6` (horário comercial)

**Fluxo:**
```
1. Calcula limite (30 min atrás)
         │
         ▼
2. Busca agendamentos atrasados
         │
         ▼
3. Para cada:
   ├── Atualiza status → faltou
   ├── Notifica paciente
   ├── Notifica equipe
   └── Atualiza card
```

---

## 5. Configuração

### 5.1 Instalação do Kestra

```bash
# Docker Compose
docker-compose up -d kestra

# Ou standalone
docker run -d \
  --name kestra \
  -p 8080:8080 \
  -v kestra-data:/app/storage \
  kestra/kestra:latest
```

### 5.2 Deploy dos Workflows

```bash
# Via CLI
kestra flow namespace update clinica ./workflows/

# Via API
curl -X POST http://localhost:8080/api/v1/flows \
  -H "Content-Type: application/x-yaml" \
  --data-binary @workflows/01-confirmacao-consulta.yml
```

### 5.3 Configuração de Secrets

```bash
# Via CLI
kestra secret create API_URL "https://api.clinica.com"
kestra secret create API_INTERNAL_TOKEN "token-secreto"
# ... outros secrets

# Via UI
# Acesse http://localhost:8080 → Settings → Secrets
```

---

## 6. Monitoramento

### 6.1 UI do Kestra

- **Dashboard:** Visão geral de execuções
- **Flows:** Lista de workflows
- **Executions:** Histórico de execuções
- **Logs:** Logs detalhados por task

### 6.2 Métricas Importantes

| Métrica | Alerta |
|---------|--------|
| Taxa de sucesso | < 95% |
| Tempo médio de execução | > 5 min |
| Execuções pendentes | > 100 |
| Erros por hora | > 10 |

### 6.3 Logs

```bash
# Ver logs do container
docker logs -f clinica-kestra

# Logs de execução específica
curl http://localhost:8080/api/v1/executions/{id}/logs
```

---

## 7. Troubleshooting

### 7.1 Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `secret not found` | Secret não configurado | Criar secret no Kestra |
| `connection refused` | API fora do ar | Verificar API |
| `rate limit exceeded` | Muitas chamadas | Adicionar retry/delay |
| `timeout` | Operação lenta | Aumentar timeout |

### 7.2 Re-executar Workflow

```bash
# Via API
curl -X POST http://localhost:8080/api/v1/executions/{id}/restart

# Via UI
# Executions → Selecionar → Restart
```

### 7.3 Debug

1. Acesse a execução no Kestra UI
2. Clique em cada task para ver:
   - Inputs recebidos
   - Outputs gerados
   - Logs de execução
   - Erro (se houver)

---

## Resumo

| Workflow | Trigger | Frequência |
|----------|---------|------------|
| confirmacao-consulta | Webhook | Sob demanda |
| lembrete-d1 | Cron | Diário 18h |
| processar-mensagem-whatsapp | Webhook | Sob demanda |
| transcrever-audio | Webhook | Sob demanda |
| gerar-soap | Webhook | Sob demanda |
| processar-documento-financeiro | Webhook | Sob demanda |
| conciliar-extrato | Webhook | Sob demanda |
| alertas-vencimento | Cron | Diário 8h |
| processar-exame-whatsapp | Webhook | Sob demanda |
| anamnese-pendente | Cron | Diário 10h |
| pesquisa-satisfacao | Cron | Diário 19h |
| marcar-falta | Cron | Horário comercial |

---

**Documento gerado em:** Janeiro 2026  
**Versão:** 1.0
