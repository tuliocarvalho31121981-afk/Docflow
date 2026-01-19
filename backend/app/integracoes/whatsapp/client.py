"""
WhatsApp Client
Integração com Evolution API para envio de mensagens.
"""

from typing import Optional

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import IntegrationError

logger = structlog.get_logger()


class WhatsAppClient:
    """Cliente para Evolution API (WhatsApp)."""

    def __init__(self):
        self.base_url = settings.evolution_api_url
        self.api_key = settings.evolution_api_key
        self.instance = settings.evolution_instance

    @property
    def headers(self) -> dict:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def _format_phone(self, phone: str) -> str:
        """Formata telefone para o padrão do WhatsApp."""
        # Remove caracteres não numéricos
        phone = "".join(filter(str.isdigit, phone))
        
        # Adiciona código do Brasil se não tiver
        if len(phone) == 11:  # DDD + número
            phone = f"55{phone}"
        elif len(phone) == 10:  # DDD + número fixo
            phone = f"55{phone}"
        
        return phone

    async def send_text(
        self,
        to: str,
        message: str,
        delay: int = 1000
    ) -> dict:
        """
        Envia mensagem de texto.
        
        Args:
            to: Número do destinatário
            to: Texto da mensagem
            delay: Delay em ms antes de enviar (simula digitação)
        """
        if not self.base_url:
            logger.warning("WhatsApp não configurado")
            return {"status": "not_configured"}

        phone = self._format_phone(to)
        
        logger.info("Enviando WhatsApp", to=phone[:8] + "****", preview=message[:50])

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/message/sendText/{self.instance}",
                    headers=self.headers,
                    json={
                        "number": phone,
                        "text": message,
                        "delay": delay
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("WhatsApp enviado", message_id=result.get("key", {}).get("id"))
                return result

        except httpx.HTTPError as e:
            logger.error("Erro ao enviar WhatsApp", error=str(e))
            raise IntegrationError("WhatsApp", str(e))

    async def send_template(
        self,
        to: str,
        template_name: str,
        variables: dict
    ) -> dict:
        """
        Envia mensagem usando template.
        
        Templates disponíveis:
        - confirmacao_consulta
        - lembrete_d1
        - anamnese_link
        - pesquisa_nps
        """
        templates = {
            "confirmacao_consulta": (
                "Olá {paciente_nome}! 👋\n\n"
                "Sua consulta está agendada:\n\n"
                "📅 *Data:* {data}\n"
                "🕐 *Horário:* {hora}\n"
                "👨‍⚕️ *Médico:* {medico_nome}\n\n"
                "Por favor, confirme sua presença respondendo:\n"
                "✅ *SIM* - Confirmo minha consulta\n"
                "❌ *CANCELAR* - Preciso cancelar\n"
                "🔄 *REMARCAR* - Preciso remarcar\n\n"
                "Qualquer dúvida, estamos à disposição!"
            ),
            "lembrete_d1": (
                "Olá {paciente_nome}! 👋\n\n"
                "Lembrete: sua consulta é *amanhã*!\n\n"
                "📅 *Data:* {data}\n"
                "🕐 *Horário:* {hora}\n"
                "👨‍⚕️ *Médico:* {medico_nome}\n\n"
                "Não se esqueça de trazer seus documentos e exames.\n\n"
                "Até amanhã! 😊"
            ),
            "anamnese_link": (
                "Olá {paciente_nome}! 👋\n\n"
                "Para agilizar seu atendimento, pedimos que preencha "
                "um breve questionário antes da consulta:\n\n"
                "🔗 {link}\n\n"
                "Leva apenas alguns minutos e nos ajuda a te atender melhor!\n\n"
                "Sua consulta: {data} às {hora}"
            ),
            "pesquisa_nps": (
                "Olá {paciente_nome}! 👋\n\n"
                "Obrigado por sua visita hoje!\n\n"
                "Gostaríamos de saber: de 0 a 10, qual a chance de você "
                "recomendar nossa clínica para amigos e familiares?\n\n"
                "Responda com um número de 0 a 10.\n\n"
                "Sua opinião é muito importante para nós! 💙"
            ),
            "exame_recebido": (
                "Olá {paciente_nome}! 👋\n\n"
                "Recebemos seu exame! ✅\n\n"
                "Nosso médico irá analisar e você será avisado se houver alguma "
                "orientação antes da sua consulta.\n\n"
                "Obrigado por enviar!"
            ),
            "falta_registrada": (
                "Olá {paciente_nome}.\n\n"
                "Sentimos sua falta na consulta de hoje às {hora}.\n\n"
                "Se precisar remarcar, entre em contato conosco.\n\n"
                "Esperamos vê-lo em breve!"
            ),
        }

        template = templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' não encontrado")

        message = template.format(**variables)
        return await self.send_text(to, message)

    async def send_media(
        self,
        to: str,
        media_url: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> dict:
        """
        Envia mídia (imagem, documento, áudio).
        
        Args:
            to: Número do destinatário
            media_url: URL da mídia
            media_type: image, document, audio, video
            caption: Legenda (opcional)
            filename: Nome do arquivo (para documentos)
        """
        if not self.base_url:
            logger.warning("WhatsApp não configurado")
            return {"status": "not_configured"}

        phone = self._format_phone(to)
        
        endpoint_map = {
            "image": "sendImage",
            "document": "sendDocument",
            "audio": "sendAudio",
            "video": "sendVideo"
        }
        
        endpoint = endpoint_map.get(media_type, "sendDocument")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "number": phone,
                    "mediaUrl": media_url
                }
                
                if caption:
                    payload["caption"] = caption
                if filename:
                    payload["fileName"] = filename

                response = await client.post(
                    f"{self.base_url}/message/{endpoint}/{self.instance}",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error("Erro ao enviar mídia WhatsApp", error=str(e))
            raise IntegrationError("WhatsApp", str(e))

    async def check_number(self, phone: str) -> dict:
        """Verifica se número está registrado no WhatsApp."""
        if not self.base_url:
            return {"exists": False, "reason": "not_configured"}

        phone = self._format_phone(phone)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/whatsappNumbers/{self.instance}",
                    headers=self.headers,
                    json={"numbers": [phone]},
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result and len(result) > 0:
                    return {
                        "exists": result[0].get("exists", False),
                        "jid": result[0].get("jid")
                    }
                
                return {"exists": False}

        except httpx.HTTPError as e:
            logger.error("Erro ao verificar número", error=str(e))
            return {"exists": False, "error": str(e)}


# Singleton
whatsapp_client = WhatsAppClient()
