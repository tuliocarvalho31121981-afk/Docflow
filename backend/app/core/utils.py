"""
Core - Utils
Funções utilitárias.
"""
import re
from datetime import date, datetime, timezone
from typing import Optional

import pytz


# Timezone Brasil
TZ_BRASILIA = pytz.timezone("America/Sao_Paulo")


def now_brasilia() -> datetime:
    """Retorna datetime atual no fuso de Brasília."""
    return datetime.now(TZ_BRASILIA)


def today_brasilia() -> date:
    """Retorna data atual no fuso de Brasília."""
    return now_brasilia().date()


def calculate_age(birth_date: date | str) -> int:
    """Calcula idade a partir da data de nascimento."""
    if isinstance(birth_date, str):
        birth_date = date.fromisoformat(birth_date)
    
    today = today_brasilia()
    age = today.year - birth_date.year
    
    # Ajusta se ainda não fez aniversário este ano
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age


def format_cpf(cpf: str) -> str:
    """
    Formata CPF removendo caracteres não numéricos.
    Retorna apenas os dígitos.
    """
    return re.sub(r"[^0-9]", "", cpf)


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF usando dígitos verificadores.
    Aceita CPF com ou sem formatação.
    """
    cpf = format_cpf(cpf)
    
    if len(cpf) != 11:
        return False
    
    # CPFs inválidos conhecidos
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Validação do segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2


def format_telefone(telefone: str) -> str:
    """
    Formata telefone removendo caracteres não numéricos.
    Remove código do país se presente.
    """
    telefone = re.sub(r"[^0-9]", "", telefone)
    
    # Remove código do país (55)
    if len(telefone) >= 12 and telefone.startswith("55"):
        telefone = telefone[2:]
    
    return telefone


def format_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ removendo caracteres não numéricos.
    """
    return re.sub(r"[^0-9]", "", cnpj)


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ usando dígitos verificadores.
    """
    cnpj = format_cnpj(cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # CNPJs inválidos conhecidos
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação do primeiro dígito
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Validação do segundo dígito
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cnpj[13]) == digito2


def mask_cpf(cpf: str) -> str:
    """Mascara CPF para logs: 123.***.**4-56"""
    cpf = format_cpf(cpf)
    if len(cpf) != 11:
        return cpf[:3] + "***"
    return f"{cpf[:3]}.***.**{cpf[8]}-{cpf[9:]}"


def mask_telefone(telefone: str) -> str:
    """Mascara telefone para logs: (11) ****-1234"""
    telefone = format_telefone(telefone)
    if len(telefone) < 8:
        return "****" + telefone[-4:]
    return f"****-{telefone[-4:]}"
