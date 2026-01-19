# -*- coding: utf-8 -*-
"""
Governança - Router
Endpoints para o sistema de supervisão humana integrada.

TRIGGERS (chamados pelos workflows):
1. POST /trigger/whatsapp - Mensagem WhatsApp recebida
2. POST /trigger/card-criado - Card criado no Kanban
3. POST /trigger/mudanca-fase - Card mudou de fase

VALIDAÇÃO (usados pela governadora):
- GET /validacoes - Lista pendentes
- POST /validacoes/{id}/validar - Processa validação
- GET /dashboard - Visão geral
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.security import CurrentUser, require_permission
from app.governanca.service import (
    governanca_service,
    TriggerType,
    StatusValidacao
)


router = APIRouter(prefix="/governanca", tags=["Governança"])


# ============================================
# SCHEMAS
# ============================================

class TriggerWhatsAppRequest(BaseModel):
    telefone: str
    mensagem: str
    interpretacao: Dict[str, Any]
    acao_tomada: Dict[str, Any]


class TriggerCardCriadoRequest(BaseModel):
    card_id: str
    agendamento: Dict[str, Any]
    paciente: Dict[str, Any]


class TriggerMudancaFaseRequest(BaseModel):
    card_id: str
    fase_anterior: int
    fase_nova: int
    checklist_anterior: Dict[str, Any]


class RegistrarEvidenciaRequest(BaseModel):
    card_id: str
    tarefa_key: str
    fase: int
    dados: Dict[str, Any]
    arquivo_url: Optional[str] = None


class ValidarRequest(BaseModel):
    resultado: str  # aprovado, corrigido, rejeitado
    correcoes: Optional[Dict[str, Any]] = None
    observacao: Optional[str] = None


class TriggerResponse(BaseModel):
    requer_validacao: bool
    validacao_id: Optional[str] = None
    problemas: Optional[List[str]] = None


# ============================================
# TRIGGERS (chamados pelos workflows)
# ============================================

@router.post(
    "/trigger/whatsapp",
    response_model=TriggerResponse,
    summary="Trigger: Mensagem WhatsApp"
)
async def trigger_whatsapp(
    data: TriggerWhatsAppRequest,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    TRIGGER 1: Mensagem WhatsApp recebida.
    
    Chamado pelo workflow quando uma mensagem é processada.
    Registra a interpretação e ação tomada para validação.
    """
    return await governanca_service.trigger_mensagem_whatsapp(
        clinica_id=current_user.clinica_id,
        telefone=data.telefone,
        mensagem=data.mensagem,
        interpretacao=data.interpretacao,
        acao_tomada=data.acao_tomada,
        current_user=current_user
    )


@router.post(
    "/trigger/card-criado",
    response_model=TriggerResponse,
    summary="Trigger: Card criado"
)
async def trigger_card_criado(
    data: TriggerCardCriadoRequest,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    TRIGGER 2: Card criado no Kanban.
    
    Chamado quando um novo card é criado.
    Verifica se os dados estão corretos.
    """
    return await governanca_service.trigger_card_criado(
        clinica_id=current_user.clinica_id,
        card_id=data.card_id,
        agendamento=data.agendamento,
        paciente=data.paciente,
        current_user=current_user
    )


@router.post(
    "/trigger/mudanca-fase",
    response_model=TriggerResponse,
    summary="Trigger: Mudança de fase"
)
async def trigger_mudanca_fase(
    data: TriggerMudancaFaseRequest,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    TRIGGER 3: Card mudou de fase no Kanban.
    
    Chamado automaticamente quando um card muda de fase.
    Verifica se todas as evidências da fase anterior estão completas.
    """
    return await governanca_service.trigger_mudanca_fase(
        clinica_id=current_user.clinica_id,
        card_id=data.card_id,
        fase_anterior=data.fase_anterior,
        fase_nova=data.fase_nova,
        checklist_anterior=data.checklist_anterior,
        current_user=current_user
    )


# ============================================
# EVIDÊNCIAS
# ============================================

@router.post(
    "/evidencias",
    summary="Registrar evidência de tarefa"
)
async def registrar_evidencia(
    data: RegistrarEvidenciaRequest,
    current_user: CurrentUser = Depends(require_permission("governanca", "C"))
):
    """
    Registra evidência de uma tarefa cumprida.
    
    Chamado pelos workflows quando uma tarefa é executada.
    A evidência é usada na validação de mudança de fase.
    """
    return await governanca_service.registrar_evidencia(
        card_id=data.card_id,
        tarefa_key=data.tarefa_key,
        fase=data.fase,
        dados=data.dados,
        current_user=current_user,
        arquivo_url=data.arquivo_url
    )


# ============================================
# VALIDAÇÃO (usados pela governadora)
# ============================================

@router.get(
    "/validacoes",
    summary="Lista validações pendentes"
)
async def listar_validacoes(
    trigger: Optional[TriggerType] = Query(None, description="Filtrar por tipo de trigger"),
    current_user: CurrentUser = Depends(require_permission("governanca", "L"))
):
    """
    Lista validações pendentes para a governadora.
    
    Pode filtrar por tipo de trigger:
    - mensagem_whatsapp
    - card_criado
    - mudanca_fase
    """
    return await governanca_service.listar_pendentes(
        current_user=current_user,
        trigger=trigger
    )


@router.get(
    "/validacoes/{validacao_id}",
    summary="Detalhes de validação"
)
async def get_validacao(
    validacao_id: str,
    current_user: CurrentUser = Depends(require_permission("governanca", "L"))
):
    """
    Retorna detalhes completos de uma validação.
    
    Inclui:
    - Evidências coletadas
    - Dados para verificação
    - Perguntas orientadoras
    """
    # Por simplicidade, retorna da lista filtrada
    pendentes = await governanca_service.listar_pendentes(current_user)
    validacao = next((v for v in pendentes["itens"] if v["id"] == validacao_id), None)
    if not validacao:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Validação não encontrada")
    return validacao


@router.post(
    "/validacoes/{validacao_id}/validar",
    summary="Processar validação"
)
async def processar_validacao(
    validacao_id: str,
    data: ValidarRequest,
    current_user: CurrentUser = Depends(require_permission("governanca", "E"))
):
    """
    Processa a validação da governadora.
    
    Resultados:
    - **aprovado**: Ação correta, trust +2
    - **corrigido**: Erro menor corrigido, trust -5
    - **rejeitado**: Erro grave, trust -15
    """
    return await governanca_service.processar_validacao(
        validacao_id=validacao_id,
        resultado=StatusValidacao(data.resultado),
        current_user=current_user,
        correcoes=data.correcoes,
        observacao=data.observacao
    )


@router.post(
    "/validacoes/aprovar-lote",
    summary="Aprovar múltiplas validações"
)
async def aprovar_lote(
    validacao_ids: List[str],
    current_user: CurrentUser = Depends(require_permission("governanca", "E"))
):
    """Aprova múltiplas validações de uma vez."""
    resultados = []
    for vid in validacao_ids:
        try:
            r = await governanca_service.processar_validacao(
                validacao_id=vid,
                resultado=StatusValidacao.APROVADO,
                current_user=current_user
            )
            resultados.append({"id": vid, "sucesso": True, **r})
        except Exception as e:
            resultados.append({"id": vid, "sucesso": False, "erro": str(e)})
    
    return {
        "total": len(validacao_ids),
        "sucesso": len([r for r in resultados if r.get("sucesso")]),
        "resultados": resultados
    }


# ============================================
# DASHBOARD
# ============================================

@router.get(
    "/dashboard",
    summary="Dashboard da governança"
)
async def get_dashboard(
    current_user: CurrentUser = Depends(require_permission("governanca", "L"))
):
    """
    Dashboard completo para a governadora.
    
    Inclui:
    - Status de implantação (dias restantes)
    - Validações pendentes
    - Performance dos últimos 30 dias
    - Trust scores por categoria
    """
    return await governanca_service.get_dashboard(current_user)
