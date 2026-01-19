"""
Groq Client
Cliente para transcrição de áudio via Groq (Whisper).
Grátis e ~10x mais rápido que OpenAI.
"""

import tempfile
from pathlib import Path
from typing import Optional, Union

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class GroqClient:
    """Cliente para Groq API (Whisper)."""

    def __init__(self):
        self.base_url = "https://api.groq.com/openai/v1"
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model_whisper

    async def transcribe(
        self,
        audio_data: Union[bytes, str, Path],
        language: str = "pt",
        prompt: Optional[str] = None,
        response_format: str = "text",
    ) -> str:
        """
        Transcreve áudio para texto usando Whisper via Groq.
        
        Args:
            audio_data: Bytes do áudio, path do arquivo, ou base64
            language: Código do idioma (pt, en, es, etc)
            prompt: Texto opcional para guiar a transcrição
            response_format: Formato da resposta (text, json, verbose_json, srt, vtt)
            
        Returns:
            Texto transcrito
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não configurada")

        # Prepara o arquivo de áudio
        if isinstance(audio_data, (str, Path)):
            # É um path de arquivo
            file_path = Path(audio_data)
            if not file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            audio_bytes = file_path.read_bytes()
            filename = file_path.name
        elif isinstance(audio_data, bytes):
            audio_bytes = audio_data
            filename = "audio.mp3"
        else:
            raise ValueError("audio_data deve ser bytes, str ou Path")

        # Detecta formato pelo magic number ou extensão
        content_type = self._detect_content_type(audio_bytes, filename)

        logger.info(
            "Groq transcription request",
            model=self.model,
            language=language,
            file_size=len(audio_bytes),
            content_type=content_type,
        )

        # Monta o form-data
        files = {
            "file": (filename, audio_bytes, content_type),
        }
        data = {
            "model": self.model,
            "language": language,
            "response_format": response_format,
        }
        if prompt:
            data["prompt"] = prompt

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()

        if response_format == "text":
            result = response.text
        else:
            result = response.json()

        logger.info(
            "Groq transcription complete",
            model=self.model,
            result_length=len(str(result)),
        )

        return result

    async def transcribe_with_timestamps(
        self,
        audio_data: Union[bytes, str, Path],
        language: str = "pt",
    ) -> dict:
        """
        Transcreve áudio com timestamps detalhados.
        
        Returns:
            Dict com texto, segments e timestamps
        """
        result = await self.transcribe(
            audio_data=audio_data,
            language=language,
            response_format="verbose_json",
        )
        return result

    async def transcribe_to_srt(
        self,
        audio_data: Union[bytes, str, Path],
        language: str = "pt",
    ) -> str:
        """
        Transcreve áudio e retorna legendas em formato SRT.
        
        Returns:
            String no formato SRT
        """
        result = await self.transcribe(
            audio_data=audio_data,
            language=language,
            response_format="srt",
        )
        return result

    def _detect_content_type(self, data: bytes, filename: str) -> str:
        """Detecta o content-type do áudio."""
        # Por extensão
        ext = Path(filename).suffix.lower()
        ext_map = {
            ".mp3": "audio/mpeg",
            ".mp4": "audio/mp4",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg",
            ".oga": "audio/ogg",
            ".flac": "audio/flac",
        }
        if ext in ext_map:
            return ext_map[ext]

        # Por magic number
        if data[:3] == b"ID3" or data[:2] == b"\xff\xfb":
            return "audio/mpeg"
        if data[:4] == b"RIFF":
            return "audio/wav"
        if data[:4] == b"fLaC":
            return "audio/flac"
        if data[:4] == b"OggS":
            return "audio/ogg"

        # Default
        return "audio/mpeg"


# Singleton
groq_client = GroqClient()
