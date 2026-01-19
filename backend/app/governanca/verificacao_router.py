# -*- coding: utf-8 -*-
"""
Verificação de Evidências - Router
Endpoints para verificação e governança baseada em evidências.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import CurrentUser, require_permission
from app.governanca.verificacao_service import verificacao_service


router = APIRouter(prefix="/verificacao", tags=["Verificação"])


# ============================================
# TRIGGERS DE VERIFICAÇÃO
# ============================================

@router.post(
    "/trigger/mensagem-whatsapp",
    summary="Trigger 1: Verificar após mensagem WhatsApp"
)
async def trigger_mensagem_whatsapp(
    telefone: str,
    mensagem_id: str,
    clinica_id: str,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    Verifica se cadastro foi criado corretamente após mensagem WhatsApp.
    
    Chamado pelo workflow quando recebe mensagem de número novo.
    """
    return await verificacao_service.verificar_mensagem_whatsapp(
        telefone=telefone,
        mensagem_id=mensagem_id,
        clinica_id=clinica_id,
        current_user=current_user
    )


@router.post(
    "/trigger/card-criado/{card_id}",
    summary="Trigger 2: Verificar card criado"
)
async def trigger_card_criado(
    card_id: str,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    Verifica se card foi criado com todos os dados necessários.
    
    Chamado automaticamente quando card é criado no Kanban.
    """
    return await verificacao_service.verificar_card_criado(
        card_id=card_id,
        current_user=current_user
    )


@router.post(
    "/trigger/mudanca-fase/{card_id}",
    summary="Trigger 3: Verificar mudança de fase"
)
async def trigger_mudanca_fase(
    card_id: str,
    fase_anterior: int,
    fase_nova: int,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    Verifica se todas as evidências da fase anterior existem.
    
    Chamado automaticamente quando card muda de fase no Kanban.
    """
    return await verificacao_service.verificar_mudanca_fase(
        card_id=card_id,
        fase_anterior=fase_anterior,
        fase_nova=fase_nova,
        current_user=current_user
    )


# ============================================
# ALERTAS PARA GOVERNADORA
# ============================================

@router.get(
    "/alertas",
    summary="Lista alertas pendentes"
)
async def listar_alertas(
    limit: int = Query(50, le=100),
    current_user: CurrentUser = Depends(require_permission("governanca", "L"))
):
    """
    Lista alertas de evidências faltando para a governadora.
    """
    return await verificacao_service.listar_alertas_pendentes(
        current_user=current_user,
        limit=limit
    )


@router.post(
    "/alertas/{alerta_id}/resolver",
    summary="Resolver alerta"
)
async def resolver_alerta(
    alerta_id: str,
    resolucao: str = Query(..., description="ok, ignorado, corrigido"),
    observacao: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("governanca", "E"))
):
    """
    Governadora resolve um alerta de evidência.
    """
    return await verificacao_service.resolver_alerta(
        alerta_id=alerta_id,
        resolucao=resolucao,
        current_user=current_user,
        observacao=observacao
    )


# ============================================
# MÉTRICAS E TAXA DE VALIDAÇÃO
# ============================================

@router.get(
    "/taxa-validacao",
    summary="Calcula taxa de validação atual"
)
async def get_taxa_validacao(
    dias: int = Query(30, le=365, description="Período de análise em dias"),
    current_user: CurrentUser = Depends(require_permission("governanca", "L"))
):
    """
    Calcula a taxa de validação necessária baseada na performance.
    
    - Primeiros 30 dias: 100% (fase de implantação)
    - Depois: Diminui conforme taxa de sucesso do sistema
    """
    return await verificacao_service.calcular_taxa_validacao(
        clinica_id=current_user.clinica_id,
        current_user=current_user,
        dias=dias
    )
