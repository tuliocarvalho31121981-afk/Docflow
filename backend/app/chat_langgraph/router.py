# app/chat_langgraph/router.py
"""
Endpoints FastAPI para Chat LangGraph - ADAPTADO PARA CLINICOS
Usa o padrão de database do projeto (get_service_client + SupabaseClient)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

# ============================================
# IMPORTS DO PROJETO CLINICOS
# ============================================

from app.core.config import settings
from app.core.database import get_service_client, SupabaseClient
from app.core.security import CurrentUser, require_permission

# LLM Provider
from .llm_providers import get_llm_provider

# Service e Schemas locais
from .service import criar_chat_service
from .schemas import (
    MensagemRequest,
    MensagemResponse,
    ConversaResponse,
    WebhookWhatsAppRequest
)


# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/chat", tags=["Chat LangGraph"])


# ============================================
# CONFIGURAÇÃO
# ============================================

# Clínica padrão para desenvolvimento (mesmo padrão do chat original)
DEFAULT_CLINICA_ID = getattr(settings, 'default_clinica_id', None) or "a9a6f406-3b46-4dab-b810-6c25d62f743b"


# ============================================
# DEPENDÊNCIAS
# ============================================

def get_db() -> SupabaseClient:
    """
    Retorna cliente Supabase usando o padrão do projeto.
    Usa service_client com wrapper SupabaseClient.
    """
    client = get_service_client()
    return SupabaseClient(client)


def get_chat_service_sync():
    """
    Retorna o ChatService configurado.
    """
    db = get_db()
    llm_client = get_llm_provider()
    return criar_chat_service(db, llm_client, settings)


async def get_chat_service():
    """
    Dependency que retorna o ChatService configurado.
    """
    return get_chat_service_sync()


def get_clinica_id(current_user: Optional[dict] = None) -> str:
    """Extrai clinica_id do usuário ou usa padrão"""
    if current_user:
        return current_user.get("clinica_id", DEFAULT_CLINICA_ID)
    return DEFAULT_CLINICA_ID


# ============================================
# ENDPOINTS PRINCIPAIS
# ============================================

@router.post("/mensagem", response_model=MensagemResponse)
async def processar_mensagem(
    request: MensagemRequest,
    current_user: CurrentUser = Depends(require_permission("chat", "C")),
    chat_service = Depends(get_chat_service)
):
    """
    Processa uma mensagem do paciente via WhatsApp.

    **Fluxo:**
    1. Identifica/cadastra paciente pelo telefone
    2. Cria card (lead) no primeiro contato
    3. Classifica intenção com LLM (Groq)
    4. Executa fluxo no grafo LangGraph
    5. Dispara webhooks Kestra se necessário
    6. Retorna resposta para enviar ao paciente
    """

    # Usa clinica_id do usuário autenticado
    clinica_id = current_user.clinica_id

    try:
        resultado = await chat_service.processar_mensagem(
            clinica_id=clinica_id,
            telefone=request.telefone,
            mensagem=request.mensagem,
            tipo_mensagem=request.tipo,
            midia_url=request.midia_url
        )

        return MensagemResponse(**resultado)

    except Exception as e:
        print(f"[ERROR] processar_mensagem: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


@router.post("/webhook/whatsapp")
async def webhook_whatsapp(
    payload: WebhookWhatsAppRequest,
    chat_service = Depends(get_chat_service)
):
    """
    Webhook para receber mensagens do Evolution API (WhatsApp).

    NOTA: Este endpoint é público (sem autenticação) pois recebe chamadas
    externas do Evolution API. Em produção, deve-se validar via chave secreta
    ou IP whitelist.
    """

    try:
        data = payload.data

        # Ignora mensagens enviadas por nós
        if data.get("key", {}).get("fromMe"):
            return {"status": "ignored", "reason": "message_from_me"}

        # Extrai telefone
        remote_jid = data.get("key", {}).get("remoteJid", "")
        telefone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

        # Extrai mensagem
        message = data.get("message", {})
        conteudo = (
            message.get("conversation") or
            message.get("extendedTextMessage", {}).get("text") or
            ""
        )

        if not conteudo:
            return {"status": "ignored", "reason": "no_text_content"}

        clinica_id = DEFAULT_CLINICA_ID

        resultado = await chat_service.processar_mensagem(
            clinica_id=clinica_id,
            telefone=telefone,
            mensagem=conteudo,
            tipo_mensagem="texto"
        )

        return {
            "status": "processed",
            "conversa_id": resultado.get("conversa_id"),
            "resposta": resultado.get("resposta")
        }

    except Exception as e:
        print(f"[ERROR] Webhook WhatsApp: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE CONSULTA
# ============================================

@router.get("/conversas", response_model=List[ConversaResponse])
async def listar_conversas(
    apenas_ativas: bool = Query(True, description="Apenas conversas ativas"),
    limite: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    current_user: CurrentUser = Depends(require_permission("chat", "L")),
    chat_service = Depends(get_chat_service)
):
    """Lista conversas da clínica."""

    # Usa clinica_id do usuário autenticado
    clinica_id = current_user.clinica_id

    try:
        conversas = await chat_service.listar_conversas(
            clinica_id=clinica_id,
            apenas_ativas=apenas_ativas,
            limite=limite
        )

        resultado = []
        for conv in conversas:
            resultado.append(ConversaResponse(
                telefone=conv.get("telefone"),
                paciente_id=conv.get("paciente_id"),
                paciente_nome=None,
                estado_atual=conv.get("ultimo_estado", ""),
                total_mensagens=0,
                ultima_mensagem=conv.get("updated_at"),
                mensagens=[]
            ))

        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversas/{telefone}", response_model=ConversaResponse)
async def get_conversa(
    telefone: str,
    current_user: CurrentUser = Depends(require_permission("chat", "L")),
    chat_service = Depends(get_chat_service)
):
    """Busca conversa específica pelo telefone."""

    # Usa clinica_id do usuário autenticado
    clinica_id = current_user.clinica_id

    try:
        conversa = await chat_service.get_conversa(telefone, clinica_id)

        if not conversa:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        mensagens = conversa.get("mensagens", [])

        return ConversaResponse(
            telefone=conversa.get("telefone"),
            paciente_id=conversa.get("paciente_id"),
            paciente_nome=None,
            estado_atual=conversa.get("ultimo_estado", ""),
            total_mensagens=len(mensagens),
            ultima_mensagem=conversa.get("updated_at"),
            mensagens=mensagens
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS UTILITÁRIOS
# ============================================

@router.get("/grafo")
async def get_grafo_visual(
    current_user: CurrentUser = Depends(require_permission("chat", "L")),
    chat_service = Depends(get_chat_service)
):
    """Retorna diagrama Mermaid do grafo LangGraph."""

    try:
        diagrama = chat_service.get_grafo_mermaid()
        return {
            "formato": "mermaid",
            "diagrama": diagrama
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(
    current_user: CurrentUser = Depends(require_permission("chat", "L"))
):
    """Verifica status do serviço de chat."""

    try:
        # Valida configuração
        db = get_db()
        llm = get_llm_provider()

        return {
            "status": "ok",
            "servico": "chat_langgraph",
            "versao": "1.0.0",
            "llm_provider": llm.get_provider_name(),
            "clinica_padrao": DEFAULT_CLINICA_ID
        }
    except Exception as e:
        return {
            "status": "error",
            "servico": "chat_langgraph",
            "erro": str(e)
        }


@router.get("/config")
async def get_config(
    current_user: CurrentUser = Depends(require_permission("chat", "L"))
):
    """
    Retorna configuração do chat para o frontend.
    Compatibilidade com o frontend existente.
    """
    try:
        llm = get_llm_provider()

        return {
            "llm_provider": llm.get_provider_name(),
            "model": getattr(llm, 'model', 'llama-3.3-70b-versatile'),
            "status": "ok",
            "versao": "1.0.0",
            "funcionalidades": {
                "agendamento": True,
                "funil_leads": True,
                "governanca": True,
                "multi_turno": True
            }
        }
    except Exception as e:
        return {
            "llm_provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "status": "ok",
            "versao": "1.0.0",
            "funcionalidades": {
                "agendamento": True,
                "funil_leads": True,
                "governanca": True,
                "multi_turno": True
            }
        }


# ============================================
# ENDPOINT DE TESTE (DESENVOLVIMENTO)
# ============================================

@router.post("/teste")
async def teste_interpretacao(
    mensagem: str = Query(..., description="Mensagem para testar"),
    current_user: CurrentUser = Depends(require_permission("chat", "C")),
    chat_service = Depends(get_chat_service)
):
    """
    Endpoint de teste para verificar interpretação do LLM.
    NÃO USAR EM PRODUÇÃO - apenas para debug.
    """

    try:
        resultado = await chat_service.processar_mensagem(
            clinica_id=current_user.clinica_id,
            telefone="00000000000",
            mensagem=mensagem
        )

        return {
            "mensagem": mensagem,
            "interpretacao": {
                "intencao": resultado.get("intencao"),
                "confianca": resultado.get("confianca"),
                "estado": resultado.get("estado")
            },
            "resposta": resultado.get("resposta")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
