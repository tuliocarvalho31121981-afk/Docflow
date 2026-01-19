-- ============================================================================
-- FASE 2: AGENDA
-- ============================================================================
-- Sistema de agendamento: horários, bloqueios e agendamentos
-- Depende de: clinicas, users, pacientes (Fase 1)
-- ============================================================================


-- ============================================================================
-- 1. TIPOS DE CONSULTA
-- ============================================================================
-- Define os tipos de atendimento oferecidos (consulta, retorno, exame, etc)

CREATE TABLE tipos_consulta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(100) NOT NULL,                 -- Ex: "Consulta", "Retorno", "Check-up"
    descricao TEXT,
    cor VARCHAR(7) DEFAULT '#3B82F6',           -- Hex color para UI
    
    -- Configurações
    duracao_minutos INTEGER NOT NULL DEFAULT 30,
    valor_particular DECIMAL(10,2),             -- Preço se particular
    
    -- Regras
    permite_encaixe BOOLEAN DEFAULT false,      -- Pode ser encaixe?
    antecedencia_minima_horas INTEGER DEFAULT 2, -- Mínimo de horas para agendar
    antecedencia_maxima_dias INTEGER DEFAULT 60, -- Máximo de dias para agendar
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_tipos_consulta_clinica ON tipos_consulta(clinica_id);

-- Trigger updated_at
CREATE TRIGGER trigger_tipos_consulta_updated_at
    BEFORE UPDATE ON tipos_consulta
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 2. HORARIOS DISPONIVEIS
-- ============================================================================
-- Template semanal de cada médico. Define quando ele atende.

CREATE TABLE horarios_disponiveis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    medico_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Dia da semana (0=Domingo, 1=Segunda, ..., 6=Sábado)
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    
    -- Período
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    
    -- Configurações do período
    intervalo_minutos INTEGER DEFAULT 30,       -- Duração padrão do slot
    vagas_por_horario INTEGER DEFAULT 1,        -- Quantos pacientes por slot (geralmente 1)
    
    -- Tipos de consulta aceitos neste horário
    tipos_consulta_ids UUID[] DEFAULT '{}',     -- Se vazio, aceita todos
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validação: hora_fim > hora_inicio
    CONSTRAINT horario_valido CHECK (hora_fim > hora_inicio)
);

-- Indexes
CREATE INDEX idx_horarios_clinica ON horarios_disponiveis(clinica_id);
CREATE INDEX idx_horarios_medico ON horarios_disponiveis(medico_id);
CREATE INDEX idx_horarios_dia ON horarios_disponiveis(dia_semana);

-- Trigger updated_at
CREATE TRIGGER trigger_horarios_updated_at
    BEFORE UPDATE ON horarios_disponiveis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 3. BLOQUEIOS AGENDA
-- ============================================================================
-- Exceções: férias, feriados, compromissos, etc.

CREATE TABLE bloqueios_agenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Escopo do bloqueio
    medico_id UUID REFERENCES users(id),        -- NULL = bloqueio para toda a clínica
    
    -- Período
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    hora_inicio TIME,                           -- NULL = dia inteiro
    hora_fim TIME,                              -- NULL = dia inteiro
    
    -- Identificação
    motivo VARCHAR(255) NOT NULL,               -- Ex: "Férias", "Congresso", "Feriado"
    tipo VARCHAR(50) DEFAULT 'bloqueio' CHECK (tipo IN ('bloqueio', 'feriado', 'ferias', 'outro')),
    
    -- Recorrência (para feriados anuais)
    recorrente_anual BOOLEAN DEFAULT false,     -- Repete todo ano na mesma data?
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Validação
    CONSTRAINT bloqueio_data_valida CHECK (data_fim >= data_inicio),
    CONSTRAINT bloqueio_hora_valida CHECK (
        (hora_inicio IS NULL AND hora_fim IS NULL) OR 
        (hora_inicio IS NOT NULL AND hora_fim IS NOT NULL AND hora_fim > hora_inicio)
    )
);

-- Indexes
CREATE INDEX idx_bloqueios_clinica ON bloqueios_agenda(clinica_id);
CREATE INDEX idx_bloqueios_medico ON bloqueios_agenda(medico_id);
CREATE INDEX idx_bloqueios_data ON bloqueios_agenda(data_inicio, data_fim);

-- Index para buscar bloqueios ativos em uma data
CREATE INDEX idx_bloqueios_periodo ON bloqueios_agenda(data_inicio, data_fim, medico_id);


-- ============================================================================
-- 4. CONVENIOS
-- ============================================================================
-- Convênios aceitos pela clínica (necessário antes de agendamentos)

CREATE TABLE convenios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(255) NOT NULL,                 -- Ex: "Unimed", "Bradesco Saúde"
    codigo_ans VARCHAR(20),                     -- Registro ANS
    
    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Configurações de faturamento
    prazo_envio_guias_dias INTEGER DEFAULT 5,   -- Dias após consulta para enviar
    prazo_pagamento_dias INTEGER DEFAULT 30,    -- Dias para receber após envio
    
    -- Valores (tabela simplificada, pode expandir depois)
    valor_consulta DECIMAL(10,2),
    valor_retorno DECIMAL(10,2),
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_convenios_clinica ON convenios(clinica_id);

-- Trigger updated_at
CREATE TRIGGER trigger_convenios_updated_at
    BEFORE UPDATE ON convenios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 5. PACIENTES_CONVENIOS
-- ============================================================================
-- Vínculo paciente <-> convênio (um paciente pode ter vários)

CREATE TABLE pacientes_convenios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    convenio_id UUID NOT NULL REFERENCES convenios(id) ON DELETE CASCADE,
    
    -- Dados do plano
    numero_carteirinha VARCHAR(50) NOT NULL,
    plano VARCHAR(100),                         -- Ex: "Enfermaria", "Apartamento"
    
    -- Validade
    data_validade DATE,
    
    -- Controle
    principal BOOLEAN DEFAULT false,            -- Convênio principal?
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Paciente não pode ter mesmo convênio duplicado
    UNIQUE(paciente_id, convenio_id)
);

-- Indexes
CREATE INDEX idx_pac_convenios_paciente ON pacientes_convenios(paciente_id);
CREATE INDEX idx_pac_convenios_convenio ON pacientes_convenios(convenio_id);

-- Trigger updated_at
CREATE TRIGGER trigger_pac_convenios_updated_at
    BEFORE UPDATE ON pacientes_convenios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 6. AGENDAMENTOS
-- ============================================================================
-- Coração da agenda. Cada linha = uma consulta marcada.

CREATE TABLE agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Quem
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Quando
    data DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    
    -- O quê
    tipo_consulta_id UUID REFERENCES tipos_consulta(id),
    
    -- Como vai pagar
    forma_pagamento VARCHAR(20) NOT NULL CHECK (forma_pagamento IN ('particular', 'convenio')),
    convenio_id UUID REFERENCES convenios(id), -- Se forma_pagamento = 'convenio'
    paciente_convenio_id UUID REFERENCES pacientes_convenios(id), -- Carteirinha usada
    valor_previsto DECIMAL(10,2),               -- Valor esperado
    
    -- Motivo/Queixa
    motivo_consulta TEXT,                       -- Preenchido na pré-consulta
    
    -- Status do agendamento
    status VARCHAR(30) DEFAULT 'agendado' CHECK (status IN (
        'agendado',          -- Marcado, aguardando
        'confirmado',        -- Paciente confirmou
        'aguardando',        -- Paciente fez check-in, aguardando ser chamado
        'em_atendimento',    -- Médico chamou
        'atendido',          -- Consulta finalizada
        'faltou',            -- No-show
        'cancelado',         -- Cancelado
        'remarcado'          -- Foi remarcado (virou outro agendamento)
    )),
    
    -- Timestamps de cada etapa (checkpoints)
    confirmado_em TIMESTAMP WITH TIME ZONE,
    checkin_em TIMESTAMP WITH TIME ZONE,        -- CHECK-IN CLÍNICA
    chamado_em TIMESTAMP WITH TIME ZONE,        -- CHECK-IN CONSULTA
    finalizado_em TIMESTAMP WITH TIME ZONE,     -- CHECK-OUT
    
    -- Se cancelado/faltou
    motivo_cancelamento TEXT,
    cancelado_por UUID REFERENCES users(id),
    cancelado_por_paciente BOOLEAN DEFAULT false,
    
    -- Agendamento de origem (se for remarcação)
    agendamento_origem_id UUID REFERENCES agendamentos(id),
    
    -- Card derivado (se for retorno com exames pendentes)
    card_derivado_de UUID,                      -- Referência ao card que originou (preenchido depois)
    
    -- Encaixe?
    is_encaixe BOOLEAN DEFAULT false,
    
    -- Lembrete
    lembrete_enviado BOOLEAN DEFAULT false,
    lembrete_enviado_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id),  -- Se funcionário agendou
    created_by_paciente BOOLEAN DEFAULT false,  -- Se paciente agendou via WhatsApp
    
    -- Validação
    CONSTRAINT agendamento_horario_valido CHECK (hora_fim > hora_inicio),
    CONSTRAINT agendamento_convenio_obrigatorio CHECK (
        (forma_pagamento = 'particular') OR 
        (forma_pagamento = 'convenio' AND convenio_id IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_agendamentos_clinica ON agendamentos(clinica_id);
CREATE INDEX idx_agendamentos_paciente ON agendamentos(paciente_id);
CREATE INDEX idx_agendamentos_medico ON agendamentos(medico_id);
CREATE INDEX idx_agendamentos_data ON agendamentos(data);
CREATE INDEX idx_agendamentos_status ON agendamentos(status);

-- Index composto para buscar agenda do médico em uma data
CREATE INDEX idx_agendamentos_medico_data ON agendamentos(medico_id, data);

-- Index para buscar agendamentos futuros de um paciente
CREATE INDEX idx_agendamentos_paciente_data ON agendamentos(paciente_id, data);

-- Trigger updated_at
CREATE TRIGGER trigger_agendamentos_updated_at
    BEFORE UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 7. AGENDAMENTOS_HISTORICO
-- ============================================================================
-- Log de mudanças de status do agendamento (auditoria)

CREATE TABLE agendamentos_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agendamento_id UUID NOT NULL REFERENCES agendamentos(id) ON DELETE CASCADE,
    
    -- Mudança
    status_anterior VARCHAR(30),
    status_novo VARCHAR(30) NOT NULL,
    
    -- Quem mudou
    changed_by_user UUID REFERENCES users(id),
    changed_by_paciente BOOLEAN DEFAULT false,  -- Se foi ação do paciente (WhatsApp)
    changed_by_sistema BOOLEAN DEFAULT false,   -- Se foi automático
    
    -- Contexto
    motivo TEXT,
    
    -- Quando
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_agend_hist_agendamento ON agendamentos_historico(agendamento_id);


-- ============================================================================
-- 8. TRIGGER: REGISTRAR HISTÓRICO DE STATUS
-- ============================================================================

CREATE OR REPLACE FUNCTION on_agendamento_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO agendamentos_historico (
            agendamento_id,
            status_anterior,
            status_novo,
            changed_by_sistema
        ) VALUES (
            NEW.id,
            OLD.status,
            NEW.status,
            true  -- Por padrão assume sistema, pode ser sobrescrito na aplicação
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agendamento_historico
    AFTER UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION on_agendamento_status_change();


-- ============================================================================
-- 9. FUNCTION: BUSCAR SLOTS DISPONÍVEIS
-- ============================================================================
-- Retorna slots livres para um médico em uma data

CREATE OR REPLACE FUNCTION get_slots_disponiveis(
    p_clinica_id UUID,
    p_medico_id UUID,
    p_data DATE
)
RETURNS TABLE (
    hora_inicio TIME,
    hora_fim TIME,
    disponivel BOOLEAN
) AS $$
DECLARE
    v_dia_semana INTEGER;
BEGIN
    v_dia_semana := EXTRACT(DOW FROM p_data);
    
    -- Retorna slots baseado nos horários disponíveis menos agendamentos existentes
    RETURN QUERY
    WITH slots AS (
        -- Gera slots baseado nos horários do médico
        SELECT 
            h.hora_inicio + (generate_series(0, 
                EXTRACT(EPOCH FROM (h.hora_fim - h.hora_inicio))::INTEGER / 60 / h.intervalo_minutos - 1
            ) * h.intervalo_minutos * INTERVAL '1 minute') AS slot_inicio,
            h.hora_inicio + (generate_series(1, 
                EXTRACT(EPOCH FROM (h.hora_fim - h.hora_inicio))::INTEGER / 60 / h.intervalo_minutos
            ) * h.intervalo_minutos * INTERVAL '1 minute') AS slot_fim,
            h.intervalo_minutos
        FROM horarios_disponiveis h
        WHERE h.clinica_id = p_clinica_id
          AND h.medico_id = p_medico_id
          AND h.dia_semana = v_dia_semana
          AND h.ativo = true
    ),
    bloqueios AS (
        -- Busca bloqueios para a data
        SELECT b.hora_inicio AS bl_inicio, b.hora_fim AS bl_fim
        FROM bloqueios_agenda b
        WHERE b.clinica_id = p_clinica_id
          AND (b.medico_id = p_medico_id OR b.medico_id IS NULL)
          AND p_data BETWEEN b.data_inicio AND b.data_fim
    ),
    agendados AS (
        -- Busca agendamentos existentes
        SELECT a.hora_inicio AS ag_inicio, a.hora_fim AS ag_fim
        FROM agendamentos a
        WHERE a.clinica_id = p_clinica_id
          AND a.medico_id = p_medico_id
          AND a.data = p_data
          AND a.status NOT IN ('cancelado', 'faltou', 'remarcado')
    )
    SELECT 
        s.slot_inicio::TIME AS hora_inicio,
        s.slot_fim::TIME AS hora_fim,
        NOT EXISTS (
            SELECT 1 FROM bloqueios b 
            WHERE (b.bl_inicio IS NULL OR s.slot_inicio::TIME >= b.bl_inicio)
              AND (b.bl_fim IS NULL OR s.slot_fim::TIME <= b.bl_fim)
        ) AND NOT EXISTS (
            SELECT 1 FROM agendados a
            WHERE s.slot_inicio::TIME < a.ag_fim AND s.slot_fim::TIME > a.ag_inicio
        ) AS disponivel
    FROM slots s
    ORDER BY s.slot_inicio;
    
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 10. FUNCTION: MÉTRICAS DO DIA
-- ============================================================================
-- Retorna métricas de tempo para o dashboard

CREATE OR REPLACE FUNCTION get_metricas_dia(
    p_clinica_id UUID,
    p_data DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    total_agendados INTEGER,
    total_atendidos INTEGER,
    total_aguardando INTEGER,
    total_faltaram INTEGER,
    tempo_medio_espera_minutos NUMERIC,
    tempo_medio_consulta_minutos NUMERIC,
    taxa_ocupacao NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_agendados,
        COUNT(*) FILTER (WHERE status = 'atendido')::INTEGER AS total_atendidos,
        COUNT(*) FILTER (WHERE status = 'aguardando')::INTEGER AS total_aguardando,
        COUNT(*) FILTER (WHERE status = 'faltou')::INTEGER AS total_faltaram,
        
        -- Tempo médio de espera (check-in até chamado)
        ROUND(AVG(
            EXTRACT(EPOCH FROM (chamado_em - checkin_em)) / 60
        ) FILTER (WHERE chamado_em IS NOT NULL AND checkin_em IS NOT NULL), 1) AS tempo_medio_espera_minutos,
        
        -- Tempo médio de consulta (chamado até finalizado)
        ROUND(AVG(
            EXTRACT(EPOCH FROM (finalizado_em - chamado_em)) / 60
        ) FILTER (WHERE finalizado_em IS NOT NULL AND chamado_em IS NOT NULL), 1) AS tempo_medio_consulta_minutos,
        
        -- Taxa de ocupação (atendidos / agendados)
        ROUND(
            COUNT(*) FILTER (WHERE status = 'atendido')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE status NOT IN ('cancelado', 'remarcado')), 0) * 100
        , 1) AS taxa_ocupacao
        
    FROM agendamentos
    WHERE clinica_id = p_clinica_id
      AND data = p_data;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 11. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE tipos_consulta ENABLE ROW LEVEL SECURITY;
ALTER TABLE horarios_disponiveis ENABLE ROW LEVEL SECURITY;
ALTER TABLE bloqueios_agenda ENABLE ROW LEVEL SECURITY;
ALTER TABLE convenios ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes_convenios ENABLE ROW LEVEL SECURITY;
ALTER TABLE agendamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE agendamentos_historico ENABLE ROW LEVEL SECURITY;

-- Policies: usuário só vê dados da sua clínica
CREATE POLICY "tipos_consulta_clinica" ON tipos_consulta
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "horarios_clinica" ON horarios_disponiveis
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "bloqueios_clinica" ON bloqueios_agenda
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "convenios_clinica" ON convenios
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "pac_convenios_clinica" ON pacientes_convenios
    FOR ALL USING (
        paciente_id IN (
            SELECT id FROM pacientes 
            WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        )
    );

CREATE POLICY "agendamentos_clinica" ON agendamentos
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "agend_historico_clinica" ON agendamentos_historico
    FOR ALL USING (
        agendamento_id IN (
            SELECT id FROM agendamentos 
            WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        )
    );


-- ============================================================================
-- 12. TIPOS DE CONSULTA PADRÃO (SEED)
-- ============================================================================

CREATE OR REPLACE FUNCTION criar_tipos_consulta_padrao(p_clinica_id UUID)
RETURNS void AS $$
BEGIN
    INSERT INTO tipos_consulta (clinica_id, nome, descricao, duracao_minutos, cor) VALUES
    (p_clinica_id, 'Consulta', 'Primeira consulta ou consulta de rotina', 30, '#3B82F6'),
    (p_clinica_id, 'Retorno', 'Retorno de consulta anterior', 20, '#10B981'),
    (p_clinica_id, 'Check-up', 'Avaliação completa', 45, '#8B5CF6'),
    (p_clinica_id, 'Urgência', 'Atendimento de urgência', 30, '#EF4444'),
    (p_clinica_id, 'Procedimento', 'Procedimentos em consultório', 60, '#F59E0B');
END;
$$ LANGUAGE plpgsql;

-- Adiciona ao trigger de criação de clínica
CREATE OR REPLACE FUNCTION on_clinica_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM criar_perfis_padrao(NEW.id);
    PERFORM criar_tipos_consulta_padrao(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- FIM DA FASE 2
-- ============================================================================
