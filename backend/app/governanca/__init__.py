# -*- coding: utf-8 -*-
"""
Governança Module
Sistema de supervisão humana integrado com Kanban e Evidências.

MODELO:
- Sistema executa primeiro
- Governadora valida depois
- Se erro, corrige
- Trust score aprende

TRIGGERS:
1. Mensagem WhatsApp → Verifica interpretação
2. Card criado → Verifica dados
3. Mudança de fase → Verifica evidências

USO:
```python
from app.governanca import governanca_service, TriggerType

# Trigger 1: WhatsApp
await governanca_service.trigger_mensagem_whatsapp(
    clinica_id="...",
    telefone="11999...",
    mensagem="quero agendar",
    interpretacao={"intencao": "agendar"},
    acao_tomada={"tipo": "iniciar_agendamento"},
    current_user=user
)

# Trigger 2: Card criado
await governanca_service.trigger_card_criado(
    clinica_id="...",
    card_id="card-123",
    agendamento={...},
    paciente={...},
    current_user=user
)

# Trigger 3: Mudança de fase
await governanca_service.trigger_mudanca_fase(
    clinica_id="...",
    card_id="card-123",
    fase_anterior=0,
    fase_nova=1,
    checklist_anterior={...},
    current_user=user
)
```
"""
from app.governanca.router import router
from app.governanca.service import (
    governanca_service,
    GovernancaService,
    TriggerType,
    TipoEvidencia,
    StatusValidacao,
    EVIDENCIAS_ESPERADAS,
    DIAS_IMPLANTACAO
)

__all__ = [
    "router",
    "governanca_service",
    "GovernancaService",
    "TriggerType",
    "TipoEvidencia",
    "StatusValidacao",
    "EVIDENCIAS_ESPERADAS",
    "DIAS_IMPLANTACAO"
]
