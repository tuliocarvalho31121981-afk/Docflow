"""
Webhooks - WhatsApp
Recebe e processa mensagens do WhatsApp via Evolution API.

NOTA: Webhooks usam get_admin_db() porque são chamados externamente
sem contexto de usuário autenticado. Isso é uma exceção intencional.
"""

import hashlib
import hmac
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
import structlog

from app.core.config import settings
from app.core.database import get_admin_db
from app.integracoes.whatsapp.client import whatsapp_client

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verifica assinatura do webhook."""
    if not settings.webhook_secret:
        return True  # Skip se não configurado

    expected = hmac.new(
        settings.webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/whatsapp", summary="Webhook WhatsApp")
async def webhook_whatsapp(
    request: Request,
    x_webhook_secret: Optional[str] = Header(default=None)
):
    """
    Recebe mensagens do WhatsApp via Evolution API.
    
    Eventos tratados:
    - messages.upsert: Nova mensagem recebida
    - messages.update: Status de mensagem atualizado
    """
    body = await request.body()

    # Verifica assinatura (se configurado)
    if settings.webhook_secret and x_webhook_secret:
        if x_webhook_secret != settings.webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        logger.error("Payload inválido")
        return {"status": "error", "message": "Invalid JSON"}

    event = payload.get("event")
    instance = payload.get("instance")
    data = payload.get("data", {})

    logger.info("Webhook WhatsApp recebido", event=event, instance=instance)

    # Processa apenas mensagens recebidas
    if event == "messages.upsert":
        await process_incoming_message(data)
    elif event == "messages.update":
        # Status de mensagem enviada (entregue, lida, etc)
        logger.debug("Status atualizado", data=data)

    return {"status": "processed"}


async def process_incoming_message(data: dict):
    """Processa mensagem recebida do paciente."""
    key = data.get("key", {})
    message = data.get("message", {})
    
    # Ignora mensagens enviadas por nós
    if key.get("fromMe"):
        return

    # Extrai dados
    remote_jid = key.get("remoteJid", "")
    phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
    
    # Remove código do país se presente
    if phone.startswith("55") and len(phone) > 11:
        phone = phone[2:]

    message_id = key.get("id")
    timestamp = data.get("messageTimestamp")

    # Extrai conteúdo
    text = None
    media_type = None
    media_url = None

    if "conversation" in message:
        text = message["conversation"]
    elif "extendedTextMessage" in message:
        text = message["extendedTextMessage"].get("text")
    elif "imageMessage" in message:
        media_type = "image"
        media_url = message["imageMessage"].get("url")
        text = message["imageMessage"].get("caption")
    elif "documentMessage" in message:
        media_type = "document"
        media_url = message["documentMessage"].get("url")
        text = message["documentMessage"].get("caption")
    elif "audioMessage" in message:
        media_type = "audio"
        media_url = message["audioMessage"].get("url")

    logger.info(
        "Mensagem recebida",
        phone=phone[:4] + "****",
        text=text[:50] if text else None,
        media_type=media_type
    )

    # Busca paciente pelo telefone
    # Primeiro, precisamos identificar a clínica
    # Por enquanto, busca em todas (depois melhorar com multi-tenant)
    
    db = get_admin_db()
    pacientes = await db.select(
        table="pacientes",
        columns="id, clinica_id, nome, telefone",
        filters={"telefone": phone}
    )

    if not pacientes:
        # Paciente não cadastrado
        logger.info("Paciente não encontrado", phone=phone[:4] + "****")
        await whatsapp_client.send_text(
            phone,
            "Olá! Não encontramos seu cadastro em nosso sistema. "
            "Por favor, entre em contato com a clínica para se cadastrar."
        )
        return

    paciente = pacientes[0]
    clinica_id = paciente["clinica_id"]
    paciente_id = paciente["id"]
    paciente_nome = paciente["nome"]

    # Busca agendamento pendente do paciente
    agendamentos = await db.select(
        table="agendamentos",
        filters={
            "clinica_id": clinica_id,
            "paciente_id": paciente_id,
            "status": "agendado"
        },
        order_by="data"
    )

    agendamento = agendamentos[0] if agendamentos else None

    # Processa ação baseado no texto
    if text:
        text_upper = text.strip().upper()
        
        if text_upper in ("SIM", "S", "CONFIRMO", "1", "CONFIRMAR"):
            await handle_confirmacao(agendamento, paciente_nome, phone, clinica_id)
        
        elif text_upper in ("NAO", "NÃO", "CANCELAR", "2", "CANCELA"):
            await handle_cancelamento(agendamento, paciente_nome, phone, clinica_id)
        
        elif text_upper in ("REMARCAR", "REAGENDAR", "3"):
            await handle_remarcacao(agendamento, paciente_nome, phone, clinica_id)
        
        elif text_upper.isdigit() and 0 <= int(text_upper) <= 10:
            # Resposta de NPS
            await handle_nps(paciente_id, int(text_upper), clinica_id)
        
        else:
            # Mensagem genérica
            await handle_mensagem_generica(paciente_nome, phone, text, agendamento)

    # Processa mídia (exame enviado)
    if media_type and media_url:
        await handle_media(
            paciente_id=paciente_id,
            paciente_nome=paciente_nome,
            phone=phone,
            clinica_id=clinica_id,
            media_type=media_type,
            media_url=media_url,
            caption=text
        )

    # Registra mensagem no banco
    await db.insert(
        table="cards_mensagens",
        data={
            "clinica_id": clinica_id,
            "paciente_id": paciente_id,
            "card_id": None,  # Vincular depois se tiver card ativo
            "direcao": "recebida",
            "canal": "whatsapp",
            "conteudo": text or "[mídia]",
            "tipo": media_type or "texto",
            "metadata": {
                "message_id": message_id,
                "media_url": media_url
            }
        }
    )


async def handle_confirmacao(agendamento: dict, paciente_nome: str, phone: str, clinica_id: str):
    """Processa confirmação de consulta."""
    if not agendamento:
        await whatsapp_client.send_text(
            phone,
            f"Olá {paciente_nome}! Não encontramos nenhum agendamento pendente. "
            "Se você tem uma consulta agendada, entre em contato com a clínica."
        )
        return

    # Confirma agendamento (atualiza direto no banco)
    db = get_admin_db()
    await db.update(
        table="agendamentos",
        data={"status": "confirmado"},
        filters={"id": agendamento["id"]}
    )

    await whatsapp_client.send_text(
        phone,
        f"Perfeito, {paciente_nome}! ✅\n\n"
        f"Sua consulta está *confirmada* para {agendamento['data']} às {agendamento['hora_inicio']}.\n\n"
        "Até lá!"
    )

    logger.info("Agendamento confirmado via WhatsApp", agendamento_id=agendamento["id"])


async def handle_cancelamento(agendamento: dict, paciente_nome: str, phone: str, clinica_id: str):
    """Processa cancelamento de consulta."""
    if not agendamento:
        await whatsapp_client.send_text(
            phone,
            f"Olá {paciente_nome}! Não encontramos nenhum agendamento pendente para cancelar."
        )
        return

    # Cancela agendamento (atualiza direto no banco)
    db = get_admin_db()
    await db.update(
        table="agendamentos",
        data={
            "status": "cancelado",
            "motivo_cancelamento": "Cancelado pelo paciente via WhatsApp"
        },
        filters={"id": agendamento["id"]}
    )

    await whatsapp_client.send_text(
        phone,
        f"Entendido, {paciente_nome}.\n\n"
        "Sua consulta foi *cancelada*.\n\n"
        "Se precisar agendar novamente, entre em contato conosco."
    )

    logger.info("Agendamento cancelado via WhatsApp", agendamento_id=agendamento["id"])


async def handle_remarcacao(agendamento: dict, paciente_nome: str, phone: str, clinica_id: str):
    """Processa solicitação de remarcação."""
    await whatsapp_client.send_text(
        phone,
        f"Entendido, {paciente_nome}!\n\n"
        "Para remarcar sua consulta, nossa equipe entrará em contato "
        "para verificar os horários disponíveis.\n\n"
        "Você também pode ligar diretamente para a clínica."
    )

    # Notifica equipe (criar notificação no sistema)
    db = get_admin_db()
    await db.insert(
        table="notificacoes",
        data={
            "clinica_id": clinica_id,
            "tipo": "remarcacao_solicitada",
            "titulo": "Solicitação de Remarcação",
            "mensagem": f"Paciente {paciente_nome} solicitou remarcação via WhatsApp",
            "perfil_destino": "Recepção",
            "prioridade": "media",
            "dados": {
                "agendamento_id": agendamento["id"] if agendamento else None,
                "paciente_nome": paciente_nome,
                "telefone": phone
            }
        }
    )

    logger.info("Remarcação solicitada via WhatsApp", paciente=paciente_nome)


async def handle_nps(paciente_id: str, nota: int, clinica_id: str):
    """Registra resposta de NPS."""
    db = get_admin_db()
    await db.insert(
        table="pesquisas_satisfacao",
        data={
            "clinica_id": clinica_id,
            "paciente_id": paciente_id,
            "nota_nps": nota,
            "origem": "whatsapp"
        }
    )

    logger.info("NPS registrado", paciente_id=paciente_id, nota=nota)


async def handle_mensagem_generica(paciente_nome: str, phone: str, text: str, agendamento: dict):
    """Resposta para mensagens não reconhecidas."""
    if agendamento:
        await whatsapp_client.send_text(
            phone,
            f"Olá {paciente_nome}! 👋\n\n"
            f"Você tem uma consulta agendada para {agendamento['data']} às {agendamento['hora']}.\n\n"
            "Responda:\n"
            "✅ *SIM* - Para confirmar\n"
            "❌ *CANCELAR* - Para cancelar\n"
            "🔄 *REMARCAR* - Para remarcar\n\n"
            "Para outras questões, entre em contato com a clínica."
        )
    else:
        await whatsapp_client.send_text(
            phone,
            f"Olá {paciente_nome}! 👋\n\n"
            "Não entendi sua mensagem. "
            "Para falar com a clínica, aguarde que nossa equipe irá responder."
        )


async def handle_media(
    paciente_id: str,
    paciente_nome: str,
    phone: str,
    clinica_id: str,
    media_type: str,
    media_url: str,
    caption: Optional[str]
):
    """Processa mídia recebida (provavelmente exame)."""
    logger.info("Mídia recebida", paciente_id=paciente_id, media_type=media_type)

    # Registra como documento do paciente
    db = get_admin_db()
    await db.insert(
        table="pacientes_documentos",
        data={
            "clinica_id": clinica_id,
            "paciente_id": paciente_id,
            "tipo": "exame",
            "descricao": caption or "Exame enviado via WhatsApp",
            "arquivo_url": media_url,
            "origem": "whatsapp",
            "status": "pendente_analise"
        }
    )

    # Confirma recebimento
    await whatsapp_client.send_template(
        phone,
        "exame_recebido",
        {"paciente_nome": paciente_nome}
    )

    # Notifica equipe
    await db.insert(
        table="notificacoes",
        data={
            "clinica_id": clinica_id,
            "tipo": "exame_recebido",
            "titulo": "Novo Exame Recebido",
            "mensagem": f"Paciente {paciente_nome} enviou exame via WhatsApp",
            "perfil_destino": "Médico",
            "prioridade": "baixa",
            "dados": {
                "paciente_id": paciente_id,
                "media_url": media_url
            }
        }
    )
