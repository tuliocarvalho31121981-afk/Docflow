"""
Script de Teste - API DocFlow
Testa todos os endpoints da API com autenticação real.

Uso:
    python test_api.py

Requisitos:
    pip install requests python-dotenv
"""

import os
import sys
import json
from datetime import date, timedelta
from typing import Optional
from uuid import uuid4

import requests
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8080/v1")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Credenciais de teste (criar usuário no Supabase primeiro)
TEST_EMAIL = os.getenv("TEST_EMAIL", "tuliocarvalho31121981@gmail.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "aloha123")

# Cores para output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_test(method: str, endpoint: str, status: int, success: bool, msg: str = ""):
    color = Colors.GREEN if success else Colors.RED
    icon = "✓" if success else "✗"
    method_color = {
        "GET": Colors.CYAN,
        "POST": Colors.GREEN,
        "PATCH": Colors.YELLOW,
        "DELETE": Colors.RED,
        "PUT": Colors.YELLOW
    }.get(method, Colors.END)

    print(f"{color}{icon}{Colors.END} [{method_color}{method:6}{Colors.END}] {endpoint:45} → {status} {msg}")


def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {text}{Colors.END}")
    print("-" * 50)


# =============================================================================
# CLASSE DE TESTE
# =============================================================================

class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.headers: dict = {}
        self.results = {"passed": 0, "failed": 0, "skipped": 0}

        # IDs criados durante os testes
        self.paciente_id: Optional[str] = None
        self.agendamento_id: Optional[str] = None
        self.card_id: Optional[str] = None
        self.perfil_id: Optional[str] = None
        self.evidencia_id: Optional[str] = None
        self.medico_id: Optional[str] = None
        self.tipo_consulta_id: Optional[str] = None

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
        expected_status: list = [200, 201],
        description: str = ""
    ) -> tuple[bool, dict]:
        """Faz requisição e retorna (sucesso, response_data)."""
        url = f"{BASE_URL}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self.headers,
                timeout=30
            )

            success = response.status_code in expected_status

            if success:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

            # Parse response
            try:
                resp_data = response.json()
            except:
                resp_data = {"raw": response.text}

            # Print result
            msg = description if description else ""
            if not success:
                error_msg = resp_data.get("error", {}).get("message", "")[:50]
                if error_msg:
                    msg = f"- {error_msg}"

            print_test(method, endpoint, response.status_code, success, msg)

            return success, resp_data

        except requests.exceptions.ConnectionError:
            self.results["failed"] += 1
            print_test(method, endpoint, 0, False, "- Connection refused")
            return False, {}
        except Exception as e:
            self.results["failed"] += 1
            print_test(method, endpoint, 0, False, f"- {str(e)[:40]}")
            return False, {}

    def skip(self, method: str, endpoint: str, reason: str):
        """Marca teste como pulado."""
        self.results["skipped"] += 1
        print(f"{Colors.YELLOW}○{Colors.END} [{method:6}] {endpoint:45} → SKIP - {reason}")

    # =========================================================================
    # TESTES
    # =========================================================================

    def test_health(self):
        """Testa endpoints de health."""
        print_section("Health Check")

        # Health
        self.request("GET", "/../health", expected_status=[200])

        # Root
        self.request("GET", "/../", expected_status=[200])

        # Test DB
        self.request("GET", "/../test-db", expected_status=[200])

    def test_auth(self):
        """Testa autenticação."""
        print_section("Autenticação")

        # Login
        success, data = self.request(
            "POST", "/auth/login",
            data={"email": TEST_EMAIL, "senha": TEST_PASSWORD},
            expected_status=[200]
        )

        if success:
            # Token pode estar diretamente no response ou dentro de "data"
            self.token = data.get("access_token") or data.get("data", {}).get("access_token")
            if self.token:
                self.headers["Authorization"] = f"Bearer {self.token}"
                print(f"   {Colors.GREEN}Token obtido com sucesso!{Colors.END}")
            else:
                print(f"   {Colors.RED}Token não encontrado na resposta{Colors.END}")
                print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   {Colors.RED}Falha no login - demais testes podem falhar{Colors.END}")

        # Me (precisa de token)
        if self.token:
            self.request("GET", "/auth/me", expected_status=[200])
        else:
            self.skip("GET", "/auth/me", "sem token")

    def test_clinica(self):
        """Testa endpoints de clínica."""
        print_section("Clínica")

        if not self.token:
            self.skip("GET", "/clinica", "sem autenticação")
            return

        # Get clínica
        self.request("GET", "/clinica", expected_status=[200])

        # Get configurações
        self.request("GET", "/clinica/configuracoes", expected_status=[200])

        # Update configurações
        self.request(
            "PATCH", "/clinica/configuracoes",
            data={"enviar_lembrete_d1": True},
            expected_status=[200]
        )

        # Listar perfis
        success, data = self.request("GET", "/clinica/perfis", expected_status=[200])

        # Criar perfil
        success, data = self.request(
            "POST", "/clinica/perfis",
            data={
                "nome": f"Perfil Teste {uuid4().hex[:6]}",
                "descricao": "Perfil criado pelo teste automatizado",
                "permissoes": {
                    "agenda": "CLE",
                    "pacientes": "L",
                    "prontuario": "-"
                }
            },
            expected_status=[201, 409]  # 409 se já existir
        )

        if success and "data" in data:
            self.perfil_id = data["data"].get("id")

        # Get perfil
        if self.perfil_id:
            self.request("GET", f"/clinica/perfis/{self.perfil_id}", expected_status=[200])
        else:
            self.skip("GET", "/clinica/perfis/{id}", "perfil não criado")

    def test_pacientes(self):
        """Testa endpoints de pacientes."""
        print_section("Pacientes")

        if not self.token:
            self.skip("GET", "/pacientes", "sem autenticação")
            return

        # Listar pacientes
        self.request("GET", "/pacientes", expected_status=[200])

        # Criar paciente (sem CPF para evitar validação)
        success, data = self.request(
            "POST", "/pacientes",
            data={
                "nome": f"Paciente Teste API {uuid4().hex[:6]}",
                "data_nascimento": "1990-05-15",
                "sexo": "M",
                "telefone": "11999999999",
                "email": f"teste_{uuid4().hex[:6]}@teste.com"
            },
            expected_status=[201, 409]
        )

        if success and "data" in data:
            self.paciente_id = data["data"].get("id")

        # Get paciente
        if self.paciente_id:
            self.request("GET", f"/pacientes/{self.paciente_id}", expected_status=[200])

            # Update paciente
            self.request(
                "PATCH", f"/pacientes/{self.paciente_id}",
                data={"observacoes": "Atualizado via teste API"},
                expected_status=[200]
            )

            # Timeline
            self.request("GET", f"/pacientes/{self.paciente_id}/timeline", expected_status=[200])

            # Histórico médico
            self.request("GET", f"/pacientes/{self.paciente_id}/historico-medico", expected_status=[200])
        else:
            self.skip("GET", "/pacientes/{id}", "paciente não criado")

        # Buscar pacientes (usa search param no list)
        self.request("GET", "/pacientes", params={"search": "Teste"}, expected_status=[200])

    def test_agenda(self):
        """Testa endpoints de agenda."""
        print_section("Agenda")

        if not self.token:
            self.skip("GET", "/agenda/tipos-consulta", "sem autenticação")
            return

        # Tipos de consulta
        success, data = self.request("GET", "/agenda/tipos-consulta", expected_status=[200])

        if success and "data" in data and len(data["data"]) > 0:
            self.tipo_consulta_id = data["data"][0].get("id")

        # Buscar médicos (precisamos de um médico_id para slots)
        # Por enquanto vamos pular slots se não tiver médico

        # Listar agendamentos
        self.request("GET", "/agenda/agendamentos", expected_status=[200])

        # Listar por data
        hoje = date.today().isoformat()
        self.request(
            "GET", "/agenda/agendamentos",
            params={"data": hoje},
            expected_status=[200]
        )

        # Criar agendamento (precisa de paciente, médico e tipo_consulta)
        if self.paciente_id and self.tipo_consulta_id:
            # Primeiro precisamos de um médico_id
            # Vamos tentar buscar da API ou pular
            self.skip("POST", "/agenda/agendamentos", "médico_id não disponível")
        else:
            self.skip("POST", "/agenda/agendamentos", "dados insuficientes")

        # Métricas
        self.request("GET", "/agenda/metricas", expected_status=[200])

        # Bloqueios
        self.request("GET", "/agenda/bloqueios", expected_status=[200])

    def test_cards(self):
        """Testa endpoints de cards/kanban."""
        print_section("Cards / Kanban")

        if not self.token:
            self.skip("GET", "/cards", "sem autenticação")
            return

        # Listar cards
        success, data = self.request("GET", "/cards", expected_status=[200])

        if success and "data" in data and len(data.get("data", [])) > 0:
            self.card_id = data["data"][0].get("id")

        # Kanban por fase
        for fase in [0, 1, 2, 3]:
            self.request("GET", f"/cards/kanban/{fase}", expected_status=[200])

        # Get card específico
        if self.card_id:
            self.request("GET", f"/cards/{self.card_id}", expected_status=[200])

            # Checklist
            self.request("GET", f"/cards/{self.card_id}/checklist", expected_status=[200])

            # Histórico
            self.request("GET", f"/cards/{self.card_id}/historico", expected_status=[200])

            # Documentos
            self.request("GET", f"/cards/{self.card_id}/documentos", expected_status=[200])

            # Mensagens
            self.request("GET", f"/cards/{self.card_id}/mensagens", expected_status=[200])
        else:
            self.skip("GET", "/cards/{id}", "nenhum card encontrado")

    def test_evidencias(self):
        """Testa endpoints de evidências."""
        print_section("Evidências")

        if not self.token:
            self.skip("GET", "/evidencias", "sem autenticação")
            return

        # Listar evidências
        success, data = self.request("GET", "/evidencias", expected_status=[200])

        if success and "data" in data and len(data.get("data", [])) > 0:
            self.evidencia_id = data["data"][0].get("id")

        # Get evidência específica
        if self.evidencia_id:
            self.request("GET", f"/evidencias/{self.evidencia_id}", expected_status=[200])
        else:
            self.skip("GET", "/evidencias/{id}", "nenhuma evidência encontrada")

        # Por entidade (exemplo com paciente)
        if self.paciente_id:
            self.request(
                "GET", f"/evidencias/entidade/pacientes/{self.paciente_id}",
                expected_status=[200]
            )

            # Resumo
            self.request(
                "GET", f"/evidencias/entidade/pacientes/{self.paciente_id}/resumo",
                expected_status=[200]
            )

            # Verificar
            self.request(
                "GET", f"/evidencias/verificar/pacientes/{self.paciente_id}/criar",
                expected_status=[200]
            )
        else:
            self.skip("GET", "/evidencias/entidade/{...}", "paciente não disponível")

    def cleanup(self):
        """Limpa dados de teste (opcional)."""
        print_section("Cleanup")

        if not self.token:
            print(f"   {Colors.YELLOW}Cleanup pulado - sem autenticação{Colors.END}")
            return

        # Deletar perfil de teste
        if self.perfil_id:
            self.request(
                "DELETE", f"/clinica/perfis/{self.perfil_id}",
                expected_status=[200, 400, 404]  # 400 se tiver usuários
            )

        # Não deletamos paciente para manter histórico
        print(f"   {Colors.YELLOW}Paciente mantido: {self.paciente_id}{Colors.END}")

    def print_summary(self):
        """Imprime resumo dos testes."""
        print_header("RESUMO DOS TESTES")

        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]

        print(f"  {Colors.GREEN}✓ Passou:  {self.results['passed']:3}{Colors.END}")
        print(f"  {Colors.RED}✗ Falhou:  {self.results['failed']:3}{Colors.END}")
        print(f"  {Colors.YELLOW}○ Pulado:  {self.results['skipped']:3}{Colors.END}")
        print(f"  {Colors.BOLD}  Total:   {total:3}{Colors.END}")

        if self.results["failed"] == 0:
            print(f"\n  {Colors.GREEN}{Colors.BOLD}🎉 Todos os testes passaram!{Colors.END}")
        else:
            print(f"\n  {Colors.RED}{Colors.BOLD}⚠️  Alguns testes falharam{Colors.END}")

        print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print_header("TESTE DA API DOCFLOW")

    print(f"  URL Base: {BASE_URL}")
    print(f"  Usuário:  {TEST_EMAIL}")
    print()

    # Verifica se API está acessível
    try:
        response = requests.get(f"{BASE_URL}/../health", timeout=5)
        if response.status_code != 200:
            print(f"{Colors.RED}API não está respondendo corretamente{Colors.END}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}Não foi possível conectar à API em {BASE_URL}{Colors.END}")
        print(f"Certifique-se de que o servidor está rodando:")
        print(f"  python -m uvicorn app.main:app --host 127.0.0.1 --port 8080")
        sys.exit(1)

    # Executa testes
    tester = APITester()

    try:
        tester.test_health()
        tester.test_auth()
        tester.test_clinica()
        tester.test_pacientes()
        tester.test_agenda()
        tester.test_cards()
        tester.test_evidencias()
        # tester.cleanup()  # Descomente para limpar dados de teste
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testes interrompidos pelo usuário{Colors.END}")

    tester.print_summary()

    # Exit code baseado nos resultados
    sys.exit(0 if tester.results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
