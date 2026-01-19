-- ============================================
-- MIGRAÇÃO: Verificação de Evidências
-- ============================================
-- Tabelas para log de verificação e alertas
-- ============================================

-- Log de todas as verificações executadas
CREATE TABLE IF NOT EXISTS verificacoes_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    trigger VARCHAR(50) NOT NULL,  -- mensagem_whatsapp, card_criado, mudanca_fase
    referencia_tipo VARCHAR(50) NOT NULL,  -- mensagem, card
    referencia_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completo',  -- completo, incompleto
    verificacoes JSONB NOT NULL DEFAULT '[]',  -- Array de verificações
    dados_extra JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_verificacoes_clinica ON verificacoes_log(clinica_id);
CREATE INDEX idx_verificacoes_trigger ON verificacoes_log(trigger);
CREATE INDEX idx_verificacoes_status ON verificacoes_log(status);
CREATE INDEX idx_verificacoes_created ON verificacoes_log(created_at);

-- Alertas para a governadora
CREATE TABLE IF NOT EXISTS alertas_governanca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    tipo VARCHAR(50) NOT NULL,  -- evidencia_faltando, erro_processo, etc
    trigger VARCHAR(50),
    card_id UUID REFERENCES cards(id),
    resumo TEXT NOT NULL,
    itens_faltando JSONB DEFAULT '[]',
    prioridade VARCHAR(20) NOT NULL DEFAULT 'normal',  -- baixa, normal, alta, critica
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',  -- pendente, resolvido, ignorado
    resolucao VARCHAR(50),  -- ok, ignorado, corrigido
    resolvido_por UUID REFERENCES usuarios(id),
    resolvido_em TIMESTAMP WITH TIME ZONE,
    observacao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alertas_clinica ON alertas_governanca(clinica_id);
CREATE INDEX idx_alertas_status ON alertas_governanca(status);
CREATE INDEX idx_alertas_prioridade ON alertas_governanca(prioridade);
CREATE INDEX idx_alertas_card ON alertas_governanca(card_id);

-- ============================================
-- RLS
-- ============================================

ALTER TABLE verificacoes_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "verificacoes_clinica" ON verificacoes_log
    FOR ALL
    USING (clinica_id = (auth.jwt() ->> 'clinica_id')::uuid);

ALTER TABLE alertas_governanca ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alertas_clinica" ON alertas_governanca
    FOR ALL
    USING (clinica_id = (auth.jwt() ->> 'clinica_id')::uuid);

-- ============================================
-- VIEWS ÚTEIS
-- ============================================

-- View de resumo de verificações por dia
CREATE OR REPLACE VIEW vw_verificacoes_diarias AS
SELECT 
    clinica_id,
    DATE(created_at) as data,
    trigger,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completo') as completos,
    COUNT(*) FILTER (WHERE status = 'incompleto') as incompletos,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completo')::numeric / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) as taxa_sucesso
FROM verificacoes_log
GROUP BY clinica_id, DATE(created_at), trigger
ORDER BY data DESC;

-- View de alertas pendentes com dados do card
CREATE OR REPLACE VIEW vw_alertas_pendentes AS
SELECT 
    a.*,
    c.fase,
    c.subfase,
    p.nome as paciente_nome,
    p.telefone as paciente_telefone,
    ag.data as agendamento_data,
    ag.hora_inicio as agendamento_hora
FROM alertas_governanca a
LEFT JOIN cards c ON a.card_id = c.id
LEFT JOIN pacientes p ON c.paciente_id = p.id
LEFT JOIN agendamentos ag ON c.agendamento_id = ag.id
WHERE a.status = 'pendente'
ORDER BY 
    CASE a.prioridade 
        WHEN 'critica' THEN 1 
        WHEN 'alta' THEN 2 
        WHEN 'normal' THEN 3 
        ELSE 4 
    END,
    a.created_at;

-- ============================================
-- FUNÇÃO: Calcular taxa de validação
-- ============================================

CREATE OR REPLACE FUNCTION calcular_taxa_validacao(p_clinica_id UUID, p_dias INTEGER DEFAULT 30)
RETURNS TABLE (
    fase TEXT,
    dias_desde_inicio INTEGER,
    taxa_sucesso NUMERIC,
    taxa_validacao NUMERIC
) AS $$
DECLARE
    v_data_inicio TIMESTAMP;
    v_dias_inicio INTEGER;
    v_total INTEGER;
    v_completos INTEGER;
    v_taxa_sucesso NUMERIC;
BEGIN
    -- Busca data de criação da clínica
    SELECT created_at INTO v_data_inicio
    FROM clinicas WHERE id = p_clinica_id;
    
    v_dias_inicio := EXTRACT(DAY FROM NOW() - v_data_inicio);
    
    -- Fase de implantação: 100% validação
    IF v_dias_inicio <= 30 THEN
        RETURN QUERY SELECT 
            'implantacao'::TEXT,
            v_dias_inicio,
            0::NUMERIC,
            1.0::NUMERIC;
        RETURN;
    END IF;
    
    -- Calcula taxa de sucesso
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completo')
    INTO v_total, v_completos
    FROM verificacoes_log
    WHERE clinica_id = p_clinica_id
    AND created_at >= NOW() - (p_dias || ' days')::INTERVAL;
    
    IF v_total = 0 THEN
        v_taxa_sucesso := 0;
    ELSE
        v_taxa_sucesso := v_completos::NUMERIC / v_total;
    END IF;
    
    -- Calcula taxa de validação baseada no sucesso
    RETURN QUERY SELECT 
        'normal'::TEXT,
        v_dias_inicio,
        ROUND(v_taxa_sucesso, 3),
        CASE 
            WHEN v_taxa_sucesso >= 0.95 THEN 0.05
            WHEN v_taxa_sucesso >= 0.90 THEN 0.20
            WHEN v_taxa_sucesso >= 0.80 THEN 0.40
            WHEN v_taxa_sucesso >= 0.70 THEN 0.60
            ELSE 1.0
        END::NUMERIC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calcular_taxa_validacao IS 'Calcula taxa de validação baseada na performance do sistema';
