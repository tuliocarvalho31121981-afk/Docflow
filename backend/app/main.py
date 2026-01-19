"""
Sistema de Gestão de Clínicas - API Backend
FastAPI Application

Versão: 1.3.0
Atualizado: Janeiro 2026
- Adicionado Chat LangGraph (Sprint 5 - Fase 0)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.exceptions import AppException

# =============================================================================
# ROUTERS
# =============================================================================

# Core
from app.auth.router import router as auth_router
from app.clinicas.router import router as clinicas_router
from app.usuarios.router import router as usuarios_router

# Módulos principais
from app.pacientes.router import router as pacientes_router
from app.agenda.router import router as agenda_router
from app.cards.router import router as cards_router
from app.evidencias.router import router as evidencias_router
from app.prontuario.router import router as prontuario_router
from app.modelos_documentos.router import router as modelos_documentos_router

# Chat - ESCOLHA UMA DAS OPÇÕES ABAIXO:

# OPÇÃO 1: Chat atual (stateless)
# from app.chat.router import router as chat_router

# OPÇÃO 2: Chat LangGraph (stateful - RECOMENDADO para Sprint 5+)
from app.chat_langgraph.router import router as chat_router

# Governança (se existir)
try:
    from app.governanca.router import router as governanca_router
    GOVERNANCA_DISPONIVEL = True
except ImportError:
    GOVERNANCA_DISPONIVEL = False

# Webhooks
from app.webhooks.whatsapp import router as whatsapp_router

logger = structlog.get_logger()


# =============================================================================
# LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle do app - startup e shutdown."""
    # Startup
    logger.info(
        "Iniciando aplicação",
        environment=settings.app_env,
        debug=settings.app_debug,
        version="1.3.0"
    )

    # Log do provedor LLM configurado
    llm_provider = getattr(settings, 'llm_provider', 'groq')
    logger.info(f"LLM Provider: {llm_provider}")

    yield

    # Shutdown
    logger.info("Encerrando aplicação")


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="Sistema de Gestão de Clínicas - ClinicOS",
    description="""
API para gestão de clínicas médicas com:
- Agendamento inteligente via WhatsApp
- Funil de leads (Fase 0)
- Governança com validação humana
- Chat com LangGraph (estado persistente)
    """,
    version="1.3.0",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
    lifespan=lifespan
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handler para exceções da aplicação."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.to_dict()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções não tratadas."""
    logger.error("Erro não tratado", error=str(exc), path=request.url.path)

    if settings.app_debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": str(exc)
                }
            }
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "Erro interno do servidor"
            }
        }
    )


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica se a API está funcionando."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "1.3.0",
        "chat_engine": "langgraph"
    }


# =============================================================================
# REGISTRA ROUTERS
# =============================================================================

# Core
app.include_router(auth_router, prefix="/v1")
app.include_router(clinicas_router, prefix="/v1")
app.include_router(usuarios_router, prefix="/v1")

# Módulos principais
app.include_router(pacientes_router, prefix="/v1")
app.include_router(agenda_router, prefix="/v1")
app.include_router(cards_router, prefix="/v1")
app.include_router(evidencias_router, prefix="/v1")
app.include_router(prontuario_router, prefix="/v1")
app.include_router(modelos_documentos_router, prefix="/v1")

# Chat (LangGraph)
app.include_router(chat_router, prefix="/v1")

# Governança (se disponível)
if GOVERNANCA_DISPONIVEL:
    app.include_router(governanca_router, prefix="/v1")

# Webhooks
app.include_router(whatsapp_router, prefix="/v1")


# =============================================================================
# ROOT
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Rota raiz."""
    return {
        "name": "ClinicOS API",
        "version": "1.3.0",
        "description": "Sistema de Gestão de Clínicas",
        "docs": "/docs" if settings.app_debug else None,
        "modules": {
            "auth": "/v1/auth",
            "clinicas": "/v1/clinicas",
            "usuarios": "/v1/usuarios",
            "pacientes": "/v1/pacientes",
            "agenda": "/v1/agenda",
            "cards": "/v1/cards",
            "prontuario": "/v1/prontuario",
            "modelos_documentos": "/v1/modelos-documentos",
            "chat": "/v1/chat",
            "governanca": "/v1/governanca" if GOVERNANCA_DISPONIVEL else None
        }
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_debug
    )
