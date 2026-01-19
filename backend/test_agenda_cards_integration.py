"""
Teste estatico da integracao Agenda <-> Cards

Este teste verifica a estrutura do codigo sem precisar de dependencias.
"""
from pathlib import Path

def test_file_structure():
    """Verifica se os metodos existem no arquivo."""
    print("[TEST] Verificando estrutura do arquivo...")

    service_file = Path(__file__).parent / "app" / "agenda" / "service.py"

    if not service_file.exists():
        print(f"[ERRO] Arquivo nao encontrado: {service_file}")
        return False

    with open(service_file, "r", encoding="utf-8") as f:
        source = f.read()

    methods = [
        "_integrar_com_cards",
        "_marcar_checklist_card",
        "_criar_checklist_card",
        "_atualizar_card_por_status"
    ]

    all_exist = True
    for method_name in methods:
        if f"async def {method_name}" in source:
            print(f"  [OK] {method_name} encontrado")
        else:
            print(f"  [ERRO] {method_name} nao encontrado")
            all_exist = False

    return all_exist

def test_create_integration():
    """Testa se o metodo create() chama a integracao."""
    print("\n[TEST] Verificando integracao no create()...")

    service_file = Path(__file__).parent / "app" / "agenda" / "service.py"
    with open(service_file, "r", encoding="utf-8") as f:
        source = f.read()

    if "_integrar_com_cards" in source:
        # Verifica se esta dentro do metodo create
        if "async def create" in source:
            create_start = source.find("async def create")
            # Procura proximo metodo ou fim
            next_methods = [
                source.find("\n    async def ", create_start + 1),
                source.find("\n    def ", create_start + 1),
            ]
            next_methods = [x for x in next_methods if x != -1]
            create_end = min(next_methods) if next_methods else len(source)

            create_method = source[create_start:create_end]
            if "_integrar_com_cards" in create_method:
                print("  [OK] create() chama _integrar_com_cards")
                # Verifica se atualiza card_id
                if "card_id" in create_method and ("ag_data[\"card_id\"]" in create_method or "agendamento[\"card_id\"]" in create_method or "data={\"card_id\"" in create_method):
                    print("  [OK] create() atualiza card_id no agendamento")
                else:
                    print("  [AVISO] create() pode nao atualizar card_id")
                return True
            else:
                print("  [ERRO] create() nao chama _integrar_com_cards")
                return False
    else:
        print("  [ERRO] _integrar_com_cards nao encontrado no arquivo")
        return False

def test_update_status_integration():
    """Testa se o metodo update_status() chama a atualizacao do card."""
    print("\n[TEST] Verificando integracao no update_status()...")

    service_file = Path(__file__).parent / "app" / "agenda" / "service.py"
    with open(service_file, "r", encoding="utf-8") as f:
        source = f.read()

    if "_atualizar_card_por_status" in source:
        if "async def update_status" in source:
            update_start = source.find("async def update_status")
            next_methods = [
                source.find("\n    async def ", update_start + 1),
                source.find("\n    def ", update_start + 1),
            ]
            next_methods = [x for x in next_methods if x != -1]
            update_end = min(next_methods) if next_methods else len(source)

            update_method = source[update_start:update_end]
            if "_atualizar_card_por_status" in update_method:
                print("  [OK] update_status() chama _atualizar_card_por_status")
                return True
            else:
                print("  [ERRO] update_status() nao chama _atualizar_card_por_status")
                return False
    else:
        print("  [ERRO] _atualizar_card_por_status nao encontrado no arquivo")
        return False

def test_metrics_calculation():
    """Testa se get_metricas() usa horarios_disponiveis."""
    print("\n[TEST] Verificando calculo de metricas...")

    service_file = Path(__file__).parent / "app" / "agenda" / "service.py"
    with open(service_file, "r", encoding="utf-8") as f:
        source = f.read()

    if "async def get_metricas" in source:
        metrics_start = source.find("async def get_metricas")
        next_methods = [
            source.find("\n    async def ", metrics_start + 1),
            source.find("\n    def ", metrics_start + 1),
        ]
        next_methods = [x for x in next_methods if x != -1]
        metrics_end = min(next_methods) if next_methods else len(source)

        metrics_method = source[metrics_start:metrics_end]

        # Verifica se usa horarios_disponiveis
        if "horarios_disponiveis" in metrics_method or "horarios_template" in metrics_method:
            if "total_slots = 20" in metrics_method:
                # Pode ter fallback
                if "fallback" in metrics_method.lower() or "else:" in metrics_method.split("total_slots = 20")[-1][:200]:
                    print("  [OK] get_metricas() usa horarios_disponiveis com fallback")
                    return True
                else:
                    print("  [AVISO] get_metricas() pode usar valor fixo como padrao")
                    return False
            else:
                print("  [OK] get_metricas() usa horarios_disponiveis")
                return True
        else:
            print("  [ERRO] get_metricas() nao usa horarios_disponiveis")
            return False
    else:
        print("  [ERRO] get_metricas() nao encontrado")
        return False

def test_get_method_card_lookup():
    """Testa se get() busca card corretamente."""
    print("\n[TEST] Verificando busca de card no get()...")

    service_file = Path(__file__).parent / "app" / "agenda" / "service.py"
    with open(service_file, "r", encoding="utf-8") as f:
        source = f.read()

    if "async def get(self, id: str" in source:
        get_start = source.find("async def get(self, id: str")
        next_methods = [
            source.find("\n    async def ", get_start + 1),
            source.find("\n    def ", get_start + 1),
        ]
        next_methods = [x for x in next_methods if x != -1]
        get_end = min(next_methods) if next_methods else len(source)

        get_method = source[get_start:get_end]

        # Verifica se busca card via card_id ou agendamento_id
        if "card_id" in get_method:
            if "ag.get(\"card_id\")" in get_method or "ag[\"card_id\"]" in get_method:
                print("  [OK] get() busca card via card_id do agendamento")
                return True
            else:
                print("  [AVISO] get() menciona card_id mas pode nao buscar corretamente")
                return False
        else:
            print("  [ERRO] get() nao busca card via card_id")
            return False
    else:
        print("  [ERRO] get() nao encontrado")
        return False

def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("TESTE DE INTEGRACAO AGENDA <-> CARDS (ANALISE ESTATICA)")
    print("=" * 60)

    results = []

    results.append(("Estrutura dos Metodos", test_file_structure()))
    results.append(("Integracao no create()", test_create_integration()))
    results.append(("Integracao no update_status()", test_update_status_integration()))
    results.append(("Calculo de Metricas", test_metrics_calculation()))
    results.append(("Busca de Card no get()", test_get_method_card_lookup()))

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASSOU" if result else "[ERRO] FALHOU"
        print(f"{test_name}: {status}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} testes passaram")
    print("=" * 60)

    if passed == total:
        print("\n[SUCESSO] Todos os testes passaram!")
        return 0
    else:
        print(f"\n[AVISO] {total - passed} teste(s) falharam")
        return 1

if __name__ == "__main__":
    exit(main())
