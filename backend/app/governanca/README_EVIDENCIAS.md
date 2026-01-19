# Sistema de Governança Integrada com Evidências

## Visão Geral

O sistema usa **3 triggers** para verificar automaticamente se as tarefas foram cumpridas com evidências.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         MODELO DE GOVERNANÇA                                │
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │  TRIGGER 1  │     │  TRIGGER 2  │     │  TRIGGER 3  │                  │
│   │  Mensagem   │     │  Card       │     │  Mudança    │                  │
│   │  WhatsApp   │     │  Criado     │     │  de Fase    │                  │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                  │
│          │                   │                   │                         │
│          ▼                   ▼                   ▼                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                   VERIFICAR EVIDÊNCIAS                              │  │
│   │                                                                     │  │
│   │  Para cada tarefa:                                                  │  │
│   │  ├── Tipo LOG → Busca na tabela mensagens/eventos                  │  │
│   │  ├── Tipo DOCUMENTO → Busca na tabela evidencias                   │  │
│   │  └── Tipo CONFIRMAÇÃO → Busca evento de ação humana                │  │
│   └─────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                          │
│                    ┌────────────┴────────────┐                             │
│                    ▼                         ▼                             │
│             ┌────────────┐            ┌────────────┐                       │
│             │ EVIDÊNCIA  │            │ EVIDÊNCIA  │                       │
│             │ ENCONTRADA │            │ FALTANDO   │                       │
│             │            │            │            │                       │
│             │ ✅ Log OK  │            │ ⚠️ Alerta  │                       │
│             │ Continua   │            │ Governança │                       │
│             └────────────┘            └────────────┘                       │
│                                              │                             │
│                                              ▼                             │
│                                    ┌────────────────┐                      │
│                                    │  GOVERNADORA   │                      │
│                                    │                │                      │
│                                    │ [Resolver]     │                      │
│                                    │ [Corrigir]     │                      │
│                                    │ [Ignorar]      │                      │
│                                    └────────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tipos de Evidência

| Tipo | Descrição | Onde Busca | Exemplo |
|------|-----------|------------|---------|
| **LOG** | Sistema registra automaticamente | `mensagens`, `card_eventos` | Confirmação enviada, check-in |
| **DOCUMENTO** | Arquivo anexado | `evidencias` | Anamnese, exame, SOAP |
| **CONFIRMAÇÃO** | Ação humana | `card_eventos` | Médico iniciou consulta |

---

## Modelo de Validação

### Fase de Implantação (Dias 1-30)
- **Taxa de validação: 100%**
- Toda ação gera alerta para governadora

### Após Implantação (Dia 31+)

| Taxa Sucesso | Taxa Validação |
|--------------|----------------|
| ≥ 95% | 5% |
| ≥ 90% | 20% |
| ≥ 80% | 40% |
| ≥ 70% | 60% |
| < 70% | 100% |

---

## Resumo

**Kanban** = Motor de automação
**Evidências** = Prova de cumprimento  
**Triggers** = Disparam verificação
**Alertas** = Notifica governadora
**Taxa** = Diminui conforme sistema acerta
