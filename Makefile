# ============================================================================
# DocFlow - Makefile
# ============================================================================
# Comandos básicos para desenvolvimento e deploy
# Uso: make <comando>
# ============================================================================

.PHONY: help install dev test lint docker db kestra clean

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
NC     := \033[0m # No Color

# ============================================================================
# HELP
# ============================================================================

help: ## Mostra esta ajuda
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║                    DocFlow - Comandos Disponíveis                   ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)USO:$(NC) make $(GREEN)<comando>$(NC)"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)SETUP & INSTALAÇÃO$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)install$(NC)          Instala todas as dependências (backend + frontend)"
	@echo "  $(GREEN)install-backend$(NC)  Instala dependências do backend Python"
	@echo "  $(GREEN)install-frontend$(NC) Instala dependências do frontend Node"
	@echo "  $(GREEN)setup$(NC)            Setup completo (install + env + db)"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)DESENVOLVIMENTO$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)dev$(NC)              Inicia backend + frontend em modo dev"
	@echo "  $(GREEN)dev-backend$(NC)      Inicia apenas o backend (FastAPI)"
	@echo "  $(GREEN)dev-frontend$(NC)     Inicia apenas o frontend (Vite/React)"
	@echo "  $(GREEN)dev-all$(NC)          Inicia tudo (backend + frontend + kestra)"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)DOCKER$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)docker-build$(NC)     Builda imagens Docker"
	@echo "  $(GREEN)docker-up$(NC)        Sobe containers (backend + redis + kestra)"
	@echo "  $(GREEN)docker-down$(NC)      Para containers"
	@echo "  $(GREEN)docker-logs$(NC)      Mostra logs dos containers"
	@echo "  $(GREEN)docker-clean$(NC)     Remove containers e volumes"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)DATABASE (SUPABASE)$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)db-migrate$(NC)       Executa migrations no Supabase"
	@echo "  $(GREEN)db-seed$(NC)          Popula dados iniciais"
	@echo "  $(GREEN)db-reset$(NC)         Reset do banco (CUIDADO!)"
	@echo "  $(GREEN)db-backup$(NC)        Backup do banco"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)KESTRA (WORKFLOWS)$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)kestra-up$(NC)        Inicia Kestra"
	@echo "  $(GREEN)kestra-down$(NC)      Para Kestra"
	@echo "  $(GREEN)kestra-deploy$(NC)    Deploy dos workflows"
	@echo "  $(GREEN)kestra-logs$(NC)      Logs do Kestra"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)TESTES & QUALIDADE$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)test$(NC)             Roda todos os testes"
	@echo "  $(GREEN)test-backend$(NC)     Testes do backend"
	@echo "  $(GREEN)test-frontend$(NC)    Testes do frontend"
	@echo "  $(GREEN)test-cov$(NC)         Testes com coverage"
	@echo "  $(GREEN)lint$(NC)             Lint do código (black + flake8 + eslint)"
	@echo "  $(GREEN)format$(NC)           Formata código automaticamente"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)DEPLOY$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)deploy-staging$(NC)   Deploy para staging"
	@echo "  $(GREEN)deploy-prod$(NC)      Deploy para produção"
	@echo ""
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)UTILITÁRIOS$(NC)"
	@echo "$(YELLOW)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "  $(GREEN)clean$(NC)            Limpa arquivos temporários"
	@echo "  $(GREEN)env-example$(NC)      Cria arquivo .env de exemplo"
	@echo "  $(GREEN)logs$(NC)             Mostra logs da aplicação"
	@echo "  $(GREEN)shell$(NC)            Abre shell no container backend"
	@echo ""

# ============================================================================
# SETUP & INSTALAÇÃO
# ============================================================================

install: install-backend install-frontend ## Instala todas as dependências
	@echo "$(GREEN)✓ Todas as dependências instaladas!$(NC)"

install-backend: ## Instala dependências do backend
	@echo "$(CYAN)→ Instalando dependências do backend...$(NC)"
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend instalado!$(NC)"

install-frontend: ## Instala dependências do frontend
	@echo "$(CYAN)→ Instalando dependências do frontend...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend instalado!$(NC)"

setup: install env-check ## Setup completo do projeto
	@echo "$(GREEN)✓ Setup completo!$(NC)"
	@echo "$(YELLOW)→ Próximo passo: configure o arquivo .env$(NC)"

env-check: ## Verifica se .env existe
	@if [ ! -f backend/.env ]; then \
		echo "$(YELLOW)⚠ Arquivo .env não encontrado!$(NC)"; \
		echo "$(CYAN)→ Criando .env a partir do exemplo...$(NC)"; \
		cp backend/.env.example backend/.env; \
		echo "$(YELLOW)→ Edite backend/.env com suas credenciais$(NC)"; \
	else \
		echo "$(GREEN)✓ Arquivo .env encontrado$(NC)"; \
	fi

# ============================================================================
# DESENVOLVIMENTO
# ============================================================================

dev: ## Inicia backend + frontend em modo dev
	@echo "$(CYAN)→ Iniciando em modo desenvolvimento...$(NC)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Inicia apenas o backend
	@echo "$(CYAN)→ Iniciando backend na porta 8000...$(NC)"
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Inicia apenas o frontend
	@echo "$(CYAN)→ Iniciando frontend na porta 5173...$(NC)"
	cd frontend && npm run dev

dev-all: ## Inicia tudo (backend + frontend + kestra)
	@echo "$(CYAN)→ Iniciando ambiente completo...$(NC)"
	@make docker-up
	@make -j2 dev-backend dev-frontend

# ============================================================================
# DOCKER
# ============================================================================

docker-build: ## Builda imagens Docker
	@echo "$(CYAN)→ Buildando imagens Docker...$(NC)"
	docker-compose -f docker-compose.yml build

docker-up: ## Sobe containers
	@echo "$(CYAN)→ Subindo containers...$(NC)"
	docker-compose -f docker-compose.yml up -d
	@echo "$(GREEN)✓ Containers rodando!$(NC)"
	@echo "  $(CYAN)Backend:$(NC)  http://localhost:8000"
	@echo "  $(CYAN)Kestra:$(NC)   http://localhost:8080"
	@echo "  $(CYAN)Redis:$(NC)    localhost:6379"

docker-down: ## Para containers
	@echo "$(CYAN)→ Parando containers...$(NC)"
	docker-compose -f docker-compose.yml down
	@echo "$(GREEN)✓ Containers parados$(NC)"

docker-logs: ## Mostra logs dos containers
	docker-compose -f docker-compose.yml logs -f

docker-clean: ## Remove containers e volumes
	@echo "$(YELLOW)⚠ Removendo containers e volumes...$(NC)"
	docker-compose -f docker-compose.yml down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✓ Limpeza concluída$(NC)"

# ============================================================================
# DATABASE (SUPABASE)
# ============================================================================

db-migrate: ## Executa migrations
	@echo "$(CYAN)→ Executando migrations...$(NC)"
	@echo "$(YELLOW)→ Acesse o Supabase Dashboard e execute os SQLs em ordem:$(NC)"
	@echo "  1. schema-fase1-fundacao.sql"
	@echo "  2. schema-fase2-agenda.sql"
	@echo "  3. schema-fase3-cards.sql"
	@echo "  4. schema-fase4-prontuario.sql"
	@echo "  5. schema-fase5-financeiro.sql"
	@echo "  6. schema-fase6-auditoria.sql"
	@echo "  7. schema-fase7-evidencias.sql"

db-seed: ## Popula dados iniciais
	@echo "$(CYAN)→ Populando dados iniciais...$(NC)"
	cd backend && . venv/bin/activate && python -m scripts.seed

db-reset: ## Reset do banco (CUIDADO!)
	@echo "$(YELLOW)⚠ ATENÇÃO: Isso vai APAGAR todos os dados!$(NC)"
	@read -p "Tem certeza? [y/N] " confirm && [ "$$confirm" = "y" ]
	@echo "$(CYAN)→ Resetando banco...$(NC)"

db-backup: ## Backup do banco
	@echo "$(CYAN)→ Criando backup...$(NC)"
	@mkdir -p backups
	@echo "$(YELLOW)→ Use o Supabase Dashboard para exportar$(NC)"

# ============================================================================
# KESTRA (WORKFLOWS)
# ============================================================================

kestra-up: ## Inicia Kestra
	@echo "$(CYAN)→ Iniciando Kestra...$(NC)"
	docker-compose -f kestra/docker-compose.yml up -d
	@echo "$(GREEN)✓ Kestra rodando em http://localhost:8080$(NC)"

kestra-down: ## Para Kestra
	@echo "$(CYAN)→ Parando Kestra...$(NC)"
	docker-compose -f kestra/docker-compose.yml down

kestra-deploy: ## Deploy dos workflows
	@echo "$(CYAN)→ Fazendo deploy dos workflows...$(NC)"
	@for f in kestra/workflows/*.yml; do \
		echo "  → Deploying $$f"; \
		curl -X POST http://localhost:8080/api/v1/flows \
			-H "Content-Type: application/x-yaml" \
			-d @$$f; \
	done
	@echo "$(GREEN)✓ Workflows deployados!$(NC)"

kestra-logs: ## Logs do Kestra
	docker-compose -f kestra/docker-compose.yml logs -f

# ============================================================================
# TESTES & QUALIDADE
# ============================================================================

test: test-backend test-frontend ## Roda todos os testes
	@echo "$(GREEN)✓ Todos os testes passaram!$(NC)"

test-backend: ## Testes do backend
	@echo "$(CYAN)→ Rodando testes do backend...$(NC)"
	cd backend && . venv/bin/activate && pytest -v

test-frontend: ## Testes do frontend
	@echo "$(CYAN)→ Rodando testes do frontend...$(NC)"
	cd frontend && npm test

test-cov: ## Testes com coverage
	@echo "$(CYAN)→ Rodando testes com coverage...$(NC)"
	cd backend && . venv/bin/activate && pytest --cov=app --cov-report=html
	@echo "$(GREEN)✓ Relatório em backend/htmlcov/index.html$(NC)"

lint: ## Lint do código
	@echo "$(CYAN)→ Rodando lint...$(NC)"
	cd backend && . venv/bin/activate && flake8 app/
	cd frontend && npm run lint
	@echo "$(GREEN)✓ Lint passou!$(NC)"

format: ## Formata código
	@echo "$(CYAN)→ Formatando código...$(NC)"
	cd backend && . venv/bin/activate && black app/ && isort app/
	cd frontend && npm run format
	@echo "$(GREEN)✓ Código formatado!$(NC)"

# ============================================================================
# DEPLOY
# ============================================================================

deploy-staging: ## Deploy para staging
	@echo "$(CYAN)→ Deploy para staging...$(NC)"
	@echo "$(YELLOW)→ Configure CI/CD no GitHub Actions$(NC)"

deploy-prod: ## Deploy para produção
	@echo "$(YELLOW)⚠ DEPLOY PARA PRODUÇÃO$(NC)"
	@read -p "Tem certeza? [y/N] " confirm && [ "$$confirm" = "y" ]
	@echo "$(CYAN)→ Deploy para produção...$(NC)"

# ============================================================================
# UTILITÁRIOS
# ============================================================================

clean: ## Limpa arquivos temporários
	@echo "$(CYAN)→ Limpando arquivos temporários...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Limpeza concluída!$(NC)"

env-example: ## Cria arquivo .env de exemplo
	@echo "$(CYAN)→ Criando .env.example...$(NC)"
	@cat > backend/.env.example << 'EOF'
# ============================================================================
# DocFlow - Variáveis de Ambiente
# ============================================================================

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-anon-key
SUPABASE_SERVICE_KEY=sua-service-key

# Redis
REDIS_URL=redis://localhost:6379

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-api-key
EVOLUTION_INSTANCE=docflow-whatsapp

# OpenAI (Whisper)
OPENAI_API_KEY=sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Kestra
KESTRA_URL=http://localhost:8080
KESTRA_API_KEY=

# App
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=sua-secret-key-aqui

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF
	@echo "$(GREEN)✓ Arquivo .env.example criado!$(NC)"

logs: ## Mostra logs da aplicação
	@tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)Nenhum arquivo de log encontrado$(NC)"

shell: ## Abre shell no container backend
	docker exec -it docflow-backend /bin/bash

# ============================================================================
# ATALHOS RÁPIDOS
# ============================================================================

up: docker-up ## Alias para docker-up
down: docker-down ## Alias para docker-down
t: test ## Alias para test
l: lint ## Alias para lint
f: format ## Alias para format
