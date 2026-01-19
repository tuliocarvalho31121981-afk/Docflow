-- Migration: 005_chat_conversas.sql
-- Descrição: Tabelas para chat/simulador
-- Data: 2026-01-16

-- =============================================
-- TABELA: conversas
-- Representa uma conversa com um telefone/paciente
-- =============================================
CREATE TABLE IF NOT EXISTS conversas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    telefone VARCHAR(20) NOT NULL,
    paciente_id UUID REFERENCES pacientes(id) ON DELETE SET NULL,
    ativa BOOLEAN DEFAULT true,
    criada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultima_mensagem_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT uk_conversa_telefone_clinica UNIQUE (telefone, clinica_id)
);

-- Índices para busca
CREATE INDEX IF NOT EXISTS idx_conversas_clinica ON conversas(clinica_id);
CREATE INDEX IF NOT EXISTS idx_conversas_telefone ON conversas(telefone);
CREATE INDEX IF NOT EXISTS idx_conversas_paciente ON conversas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_conversas_ativa ON conversas(ativa);
CREATE INDEX IF NOT EXISTS idx_conversas_ultima_msg ON conversas(ultima_mensagem_em DESC);


-- =============================================
-- TABELA: mensagens
-- Histórico de mensagens de cada conversa
-- =============================================
CREATE TABLE IF NOT EXISTS mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversa_id UUID NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('paciente', 'sistema')),
    conteudo TEXT NOT NULL,
    interpretacao JSONB,  -- Resultado da interpretação do LLM (para mensagens do paciente)
    criada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para busca
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_criada_em ON mensagens(criada_em);
CREATE INDEX IF NOT EXISTS idx_mensagens_tipo ON mensagens(tipo);


-- =============================================
-- TABELA: pacientes_simulados
-- Pacientes criados para simulação/teste
-- =============================================
CREATE TABLE IF NOT EXISTS pacientes_simulados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uk_paciente_simulado_telefone UNIQUE (telefone, clinica_id)
);


-- =============================================
-- VIEWS úteis
-- =============================================

-- View: Conversas com dados do paciente e última mensagem
CREATE OR REPLACE VIEW vw_conversas_resumo AS
SELECT 
    c.id,
    c.clinica_id,
    c.telefone,
    c.paciente_id,
    p.nome as paciente_nome,
    c.ativa,
    c.criada_em,
    c.ultima_mensagem_em,
    (
        SELECT conteudo 
        FROM mensagens m 
        WHERE m.conversa_id = c.id 
        ORDER BY m.criada_em DESC 
        LIMIT 1
    ) as ultima_mensagem,
    (
        SELECT COUNT(*) 
        FROM mensagens m 
        WHERE m.conversa_id = c.id
    ) as total_mensagens
FROM conversas c
LEFT JOIN pacientes p ON p.id = c.paciente_id;


-- =============================================
-- POLICIES (RLS)
-- =============================================

-- Habilita RLS
ALTER TABLE conversas ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- Policy: Conversas só visíveis pela clínica
CREATE POLICY conversas_clinica_policy ON conversas
    FOR ALL
    USING (clinica_id = current_setting('app.clinica_id', true)::uuid);

-- Policy: Mensagens seguem a conversa
CREATE POLICY mensagens_conversa_policy ON mensagens
    FOR ALL
    USING (
        conversa_id IN (
            SELECT id FROM conversas 
            WHERE clinica_id = current_setting('app.clinica_id', true)::uuid
        )
    );


-- =============================================
-- TRIGGERS
-- =============================================

-- Trigger: Atualiza ultima_mensagem_em quando nova mensagem é inserida
CREATE OR REPLACE FUNCTION update_conversa_ultima_mensagem()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversas 
    SET ultima_mensagem_em = NEW.criada_em
    WHERE id = NEW.conversa_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_conversa_ultima_mensagem
    AFTER INSERT ON mensagens
    FOR EACH ROW
    EXECUTE FUNCTION update_conversa_ultima_mensagem();


-- =============================================
-- COMENTÁRIOS
-- =============================================
COMMENT ON TABLE conversas IS 'Conversas de chat (simulador ou WhatsApp)';
COMMENT ON TABLE mensagens IS 'Histórico de mensagens de cada conversa';
COMMENT ON COLUMN mensagens.interpretacao IS 'JSON com resultado da interpretação do LLM: {intencao, confianca, dados}';
COMMENT ON COLUMN mensagens.tipo IS 'paciente = mensagem do paciente, sistema = resposta do sistema';
