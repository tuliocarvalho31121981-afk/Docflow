"""
OpenRouter Client
Cliente unificado para IA via OpenRouter (compatível com OpenAI API).
Suporta: Chat, Vision, Transcription
"""

import base64
from typing import Optional, Union

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class OpenRouterClient:
    """Cliente para OpenRouter API."""

    def __init__(self):
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_app_url,
            "X-Title": settings.openrouter_app_name,
        }

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Envia mensagem para o modelo de chat.
        
        Args:
            messages: Lista de mensagens [{"role": "user", "content": "..."}]
            model: Modelo a usar (default: settings.openrouter_model_chat)
            temperature: Criatividade (0-1)
            max_tokens: Máximo de tokens na resposta
            system_prompt: Prompt de sistema opcional
            
        Returns:
            Resposta do modelo como string
        """
        model = model or settings.openrouter_model_chat
        
        # Adiciona system prompt se fornecido
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info("OpenRouter chat request", model=model, messages_count=len(messages))

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info("OpenRouter chat response", model=model, tokens=data.get("usage", {}))
        
        return content

    async def chat_with_vision(
        self,
        prompt: str,
        image_data: Union[str, bytes],
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Envia imagem para análise (OCR, descrição, etc).
        
        Args:
            prompt: Instrução para o modelo
            image_data: Base64 da imagem ou bytes
            model: Modelo a usar (default: settings.openrouter_model_vision)
            max_tokens: Máximo de tokens na resposta
            
        Returns:
            Análise da imagem como string
        """
        model = model or settings.openrouter_model_vision

        # Converte bytes para base64 se necessário
        if isinstance(image_data, bytes):
            image_data = base64.b64encode(image_data).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        },
                    },
                ],
            }
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        logger.info("OpenRouter vision request", model=model)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info("OpenRouter vision response", model=model)
        
        return content

    async def generate_soap(
        self,
        transcription: str,
        patient_context: Optional[str] = None,
    ) -> dict:
        """
        Gera nota SOAP a partir de transcrição de consulta.
        
        Args:
            transcription: Texto transcrito da consulta
            patient_context: Contexto do paciente (histórico, alergias, etc)
            
        Returns:
            Dict com S, O, A, P
        """
        system_prompt = """Você é um assistente médico especializado em gerar notas SOAP.
Analise a transcrição da consulta e gere uma nota SOAP estruturada.

Retorne APENAS um JSON válido no formato:
{
    "subjetivo": "Queixa principal e história...",
    "objetivo": "Exame físico e achados...",
    "avaliacao": "Diagnóstico ou hipótese diagnóstica...",
    "plano": "Tratamento, exames, retorno..."
}

Seja conciso e objetivo. Use terminologia médica apropriada."""

        user_message = f"Transcrição da consulta:\n\n{transcription}"
        
        if patient_context:
            user_message = f"Contexto do paciente:\n{patient_context}\n\n{user_message}"

        response = await self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            temperature=0.3,  # Mais determinístico para SOAP
        )

        # Tenta parsear JSON da resposta
        import json
        try:
            # Remove possíveis marcadores de código
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            
            return json.loads(clean_response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse SOAP JSON, returning raw")
            return {
                "subjetivo": response,
                "objetivo": "",
                "avaliacao": "",
                "plano": "",
            }

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "pt",
    ) -> str:
        """
        Transcreve áudio para texto.
        
        NOTA: OpenRouter não suporta Whisper diretamente.
        Use a API OpenAI direta para transcrição ou um serviço alternativo.
        
        Por enquanto, retorna erro indicando que precisa de integração separada.
        """
        # OpenRouter não tem endpoint de audio/transcription
        # Opções:
        # 1. Usar OpenAI diretamente para Whisper
        # 2. Usar Groq (tem Whisper grátis)
        # 3. Usar AssemblyAI
        # 4. Usar local Whisper
        
        raise NotImplementedError(
            "Transcrição de áudio requer integração separada. "
            "OpenRouter não suporta Whisper diretamente. "
            "Configure OPENAI_API_KEY ou use Groq/AssemblyAI."
        )

    async def extract_document_data(
        self,
        image_data: Union[str, bytes],
        document_type: str = "general",
    ) -> dict:
        """
        Extrai dados estruturados de documento (OCR inteligente).
        
        Args:
            image_data: Imagem do documento
            document_type: Tipo do documento (nf, receita, exame, guia, general)
            
        Returns:
            Dict com dados extraídos
        """
        prompts = {
            "nf": """Extraia os dados desta Nota Fiscal:
- Número da NF
- Data de emissão
- CNPJ emitente
- Razão social emitente
- Valor total
- Itens (lista com descrição e valor)
Retorne como JSON.""",
            
            "receita": """Extraia os dados desta receita médica:
- Nome do paciente
- Data
- Medicamentos (nome, dosagem, posologia)
- Nome do médico
- CRM
Retorne como JSON.""",
            
            "exame": """Extraia os dados deste resultado de exame:
- Tipo de exame
- Data
- Laboratório
- Resultados principais
- Valores de referência
Retorne como JSON.""",
            
            "guia": """Extraia os dados desta guia:
- Número da guia
- Tipo (SADT, internação, etc)
- Beneficiário
- Prestador
- Procedimentos
- Valores
Retorne como JSON.""",
            
            "general": """Extraia todas as informações relevantes deste documento.
Identifique o tipo de documento e extraia os dados estruturados.
Retorne como JSON.""",
        }

        prompt = prompts.get(document_type, prompts["general"])
        response = await self.chat_with_vision(prompt, image_data)

        # Tenta parsear JSON
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            
            return json.loads(clean_response)
        except json.JSONDecodeError:
            return {"raw_text": response, "parse_error": True}


# Singleton
openrouter_client = OpenRouterClient()
