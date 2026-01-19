"""
DocFlow - Importação de Pacientes
Importa pacientes do CSV para o Supabase
"""

import csv
import re
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Carrega variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

CLINICA_ID = "0773158f-5c18-4c07-91ef-1da9763e5eb0"
CSV_FILE = "import.csv"

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def limpar_cpf(cpf: str) -> str:
    """Remove formatação do CPF."""
    if not cpf:
        return None
    cpf_limpo = re.sub(r'[^\d]', '', str(cpf))
    return cpf_limpo if len(cpf_limpo) == 11 else None


def limpar_telefone(telefone: str) -> str:
    """Limpa e formata telefone."""
    if not telefone:
        return None
    # Remove tudo que não é número
    numeros = re.sub(r'[^\d]', '', str(telefone))
    if len(numeros) < 8:
        return None
    # Adiciona DDD 21 se não tiver
    if len(numeros) == 8:
        numeros = "21" + numeros
    if len(numeros) == 9:
        numeros = "21" + numeros
    return numeros[:11] if len(numeros) >= 10 else None


def parse_data(data_str: str) -> str:
    """Converte data do formato BR para ISO."""
    if not data_str:
        return None
    try:
        # Tenta formato DD/MM/YYYY HH:MM:SS
        if ' ' in data_str:
            dt = datetime.strptime(data_str.strip(), "%d/%m/%Y %H:%M:%S")
        else:
            dt = datetime.strptime(data_str.strip(), "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return None


def limpar_texto(texto: str) -> str:
    """Limpa texto removendo espaços extras."""
    if not texto:
        return None
    texto = str(texto).strip()
    return texto if texto else None


def limpar_cep(cep: str) -> str:
    """Remove formatação do CEP."""
    if not cep:
        return None
    cep_limpo = re.sub(r'[^\d]', '', str(cep))
    return cep_limpo if len(cep_limpo) == 8 else None


def limpar_rg(rg: str) -> str:
    """Limpa RG."""
    if not rg:
        return None
    rg_limpo = re.sub(r'[^\dXx]', '', str(rg))
    return rg_limpo if rg_limpo else None


# =============================================================================
# MAPEAMENTO CSV -> BANCO
# =============================================================================

def mapear_paciente(row: dict) -> dict:
    """Mapeia uma linha do CSV para o formato do banco."""

    # Telefone: pega celular primeiro, depois fixo
    telefone = limpar_telefone(row.get('Celular')) or limpar_telefone(row.get('Telefone_Residencial'))
    telefone_sec = limpar_telefone(row.get('Telefone_Residencial')) if limpar_telefone(row.get('Celular')) else limpar_telefone(row.get('Telefone_Residencial_1'))

    return {
        'clinica_id': CLINICA_ID,
        'nome': limpar_texto(row.get('Nome')),
        'nome_social': limpar_texto(row.get('Nome_Social')),
        'cpf': limpar_cpf(row.get('CPF_CGC')),
        'data_nascimento': parse_data(row.get('Nascimento')),
        'telefone': telefone,
        'telefone_secundario': telefone_sec,
        'email': limpar_texto(row.get('Email')),
        'aceita_whatsapp': True if telefone else False,
        'status': 'ativo',
    }

# =============================================================================
# IMPORTAÇÃO
# =============================================================================

def importar_pacientes():
    """Importa pacientes do CSV para o Supabase."""

    print("=" * 60)
    print("DocFlow - Importação de Pacientes")
    print("=" * 60)

    # Conecta ao Supabase
    print("\n[1] Conectando ao Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("    ✓ Conectado!")

    # Lê o CSV
    print(f"\n[2] Lendo arquivo {CSV_FILE}...")
    pacientes = []
    cpfs_vistos = set()  # Para evitar duplicatas

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            paciente = mapear_paciente(row)

            # Ignora se não tem nome
            if not paciente['nome']:
                continue

            # Ignora duplicatas por CPF
            if paciente['cpf']:
                if paciente['cpf'] in cpfs_vistos:
                    continue
                cpfs_vistos.add(paciente['cpf'])

            # Remove campos None para não dar erro
            paciente = {k: v for k, v in paciente.items() if v is not None}

            pacientes.append(paciente)

            if (i + 1) % 5000 == 0:
                print(f"    Processados: {i + 1} linhas...")

    print(f"    ✓ {len(pacientes)} pacientes válidos encontrados")

    # Insere em lotes
    print("\n[3] Inserindo no Supabase...")
    BATCH_SIZE = 500
    total_inseridos = 0
    erros = 0

    for i in range(0, len(pacientes), BATCH_SIZE):
        batch = pacientes[i:i + BATCH_SIZE]
        try:
            result = supabase.table('pacientes').insert(batch).execute()
            total_inseridos += len(batch)
            print(f"    Inseridos: {total_inseridos}/{len(pacientes)}")
        except Exception as e:
            erros += len(batch)
            print(f"    ✗ Erro no lote {i}-{i+BATCH_SIZE}: {e}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA IMPORTAÇÃO")
    print("=" * 60)
    print(f"Total no CSV:      {len(pacientes)}")
    print(f"Inseridos:         {total_inseridos}")
    print(f"Erros:             {erros}")
    print("=" * 60)


if __name__ == "__main__":
    importar_pacientes()
