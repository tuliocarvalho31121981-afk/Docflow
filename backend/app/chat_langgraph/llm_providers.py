# app/chat_langgraph/llm_providers.py
"""
Abstração para provedores de LLM - ADAPTADO PARA CLINICOS

Permite trocar facilmente entre:
- OpenRouter (Claude Sonnet 4.5, GPT-4o, etc) - RECOMENDADO para agents
- Groq (LLaMA 3.3 70B) - GRÁTIS, mas function calling fraco
- DeepSeek (DeepSeek Chat) - Barato
- OpenAI (GPT-4o) - Pago, direto

Configurar via variável de ambiente:
LLM_PROVIDER=openrouter|groq|deepseek|openai

IMPORTANTE: Para agents com function calling, usar OpenRouter com Claude Sonnet 4.5
"""

import json
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

# Import das configurações do ClinicOS
try:
    from app.core.config import settings
except ImportError:
    # Fallback para desenvolvimento isolado
    from dataclasses import dataclass
    
    @dataclass
    class MockSettings:
        # OpenRouter (RECOMENDADO)
        openrouter_api_key: str = ""
        openrouter_model: str = "anthropic/claude-sonnet-4"
        
        # Groq (grátis mas function calling ruim)
        groq_api_key: str = ""
        groq_model: str = "llama-3.3-70b-versatile"
        
        # DeepSeek
        deepseek_api_key: str = ""
        deepseek_model: str = "deepseek-chat"
        
        # OpenAI direto
        openai_api_key: str = ""
        openai_model: str = "gpt-4o"
        
        # Provider padrão
        llm_provider: str = "openrouter"
    
    settings = MockSettings()
    print("[WARN] Usando MockSettings - configure app.core.config para produção")


class LLMResponse(BaseModel):
    """Resposta padronizada de qualquer LLM"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None


class BaseLLMProvider(ABC):
    """Interface base para provedores de LLM"""
    
    @property
    @abstractmethod
    def api_key(self) -> str:
        pass
    
    @property
    @abstractmethod
    def model(self) -> str:
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        pass
    
    @abstractmethod
    async def complete(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> LLMResponse:
        """Gera uma completion"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter API - Gateway para múltiplos modelos
    
    RECOMENDADO para agents com function calling!
    
    Modelos disponíveis (Janeiro 2026):
    - anthropic/claude-sonnet-4.5 (MELHOR para function calling)
    - anthropic/claude-sonnet-4 (muito bom)
    - openai/gpt-4o (alternativa)
    - openai/gpt-5 (mais caro)
    - google/gemini-2.5-flash (barato)
    
    Preços Claude Sonnet 4.5: $3/1M input, $15/1M output
    
    Obter API key em: https://openrouter.ai/keys
    """
    
    def __init__(self):
        self._api_key = getattr(settings, 'openrouter_api_key', None)
        if not self._api_key:
            raise ValueError(
                "OPENROUTER_API_KEY não configurada. "
                "Adicione ao .env: OPENROUTER_API_KEY=sk-or-v1-xxx"
            )
        self._base_url = "https://openrouter.ai/api/v1"
        self._model = getattr(settings, 'openrouter_model', 'anthropic/claude-sonnet-4')
    
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    async def complete(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://clinicos.app",  # Opcional: identificar app
                    "X-Title": "ClinicOS Agent"  # Opcional: nome do app
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0  # OpenRouter pode ser mais lento
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self._model,
                provider="openrouter",
                tokens_used=data.get("usage", {}).get("total_tokens")
            )
    
    def get_provider_name(self) -> str:
        return "openrouter"


class GroqProvider(BaseLLMProvider):
    """
    Groq API com LLaMA 3.3
    
    GRÁTIS: 14,400 requests/dia
    
    ⚠️ ATENÇÃO: Function calling é FRACO no Groq/LLaMA!
    Use apenas para chat simples, não para agents.
    
    Modelos disponíveis (Janeiro 2026):
    - llama-3.3-70b-versatile (padrão, mais capaz)
    - llama-3.1-8b-instant (mais rápido)
    
    NOTA: Modelos "tool-use-preview" foram descontinuados.
    """
    
    def __init__(self):
        self._api_key = getattr(settings, 'groq_api_key', None)
        if not self._api_key:
            raise ValueError(
                "GROQ_API_KEY não configurada. "
                "Adicione ao .env: GROQ_API_KEY=gsk_xxx"
            )
        self._base_url = "https://api.groq.com/openai/v1"
        self._model = getattr(settings, 'groq_model', 'llama-3.3-70b-versatile')
    
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    async def complete(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self._model,
                provider="groq",
                tokens_used=data.get("usage", {}).get("total_tokens")
            )
    
    def get_provider_name(self) -> str:
        return "groq"


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek API
    
    Barato: ~$0.14/1M tokens (input), ~$0.28/1M tokens (output)
    Modelo: deepseek-chat
    
    Boa alternativa para chat, function calling razoável.
    """
    
    def __init__(self):
        self._api_key = getattr(settings, 'deepseek_api_key', None)
        if not self._api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY não configurada. "
                "Adicione ao .env: DEEPSEEK_API_KEY=xxx"
            )
        self._base_url = "https://api.deepseek.com/v1"
        self._model = getattr(settings, 'deepseek_model', 'deepseek-chat')
    
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    async def complete(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self._model,
                provider="deepseek",
                tokens_used=data.get("usage", {}).get("total_tokens")
            )
    
    def get_provider_name(self) -> str:
        return "deepseek"


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API direta
    
    GPT-4o: ~$2.50/1M tokens (input), ~$10/1M tokens (output)
    
    Bom function calling, mas mais caro que OpenRouter.
    """
    
    def __init__(self):
        self._api_key = getattr(settings, 'openai_api_key', None)
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Adicione ao .env: OPENAI_API_KEY=sk-xxx"
            )
        self._base_url = "https://api.openai.com/v1"
        self._model = getattr(settings, 'openai_model', 'gpt-4o')
    
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def model(self) -> str:
        return self._model
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    async def complete(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self._model,
                provider="openai",
                tokens_used=data.get("usage", {}).get("total_tokens")
            )
    
    def get_provider_name(self) -> str:
        return "openai"


# ============================================
# FACTORY
# ============================================

_provider_instance: Optional[BaseLLMProvider] = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Retorna o provedor de LLM configurado.
    
    Configurar via LLM_PROVIDER env var:
    - openrouter (RECOMENDADO para agents)
    - groq (grátis, mas function calling fraco)
    - deepseek (barato)
    - openai (direto)
    
    Returns:
        Instância do provedor configurado
    
    Raises:
        ValueError: Se provedor inválido ou API key não configurada
    """
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    provider_name = getattr(settings, 'llm_provider', 'openrouter').lower()
    
    providers = {
        "openrouter": OpenRouterProvider,
        "groq": GroqProvider,
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(
            f"Provedor LLM inválido: {provider_name}. "
            f"Opções: {list(providers.keys())}"
        )
    
    _provider_instance = providers[provider_name]()
    print(f"[INFO] LLM Provider: {provider_name} ({_provider_instance.model})")
    
    return _provider_instance


def reset_provider():
    """Reset do provider (útil para testes)"""
    global _provider_instance
    _provider_instance = None


# ============================================
# HELPER PARA CLASSIFICAÇÃO DE INTENÇÃO
# ============================================

PROMPT_CLASSIFICACAO = """Você é um classificador de intenções para uma clínica médica.

Analise a mensagem e retorne APENAS a intenção, sem explicações.

INTENÇÕES POSSÍVEIS:
- AGENDAR: Quer marcar consulta
- REMARCAR: Quer mudar data/hora
- CANCELAR: Quer cancelar
- CONFIRMAR: Confirma consulta
- VALOR: Pergunta preço
- CONVENIO: Pergunta se aceita plano
- FAQ: Dúvida geral
- EXAMES: Enviar exames
- ANAMNESE: Preencher anamnese
- CHECK_IN: Chegou na clínica
- SAUDACAO: Só cumprimento
- DESPEDIDA: Tchau, obrigado
- DESCONHECIDO: Não conseguiu identificar

Retorne APENAS uma palavra da lista acima."""


async def classificar_intencao(mensagem: str, contexto: str = "") -> tuple[str, float]:
    """
    Classifica a intenção de uma mensagem.
    
    Args:
        mensagem: Mensagem do paciente
        contexto: Contexto adicional (nome, estado, etc)
    
    Returns:
        Tuple (intencao, confianca)
    """
    provider = get_llm_provider()
    
    user_message = f"{contexto}\n\nMensagem do paciente: {mensagem}" if contexto else mensagem
    
    try:
        response = await provider.complete(
            system_prompt=PROMPT_CLASSIFICACAO,
            user_message=user_message,
            temperature=0.1,
            max_tokens=50
        )
        
        intencao = response.content.strip().upper()
        
        # Valida se é uma intenção válida
        intencoes_validas = [
            "AGENDAR", "REMARCAR", "CANCELAR", "CONFIRMAR",
            "VALOR", "CONVENIO", "FAQ", "EXAMES", "ANAMNESE",
            "CHECK_IN", "SAUDACAO", "DESPEDIDA", "DESCONHECIDO"
        ]
        
        if intencao not in intencoes_validas:
            return "DESCONHECIDO", 0.0
        
        return intencao, 0.85  # TODO: extrair confiança real do LLM
        
    except Exception as e:
        print(f"[ERROR] Falha na classificação: {e}")
        return "DESCONHECIDO", 0.0
