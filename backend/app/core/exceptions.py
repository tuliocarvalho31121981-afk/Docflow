"""
Core - Exceptions
Exceções customizadas da aplicação.
"""
from typing import Optional


class AppException(Exception):
    """Exceção base da aplicação."""
    
    def __init__(
        self, 
        code: str, 
        message: str, 
        status_code: int = 400,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            **self.details
        }


class NotFoundError(AppException):
    """Recurso não encontrado."""
    
    def __init__(self, resource: str, id: str):
        super().__init__(
            code="not_found",
            message=f"{resource} não encontrado(a)",
            status_code=404,
            details={"resource": resource, "id": id}
        )


class ValidationError(AppException):
    """Erro de validação."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            code="validation_error",
            message=message,
            status_code=400,
            details={"field": field} if field else {}
        )


class ConflictError(AppException):
    """Conflito (recurso já existe)."""
    
    def __init__(self, field: str, value: str):
        super().__init__(
            code="conflict",
            message=f"Já existe um registro com {field}: {value}",
            status_code=409,
            details={"field": field, "value": value}
        )


class UnauthorizedError(AppException):
    """Não autorizado."""
    
    def __init__(self, message: str = "Não autorizado"):
        super().__init__(
            code="unauthorized",
            message=message,
            status_code=401
        )


class ForbiddenError(AppException):
    """Acesso negado."""
    
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(
            code="forbidden",
            message=message,
            status_code=403
        )


class InvalidStatusTransitionError(AppException):
    """Transição de status inválida."""
    
    def __init__(self, current: str, target: str):
        super().__init__(
            code="invalid_status_transition",
            message=f"Não é possível mudar de '{current}' para '{target}'",
            status_code=400,
            details={"current": current, "target": target}
        )


class SlotUnavailableError(AppException):
    """Horário não disponível."""
    
    def __init__(self, message: str = "Horário não disponível"):
        super().__init__(
            code="slot_unavailable",
            message=message,
            status_code=409
        )


class EvidenceRequiredError(AppException):
    """Evidência obrigatória não encontrada."""

    def __init__(self, action: str, missing: list[str], message: str = ""):
        super().__init__(
            code="evidence_required",
            message=message or f"Evidências necessárias para '{action}' não encontradas",
            status_code=400,
            details={"action": action, "missing": missing}
        )


class IntegrationError(AppException):
    """Erro de integração com serviço externo."""

    def __init__(self, service: str, message: str, details: Optional[dict] = None):
        super().__init__(
            code="integration_error",
            message=f"Erro na integração com {service}: {message}",
            status_code=502,
            details={"service": service, **(details or {})}
        )
