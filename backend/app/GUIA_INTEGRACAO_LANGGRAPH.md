# GUIA DE INTEGRAÇÃO: Chat LangGraph no ClinicOS

> **Versão:** 1.0.0  
> **Data:** 16 de Janeiro de 2026  
> **Status:** Pronto para Integração  
> **Sprint:** 5 (Fase 0 - Funil de Leads)

---

## 📋 ÍNDICE

1. [Resumo Executivo](#1-resumo-executivo)
2. [Análise de Compatibilidade](#2-análise-de-compatibilidade)
3. [Preparação do Ambiente](#3-preparação-do-ambiente)
4. [Passo a Passo da Integração](#4-passo-a-passo-da-integração)
5. [Adaptações Necessárias](#5-adaptações-necessárias)
6. [Migração do Chat Atual](#6-migração-do-chat-atual)
7. [Testes e Validação](#7-testes-e-validação)
8. [Troubleshooting](#8-troubleshooting)

---

# 1. RESUMO EXECUTIVO

## O Que É o Módulo LangGraph?

O módulo `chat_langgraph` é uma **reescrita completa** do chat atual (`app/chat/`) usando a biblioteca LangGraph, que permite:

- ✅ **Conversas multi-turno**: Mantém estado entre mensagens
- ✅ **Coleta progressiva de dados**: Nome → CPF → Nascimento → Convênio
- ✅ **Grafo visual**: Fluxo de nós com edges condicionais
- ✅ **Persistência de estado**: PostgreSQL via checkpointer
- ✅ **Integração com Kestra**: Webhooks automáticos

## Por Que Migrar?

| Critério | Chat Atual | Chat LangGraph |
|----------|------------|----------------|
| Estado entre mensagens | ❌ Não tem | ✅ Persistente |
| Coleta de cadastro | ❌ Tenta tudo junto | ✅ Progressiva |
| Funil de leads | ❌ Só agendamento | ✅ CRM completo |
| Governança | ✅ Integrada | ✅ Integrada |
| Complexidade | ⭐⭐ Simples | ⭐⭐⭐ Média |

## Impacto no Sprint 5

O módulo LangGraph **resolve o Sprint 5 (Fase 0 - Funil de Leads)** quase completamente:

- ✅ Card criado no primeiro contato (não no agendamento)
- ✅ Verificação de cadastro existente
- ✅ Coleta de cadastro simplificado
- ✅ Classificação de intenção com/sem card ativo
- ⚠️ Falta: Sistema de reativação (complementar)

---

# 2. ANÁLISE DE COMPATIBILIDADE

## 2.1 Estrutura de Diretórios

```
ATUAL:                              NOVO:
app/chat/                           app/chat_langgraph/
├── __init__.py                     ├── __init__.py ✅
├── router.py                       ├── router.py ✅
├── service.py                      ├── service.py ✅
├── interpreter.py                  ├── graph.py ← SUBSTITUI
├── llm_providers.py                ├── llm_providers.py ✅ (igual)
└── schemas.py                      ├── schemas.py ✅ (unificado)
                                    ├── states.py ← NOVO
                                    ├── nodes.py ← NOVO
                                    ├── nodes_agendamento.py ← NOVO
                                    └── migrations/
                                        └── 005_chat_langgraph.sql ← NOVO
```

## 2.2 Intenções - Comparativo

| Chat Atual | LangGraph | Ação |
|------------|-----------|------|
| AGENDAR | AGENDAR | ✅ Manter |
| CONFIRMAR | CONFIRMAR | ✅ Manter |
| CANCELAR | CANCELAR | ✅ Manter |
| REMARCAR | REMARCAR | ✅ Manter |
| CHECK_IN | CHECK_IN | ✅ Manter |
| INFORMACAO | VALOR, CONVENIO, FAQ | ⚠️ Subdividido |
| SAUDACAO | SAUDACAO | ✅ Manter |
| DESPEDIDA | DESPEDIDA | ✅ Manter |
| DESCONHECIDO | DESCONHECIDO | ✅ Manter |
| - | EXAMES | ➕ Novo (Fase 1) |
| - | ANAMNESE | ➕ Novo (Fase 1) |

## 2.3 Schemas de Resposta

**Chat Atual (`MensagemResponse`):**
```python
{
  "id": "uuid",
  "resposta": "Texto",
  "interpretacao": {
    "intencao": "AGENDAR",
    "confianca": 85,
    "dados": {...}
  },
  "acoes": [{"tipo": "...", "sucesso": true}],
  "validacao_pendente": true,
  "validacao_id": "uuid"
}
```

**LangGraph (`MensagemResponse` - Novo):**
```python
{
  "id": "uuid",
  "resposta": "Texto",
  "estado": "coletando_nome",  # NOVO
  "intencao": "AGENDAR",
  "confianca": 0.85,
  "acoes": ["card_criado"],  # Formato diferente
  "conversa_id": "uuid",
  "paciente_id": "uuid",
  "card_id": "uuid",
  "agendamento_id": "uuid",
  "validacao_pendente": true,
  "validacao_id": "uuid"
}
```

**Decisão:** Usar schema do LangGraph (mais completo) e adaptar frontend.

---

# 3. PREPARAÇÃO DO AMBIENTE

## 3.1 Instalar Dependências

```bash
cd backend

# Adicionar ao requirements.txt
echo "langgraph>=0.2.0" >> app/requirements.txt
echo "langchain-core>=0.3.0" >> app/requirements.txt
echo "langgraph-checkpoint-postgres>=0.0.6" >> app/requirements.txt

# Instalar
pip install -r app/requirements.txt
```

## 3.2 Configurar Variáveis de Ambiente

Adicionar ao `.env`:

```env
# === LANGGRAPH ===
# Connection string para PostgreSQL (checkpointer)
# Usar a mesma conexão do Supabase
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Kestra (opcional, para webhooks)
KESTRA_URL=http://localhost:8080
KESTRA_TOKEN=seu-token-aqui
```

## 3.3 Atualizar `core/config.py`

```python
# Adicionar ao Settings:
class Settings(BaseSettings):
    # ... existentes ...
    
    # LangGraph
    supabase_db_url: Optional[str] = Field(None, env="SUPABASE_DB_URL")
    
    # Kestra
    kestra_url: Optional[str] = Field(None, env="KESTRA_URL")
    kestra_token: Optional[str] = Field(None, env="KESTRA_TOKEN")
```

## 3.4 Aplicar Migration SQL

```bash
# Opção 1: Via psql
psql $SUPABASE_DB_URL -f app/chat_langgraph/migrations/005_chat_langgraph.sql

# Opção 2: Via Supabase Dashboard
# Copiar conteúdo do arquivo e executar no SQL Editor
```

---

# 4. PASSO A PASSO DA INTEGRAÇÃO

## 4.1 Copiar Arquivos

```bash
# Criar diretório
mkdir -p backend/app/chat_langgraph

# Copiar todos os arquivos do módulo
cp -r chat_langgraph_completo/codigo/* backend/app/chat_langgraph/
```

## 4.2 Ajustar Imports

Os arquivos usam imports relativos. Ajustar conforme estrutura real:

**`nodes.py` e `nodes_agendamento.py`:**
```python
# ANTES (fallback para desenvolvimento)
try:
    from ..pacientes import service as pacientes_service
    from ..cards import service as cards_service
    from ..agenda import service as agenda_service
    from ..governanca import service as governanca_service
except ImportError:
    pacientes_service = None
    # ...

# MANTER ASSIM - os imports vão funcionar quando integrado
```

**`llm_providers.py`:**
```python
# ANTES
from ..core.config import settings

# VERIFICAR se o path está correto para sua estrutura
from app.core.config import settings  # ou
from ..core.config import settings    # depende de onde está
```

**`router.py`:**
```python
# ANTES
try:
    from ..auth.service import get_current_user_optional
    from ..core.config import settings
    from ..core.database import get_db
    from .llm_providers import get_llm_provider
except ImportError:
    # ...

# MANTER - vai funcionar quando integrado corretamente
```

## 4.3 Registrar Router no FastAPI

Em `app/main.py`:

```python
# Importar o novo router
from app.chat_langgraph.router import router as chat_langgraph_router

# Registrar (SUBSTITUINDO o chat atual ou usando path diferente)

# Opção A: Substituir completamente
# app.include_router(chat_router, prefix="/v1")  # Comentar
app.include_router(chat_langgraph_router, prefix="/v1")

# Opção B: Manter ambos em paralelo (para migração gradual)
app.include_router(chat_router, prefix="/v1")  # Manter atual
app.include_router(chat_langgraph_router, prefix="/v1/chat-v2")  # Novo
```

## 4.4 Verificar Integração

```bash
# Iniciar backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

# Verificar endpoints
curl http://localhost:8080/docs

# Verificar status do módulo
curl http://localhost:8080/v1/chat/status
```

---

# 5. ADAPTAÇÕES NECESSÁRIAS

## 5.1 Integrar com Services Existentes

Os nós do LangGraph acessam o banco diretamente. Para manter consistência, usar os services existentes:

**Em `nodes.py`, atualizar `verificar_cadastro`:**
```python
async def verificar_cadastro(state: ConversaState, db) -> ConversaState:
    """Verifica se paciente existe no banco pelo telefone."""
    telefone = state["telefone"]
    clinica_id = state["clinica_id"]
    
    # OPÇÃO A: Usar service existente (RECOMENDADO)
    from app.pacientes import service as pacientes_service
    paciente = await pacientes_service.buscar_por_telefone(
        db=db,
        clinica_id=clinica_id,
        telefone=telefone
    )
    
    # OPÇÃO B: Manter acesso direto (atual)
    result = db.table("pacientes").select("*").eq(
        "clinica_id", clinica_id
    ).eq(
        "telefone", telefone
    ).execute()
    # ...
```

## 5.2 Garantir Governança

A governança já está integrada nos nós. Verificar que `governanca_service` está importando corretamente:

```python
# Em nodes.py e nodes_agendamento.py
from app.governanca import service as governanca_service

# Verificar que a função trigger_whatsapp existe
# Deve ter a mesma assinatura esperada:
# await governanca_service.trigger_whatsapp(
#     clinica_id=...,
#     tipo_trigger="card_criado",
#     dados={...}
# )
```

## 5.3 Adaptar Frontend

O frontend precisa lidar com o novo schema de resposta:

**Em `frontend/src/lib/api.ts`:**
```typescript
// Novo tipo de resposta
interface MensagemResponseV2 {
  id: string;
  resposta: string;
  estado: string;  // NOVO
  intencao: string | null;
  confianca: number;
  acoes: string[];  // Formato diferente
  conversa_id: string;
  paciente_id: string | null;
  card_id: string | null;
  agendamento_id: string | null;
  validacao_pendente: boolean;
  validacao_id: string | null;
  sucesso: boolean;
  tempo_processamento_ms: number | null;
}
```

**No componente de chat:**
```typescript
// Mostrar estado atual da conversa
{response.estado && (
  <div className="text-xs text-gray-500">
    Estado: {response.estado}
  </div>
)}
```

---

# 6. MIGRAÇÃO DO CHAT ATUAL

## 6.1 Estratégia Recomendada: Substituição

Como o Sprint 5 (Fase 0) requer funcionalidades que o chat atual não tem, a melhor estratégia é **substituir completamente**:

1. ✅ Mover `app/chat/` para `app/chat_legacy/` (backup)
2. ✅ Renomear `app/chat_langgraph/` para `app/chat/`
3. ✅ Atualizar imports no `main.py`
4. ✅ Testar todos os fluxos

## 6.2 O Que Reaproveitar do Chat Atual

| Arquivo | Ação |
|---------|------|
| `interpreter.py` | ❌ Substituído por `graph.py` |
| `llm_providers.py` | ✅ Já existe versão igual no LangGraph |
| `schemas.py` | ⚠️ Mesclar com novo (intenções) |
| `service.py` | ❌ Substituído por novo |
| `router.py` | ❌ Substituído por novo |

## 6.3 Comandos de Migração

```bash
cd backend/app

# 1. Backup do chat atual
mv chat chat_legacy

# 2. Renomear LangGraph
mv chat_langgraph chat

# 3. Verificar imports no main.py
# Deve estar: from app.chat.router import router as chat_router
```

---

# 7. TESTES E VALIDAÇÃO

## 7.1 Testes Manuais

### Teste 1: Paciente Novo - Coleta de Cadastro
```bash
# Mensagem 1
curl -X POST http://localhost:8080/v1/chat/mensagem \
  -H "Content-Type: application/json" \
  -d '{"telefone": "21999999999", "mensagem": "Oi, quero marcar consulta"}'

# Esperado: Pede nome
# {"resposta": "Olá! 👋 Para começar, qual seu nome completo?", "estado": "coletando_nome"}

# Mensagem 2
curl -X POST http://localhost:8080/v1/chat/mensagem \
  -H "Content-Type: application/json" \
  -d '{"telefone": "21999999999", "mensagem": "João da Silva"}'

# Esperado: Pede CPF
# {"resposta": "Prazer, João! 😊 Agora preciso do seu CPF.", "estado": "coletando_cpf"}

# ... continua coletando
```

### Teste 2: Paciente Existente - Direto para Intenção
```bash
# Paciente já cadastrado no banco
curl -X POST http://localhost:8080/v1/chat/mensagem \
  -H "Content-Type: application/json" \
  -d '{"telefone": "21988887777", "mensagem": "Quero agendar consulta"}'

# Esperado: Pula cadastro, vai para agendamento
# {"resposta": "Para qual dia você gostaria de agendar?", "estado": "coletando_data"}
```

### Teste 3: Pergunta de Valor
```bash
curl -X POST http://localhost:8080/v1/chat/mensagem \
  -H "Content-Type: application/json" \
  -d '{"telefone": "21999999999", "mensagem": "Quanto custa a consulta?"}'

# Esperado: Retorna valores
# {"resposta": "💰 Valores das consultas:\n• Consulta: R$ 250.00", "estado": "finalizado"}
```

### Teste 4: Governança
```bash
# Verificar se validação foi criada
curl http://localhost:8080/v1/governanca/validacoes/pendentes

# Esperado: Validação do card_criado ou agendamento_criado
```

## 7.2 Checklist de Validação

- [ ] Endpoint `/chat/status` retorna "ok"
- [ ] Endpoint `/chat/mensagem` aceita requests
- [ ] Coleta de cadastro funciona (nome → cpf → nascimento → convênio)
- [ ] Card é criado no primeiro contato
- [ ] Agendamento é criado após confirmar
- [ ] Governança registra validações
- [ ] Webhooks Kestra são disparados (se configurado)
- [ ] Frontend recebe e exibe respostas corretamente

---

# 8. TROUBLESHOOTING

## 8.1 Erros Comuns

### "Chat service não configurado"
```
HTTPException 500: Chat service não configurado
```

**Causa:** `get_db` ou `get_llm_provider` não encontrados.

**Solução:**
```python
# Em router.py, verificar imports
from app.core.database import get_db
from app.chat.llm_providers import get_llm_provider
```

### "GROQ_API_KEY não configurada"
```
ValueError: GROQ_API_KEY não configurada
```

**Causa:** Variável de ambiente não definida.

**Solução:**
```bash
# No .env
GROQ_API_KEY=gsk_xxx

# Verificar se Settings está carregando
python -c "from app.core.config import settings; print(settings.groq_api_key)"
```

### "Governança não disponível"
```
[WARN] Governança não disponível - pulando validação
```

**Causa:** Import de `governanca_service` falhou.

**Solução:**
```python
# Verificar se o módulo governanca existe
from app.governanca import service as governanca_service

# Verificar se a função existe
print(dir(governanca_service))  # Deve ter trigger_whatsapp
```

### "Tabela não existe"
```
relation "conversas" does not exist
```

**Causa:** Migration não foi aplicada.

**Solução:**
```bash
# Aplicar migration
psql $SUPABASE_DB_URL -f app/chat/migrations/005_chat_langgraph.sql
```

### "Checkpointer falhou"
```
[WARN] Falha ao criar PostgresSaver
```

**Causa:** `SUPABASE_DB_URL` inválida ou tabelas de checkpoint não existem.

**Solução:**
```bash
# Verificar connection string
psql $SUPABASE_DB_URL -c "SELECT 1"

# Verificar tabelas
psql $SUPABASE_DB_URL -c "SELECT * FROM langgraph_checkpoints LIMIT 1"
```

## 8.2 Logs Úteis

```python
# Adicionar em service.py para debug
import logging
logging.basicConfig(level=logging.DEBUG)

# Ver estado do grafo
resultado = await self.graph.processar_mensagem(...)
print(f"Estado: {resultado}")
```

## 8.3 Rollback

Se precisar voltar ao chat anterior:

```bash
cd backend/app

# Restaurar backup
rm -rf chat
mv chat_legacy chat

# Reiniciar servidor
# Ctrl+C e python -m uvicorn app.main:app --reload
```

---

# CHECKLIST FINAL

## Antes de Começar
- [ ] Backup do chat atual (`cp -r chat chat_backup`)
- [ ] `.env` atualizado com variáveis necessárias
- [ ] Dependências instaladas (`pip install -r requirements.txt`)

## Integração
- [ ] Arquivos copiados para `app/chat_langgraph/`
- [ ] Migration SQL aplicada
- [ ] Router registrado no `main.py`
- [ ] Imports ajustados para estrutura do projeto

## Validação
- [ ] Endpoint `/chat/status` funcionando
- [ ] Teste de coleta de cadastro OK
- [ ] Teste de agendamento OK
- [ ] Governança registrando validações
- [ ] Frontend adaptado para novo schema

## Pós-integração
- [ ] Documentação atualizada
- [ ] Equipe informada das mudanças
- [ ] Monitoramento configurado

---

**FIM DO GUIA**

> Próximos passos após integração:
> 1. Implementar sistema de reativação de leads (complemento do Sprint 5)
> 2. Integrar busca real de slots (Sprint 6)
> 3. Conectar Evolution API (Sprint 8)
