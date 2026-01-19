-- ============================================
-- MIGRATION 005: Chat LangGraph
-- ============================================
-- Tabelas e campos para suportar Chat LangGraph
-- Data: 16 de Janeiro de 2026
-- ============================================

-- ============================================
-- 1. TABELA CONVERSAS (se não existir)
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversas') THEN
        
        CREATE TABLE conversas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
            telefone VARCHAR(20) NOT NULL,
            paciente_id UUID REFERENCES pacientes(id) ON DELETE SET NULL,
            ativa BOOLEAN DEFAULT true,
            ultimo_estado VARCHAR(50),
            ultima_intencao VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Índices
        CREATE INDEX idx_conversas_clinica ON conversas(clinica_id);
        CREATE INDEX idx_conversas_telefone ON conversas(telefone);
        CREATE INDEX idx_conversas_paciente ON conversas(paciente_id);
        CREATE INDEX idx_conversas_ativa ON conversas(ativa);
        CREATE INDEX idx_conversas_updated ON conversas(updated_at);

        RAISE NOTICE 'Tabela conversas criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela conversas já existe';
    END IF;
END $$;


-- ============================================
-- 2. ADICIONA CAMPOS EM CONVERSAS (se necessário)
-- ============================================

DO $$
BEGIN
    -- Campo ultimo_estado
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversas' AND column_name = 'ultimo_estado'
    ) THEN
        ALTER TABLE conversas ADD COLUMN ultimo_estado VARCHAR(50);
        RAISE NOTICE 'Campo ultimo_estado adicionado em conversas';
    END IF;

    -- Campo ultima_intencao
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversas' AND column_name = 'ultima_intencao'
    ) THEN
        ALTER TABLE conversas ADD COLUMN ultima_intencao VARCHAR(50);
        RAISE NOTICE 'Campo ultima_intencao adicionado em conversas';
    END IF;
END $$;


-- ============================================
-- 3. TABELA MENSAGENS
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mensagens') THEN
        
        CREATE TABLE mensagens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversa_id UUID NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
            direcao VARCHAR(10) NOT NULL CHECK (direcao IN ('recebida', 'enviada')),
            tipo VARCHAR(20) DEFAULT 'texto' CHECK (tipo IN ('texto', 'audio', 'imagem', 'documento', 'video')),
            conteudo TEXT,
            midia_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Índices
        CREATE INDEX idx_mensagens_conversa ON mensagens(conversa_id);
        CREATE INDEX idx_mensagens_created ON mensagens(created_at);
        CREATE INDEX idx_mensagens_direcao ON mensagens(direcao);

        RAISE NOTICE 'Tabela mensagens criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela mensagens já existe';
    END IF;
END $$;


-- ============================================
-- 4. TABELA LANGGRAPH_CHECKPOINTS
-- ============================================
-- Persistência de estado do grafo LangGraph
-- Requerida pelo PostgresSaver
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'langgraph_checkpoints') THEN
        
        CREATE TABLE langgraph_checkpoints (
            thread_id VARCHAR(255) NOT NULL,
            checkpoint_ns VARCHAR(255) NOT NULL DEFAULT '',
            checkpoint_id VARCHAR(255) NOT NULL,
            parent_checkpoint_id VARCHAR(255),
            type VARCHAR(50),
            checkpoint JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        );

        -- Índices
        CREATE INDEX idx_checkpoints_thread ON langgraph_checkpoints(thread_id);
        CREATE INDEX idx_checkpoints_created ON langgraph_checkpoints(created_at);
        CREATE INDEX idx_checkpoints_parent ON langgraph_checkpoints(parent_checkpoint_id);

        RAISE NOTICE 'Tabela langgraph_checkpoints criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela langgraph_checkpoints já existe';
    END IF;
END $$;


-- ============================================
-- 5. TABELA LANGGRAPH_WRITES
-- ============================================
-- Requerida pelo PostgresSaver para writes pendentes
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'langgraph_writes') THEN
        
        CREATE TABLE langgraph_writes (
            thread_id VARCHAR(255) NOT NULL,
            checkpoint_ns VARCHAR(255) NOT NULL DEFAULT '',
            checkpoint_id VARCHAR(255) NOT NULL,
            task_id VARCHAR(255) NOT NULL,
            idx INTEGER NOT NULL,
            channel VARCHAR(255) NOT NULL,
            value JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        );

        -- Índices
        CREATE INDEX idx_writes_thread ON langgraph_writes(thread_id);
        CREATE INDEX idx_writes_checkpoint ON langgraph_writes(thread_id, checkpoint_ns, checkpoint_id);

        RAISE NOTICE 'Tabela langgraph_writes criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela langgraph_writes já existe';
    END IF;
END $$;


-- ============================================
-- 6. FUNÇÃO DE ATUALIZAÇÃO AUTOMÁTICA
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- 7. TRIGGER PARA CONVERSAS
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trigger_conversas_updated_at'
    ) THEN
        CREATE TRIGGER trigger_conversas_updated_at
            BEFORE UPDATE ON conversas
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        
        RAISE NOTICE 'Trigger trigger_conversas_updated_at criado';
    END IF;
END $$;


-- ============================================
-- 8. COMENTÁRIOS NAS TABELAS
-- ============================================

COMMENT ON TABLE conversas IS 'Conversas do chat LangGraph por telefone';
COMMENT ON TABLE mensagens IS 'Histórico de mensagens das conversas';
COMMENT ON TABLE langgraph_checkpoints IS 'Checkpoints do estado do grafo LangGraph';
COMMENT ON TABLE langgraph_writes IS 'Writes pendentes do LangGraph';

COMMENT ON COLUMN conversas.ultimo_estado IS 'Último estado do grafo (coletando_nome, coletando_data, etc)';
COMMENT ON COLUMN conversas.ultima_intencao IS 'Última intenção classificada (AGENDAR, VALOR, FAQ, etc)';
COMMENT ON COLUMN mensagens.direcao IS 'Direção da mensagem: recebida (do paciente) ou enviada (do sistema)';


-- ============================================
-- FIM DA MIGRATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Migration 005 - Chat LangGraph: CONCLUÍDA';
    RAISE NOTICE '==============================================';
END $$;
