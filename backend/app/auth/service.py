"""
Auth - Service
Lógica de autenticação via Supabase Auth.
"""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from typing import Any

import httpx
import jwt
import structlog
from fastapi import HTTPException, status
from jwt.algorithms import ECAlgorithm, RSAAlgorithm
from supabase import create_client

from app.core.config import settings
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    PerfilInfo,
    RefreshResponse,
    UserInfo,
    UserResponse,
)

logger = structlog.get_logger()

# Cache de clientes Supabase
_anon_client = None
_service_client = None

# Cache de chaves JWKS
_jwks_cache: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def _get_jwks_url() -> str:
    """Retorna a URL do JWKS do Supabase."""
    return f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


async def _fetch_jwks() -> dict[str, Any]:
    """Busca as chaves públicas JWKS do Supabase."""
    global _jwks_cache

    # Se já temos cache válido, retorna
    if _jwks_cache is not None:
        return _jwks_cache

    jwks_url = _get_jwks_url()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            logger.debug("JWKS carregado com sucesso", keys_count=len(_jwks_cache.get("keys", [])))
            return _jwks_cache
    except Exception as e:
        logger.error("Erro ao buscar JWKS", url=jwks_url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o token: serviço de autenticação indisponível"
        )


def _get_public_key_from_jwks(jwks: dict[str, Any], kid: str) -> Any:
    """Extrai a chave pública do JWKS baseado no kid (Key ID)."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Determina o algoritmo baseado no tipo de chave
            kty = key.get("kty")  # key type: RSA ou EC
            crv = key.get("crv")  # curve para EC (P-256, P-384, etc)

            if kty == "RSA":
                # Chave RSA
                return RSAAlgorithm.from_jwk(json.dumps(key))
            elif kty == "EC":
                # Chave EC (ECDSA)
                return ECAlgorithm.from_jwk(json.dumps(key))
            else:
                raise ValueError(f"Tipo de chave não suportado: {kty}")

    raise ValueError(f"Chave pública não encontrada para kid: {kid}")


async def validate_jwt_token(token: str) -> dict[str, Any]:
    """
    Valida um token JWT usando JWKS do Supabase.

    Retorna o payload do token se válido.
    Levanta exceção se o token for inválido ou expirado.

    Validações realizadas:
    - Assinatura JWT usando chave pública do JWKS
    - Expiração (exp)
    - Issuer (iss) - deve ser o endpoint auth do Supabase
    - Audience (aud) - deve ser "authenticated"

    Raises:
        HTTPException: Se o token for inválido, expirado ou malformado
    """
    try:
        # 1. Extrai o header sem validar (para pegar o kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg")

        if not kid:
            raise ValueError("Token JWT não contém 'kid' no header")

        if alg not in ["RS256", "ES256", "HS256"]:
            raise ValueError(f"Algoritmo JWT não suportado: {alg}")

        # 2. Busca JWKS (com cache)
        jwks = await _fetch_jwks()

        # 3. Obtém chave pública correspondente ao kid
        try:
            public_key = _get_public_key_from_jwks(jwks, kid)
        except ValueError as e:
            logger.warning("Chave pública não encontrada no JWKS", kid=kid, error=str(e))
            # Tenta limpar cache e buscar novamente (pode ter havido rotação de chaves)
            global _jwks_cache
            _jwks_cache = None
            _fetch_jwks.cache_clear()  # Limpa cache LRU
            jwks = await _fetch_jwks()
            public_key = _get_public_key_from_jwks(jwks, kid)

        # 4. Valida token com PyJWT
        # Para HS256 (legacy), usa o JWT secret
        if alg == "HS256":
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url}/auth/v1",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
        else:
            # Para RS256/ES256, usa a chave pública do JWKS
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url}/auth/v1",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )

        logger.debug(
            "Token JWT validado com sucesso",
            sub=payload.get("sub"),
            exp=payload.get("exp"),
            role=payload.get("role")
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token JWT inválido", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou malformado"
        )
    except Exception as e:
        logger.error("Erro ao validar token JWT", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao validar token"
        )


class AuthService:
    """Service para operações de autenticação."""

    def _get_anon_client(self):
        """Retorna cliente Supabase com chave anônima (para auth)."""
        global _anon_client
        if _anon_client is None:
            _anon_client = create_client(settings.supabase_url, settings.supabase_key)
        return _anon_client

    def _get_service_client(self):
        """Retorna cliente Supabase com service key (bypass RLS)."""
        global _service_client
        if _service_client is None:
            _service_client = create_client(settings.supabase_url, settings.supabase_service_key)
        return _service_client

    async def login(self, data: LoginRequest) -> LoginResponse:
        """
        Realiza login do usuário via Supabase Auth.
        Retorna tokens para autenticação nas demais rotas.
        """
        logger.info("Tentativa de login", email=data.email)

        supabase = self._get_anon_client()

        # Autentica via Supabase Auth
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.senha
            })
        except Exception as e:
            logger.warning("Falha na autenticação", email=data.email, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos"
            )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos"
            )

        # Busca dados completos (reutiliza método auxiliar)
        user_data, perfil_data, clinica_data = self._fetch_user_details(
            auth_response.user.id
        )

        # Verifica se usuário está ativo
        if not user_data.get("ativo"):
            logger.warning("Usuário inativo tentou login", user_id=user_data["id"])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )

        # Atualiza último acesso
        service_client = self._get_service_client()
        service_client.table("usuarios").update({
            "ultimo_acesso": datetime.utcnow().isoformat(),
            "primeiro_acesso": False
        }).eq("id", user_data["id"]).execute()

        logger.info("Login realizado com sucesso", user_id=user_data["id"])

        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in or 3600,
            user=UserResponse(
                id=str(user_data["id"]),
                nome=user_data["nome"],
                email=user_data["email"],
                tipo=user_data.get("tipo"),
                clinica_id=str(user_data["clinica_id"]),
                clinica_nome=clinica_data.get("nome", ""),
                perfil=PerfilInfo(
                    id=str(perfil_data.get("id", "")),
                    nome=perfil_data.get("nome", ""),
                    permissoes=perfil_data.get("permissoes", {})
                )
            )
        )

    async def refresh(self, refresh_token: str) -> RefreshResponse:
        """Renova o token usando refresh_token do Supabase."""
        logger.info("Renovando token")

        supabase = self._get_anon_client()

        try:
            auth_response = supabase.auth.refresh_session(refresh_token)
        except Exception as e:
            logger.warning("Falha ao renovar token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado"
            )

        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não foi possível renovar a sessão"
            )

        logger.info("Token renovado com sucesso")

        return RefreshResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in or 3600
        )

    async def get_current_user(self, token: str) -> UserInfo:
        """
        Retorna informações do usuário logado.

        Valida o token JWT usando JWKS do Supabase conforme documentação oficial:
        - Verifica assinatura com chave pública
        - Valida expiração (exp)
        - Valida issuer (iss)
        - Valida audience (aud)
        """
        # Valida token JWT usando JWKS (validação completa conforme Supabase)
        payload = await validate_jwt_token(token)

        # Extrai o user ID do campo 'sub' (subject)
        auth_user_id = payload.get("sub")
        if not auth_user_id:
            logger.warning("Token JWT válido mas sem campo 'sub'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: campo 'sub' não encontrado"
            )

        # Usa método auxiliar para buscar dados completos
        user_data, perfil_data, clinica_data = self._fetch_user_details(
            auth_user_id
        )

        return UserInfo(
            id=str(user_data["id"]),
            nome=user_data["nome"],
            email=user_data["email"],
            tipo=user_data.get("tipo"),
            clinica_id=str(user_data["clinica_id"]),
            clinica_nome=clinica_data.get("nome", ""),
            perfil=PerfilInfo(
                id=str(perfil_data.get("id", "")),
                nome=perfil_data.get("nome", ""),
                permissoes=perfil_data.get("permissoes", {})
            )
        )

    def _fetch_user_details(self, auth_user_id: str) -> tuple[dict, dict, dict]:
        """
        Busca dados completos do usuário (user, perfil, clinica).
        Método auxiliar para evitar duplicação de código.

        Returns:
            Tuple com (user_data, perfil_data, clinica_data)

        Raises:
            HTTPException se usuário não encontrado
        """
        service_client = self._get_service_client()

        # Busca usuário
        user_result = service_client.table("usuarios").select(
            "id, nome, email, tipo, clinica_id, perfil_id, ativo"
        ).eq("auth_user_id", auth_user_id).single().execute()

        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não cadastrado no sistema"
            )

        user_data = user_result.data

        # Busca perfil
        perfil_data = {}
        if user_data.get("perfil_id"):
            perfil_result = service_client.table("perfis").select(
                "id, nome, permissoes"
            ).eq("id", user_data["perfil_id"]).single().execute()
            if perfil_result.data:
                perfil_data = perfil_result.data

        # Busca clínica
        clinica_data = {}
        if user_data.get("clinica_id"):
            clinica_result = service_client.table("clinicas").select(
                "id, nome"
            ).eq("id", user_data["clinica_id"]).single().execute()
            if clinica_result.data:
                clinica_data = clinica_result.data

        return user_data, perfil_data, clinica_data


# Singleton
auth_service = AuthService()


# Dependency para FastAPI
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency do FastAPI para obter usuário atual.
    Uso: current_user: dict = Depends(get_current_user)
    """
    token = credentials.credentials
    user_info = await auth_service.get_current_user(token)

    # Retorna como dict para compatibilidade
    return {
        "id": user_info.id,
        "nome": user_info.nome,
        "email": user_info.email,
        "tipo": user_info.tipo,
        "clinica_id": user_info.clinica_id,
        "clinica_nome": user_info.clinica_nome,
        "perfil": {
            "id": user_info.perfil.id if user_info.perfil else None,
            "nome": user_info.perfil.nome if user_info.perfil else None,
            "permissoes": user_info.perfil.permissoes if user_info.perfil else {}
        }
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> dict | None:
    """
    Dependency opcional - retorna None se não autenticado.
    Útil para endpoints que funcionam com ou sem auth.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
