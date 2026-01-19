# -*- coding: utf-8 -*-
"""
Kanban Module
Gerenciamento de cards com automação baseada em checklist.
"""
from app.kanban.router import router
from app.kanban.service import kanban_service, KanbanService, FaseKanban
from app.kanban.schemas import (
    CardResponse,
    CardCreate,
    ChecklistItemUpdate,
    MoverCardRequest,
    KanbanResponse
)

__all__ = [
    "router",
    "kanban_service",
    "KanbanService",
    "FaseKanban",
    "CardResponse",
    "CardCreate",
    "ChecklistItemUpdate",
    "MoverCardRequest",
    "KanbanResponse"
]
