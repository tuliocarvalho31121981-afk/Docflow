-- ============================================
-- MIGRAÇÃO: Sistema de Governança Integrada
-- ============================================
-- Integrado com Kanban e Evidências
-- ============================================

-- Trust Scores (por chave de trigger/ação)
CREATE TABLE IF NOT EXISTS trust_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    chave VARCHAR(100) NOT NULL,  -- ex: "whatsapp", "card_criado", "fase_0_para_1"
    valor DECIMAL(5,2) NOT NULL DEFAULT 50,
    total INTEGER NOT NULL DEFAULT 0,
    ultima_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(clinica_id, chave)
);

CREATE INDEX idx_trust_scores_clinica ON trust_scores(clinica_id);

-- Evidências (provas de tarefas cumpridas)
CREATE TABLE IF NOT EXISTS evidencias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    card_id UUID NOT NULL REFERENCES cards(id),
    tarefa_key VARCHAR(50) NOT NULL,  -- ex: "confirmacao_enviada", "anamnese_preenchida"
    fase INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL,  -- log, documento, confirmacao, assinatura
    dados JSONB NOT NULL DEFAULT '{}',
    arquivo_url TEXT,
    completa BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX idx_evidencias_card ON evidencias(card_id);
CREATE INDEX idx_evidencias_tarefa ON evidencias(tarefa_key);
CREATE INDEX idx_evidencias_fase ON evidencias(card_id, fase);

-- Validações de Governança (fila para governadora)
CREATE TABLE IF NOT EXISTS validacoes_governanca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    trigger_type VARCHAR(50) NOT NULL,  -- mensagem_whatsapp, card_criado, mudanca_fase
    resumo TEXT NOT NULL,
    evidencias JSONB NOT NULL DEFAULT '[]',
    dados JSONB NOT NULL DEFAULT '{}',
    perguntas JSONB NOT NULL DEFAULT '[]',
    referencia_tipo VARCHAR(50),
    referencia_id UUID,
    prioridade VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    validado_por UUID,
    validado_em TIMESTAMP WITH TIME ZONE,
    observacao TEXT,
    correcoes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_validacoes_clinica ON validacoes_governanca(clinica_id);
CREATE INDEX idx_validacoes_status ON validacoes_governanca(status);
CREATE INDEX idx_validacoes_trigger ON validacoes_governanca(trigger_type);
CREATE INDEX idx_validacoes_prioridade ON validacoes_governanca(prioridade, created_at);

-- Campo para data de início do sistema na clínica
ALTER TABLE clinicas ADD COLUMN IF NOT EXISTS data_inicio_sistema TIMESTAMP WITH TIME ZONE;

-- ============================================
-- RLS (Row Level Security)
-- ============================================

ALTER TABLE trust_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "trust_scores_clinica" ON trust_scores
    FOR ALL USING (clinica_id = (auth.jwt() ->> 'clinica_id')::uuid);

ALTER TABLE evidencias ENABLE ROW LEVEL SECURITY;
CREATE POLICY "evidencias_clinica" ON evidencias
    FOR ALL USING (clinica_id = (auth.jwt() ->> 'clinica_id')::uuid);

ALTER TABLE validacoes_governanca ENABLE ROW LEVEL SECURITY;
CREATE POLICY "validacoes_clinica" ON validacoes_governanca
    FOR ALL USING (clinica_id = (auth.jwt() ->> 'clinica_id')::uuid);

-- ============================================
-- COMENTÁRIOS
-- ============================================

COMMENT ON TABLE trust_scores IS 'Trust scores por tipo de trigger - determina taxa de validação';
COMMENT ON TABLE evidencias IS 'Provas de tarefas cumpridas - logs e documentos';
COMMENT ON TABLE validacoes_governanca IS 'Fila de validações para a governadora';
COMMENT ON COLUMN clinicas.data_inicio_sistema IS 'Data de início da implantação - primeiros 30 dias = 100% validação';
