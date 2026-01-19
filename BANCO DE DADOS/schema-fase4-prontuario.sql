-- ============================================================================
-- FASE 4: PRONTUÁRIO (CONSULTA)
-- ============================================================================
-- Dados clínicos da consulta. NÍVEL CRÍTICO - apenas médico acessa.
-- Depende de: clinicas, users, pacientes, agendamentos, cards (Fases 1-3)
-- ============================================================================


-- ============================================================================
-- 1. CONSULTAS
-- ============================================================================
-- Registro principal do atendimento. Uma consulta por agendamento.

CREATE TABLE consultas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Vínculos
    agendamento_id UUID NOT NULL REFERENCES agendamentos(id),
    card_id UUID NOT NULL REFERENCES cards(id),
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Timestamps
    iniciada_em TIMESTAMP WITH TIME ZONE,       -- Quando médico chamou
    finalizada_em TIMESTAMP WITH TIME ZONE,     -- Quando médico finalizou
    duracao_minutos INTEGER,                    -- Calculado automaticamente
    
    -- Status
    status VARCHAR(20) DEFAULT 'em_andamento' CHECK (status IN (
        'em_andamento',
        'finalizada',
        'cancelada'
    )),
    
    -- Tipo de atendimento
    tipo VARCHAR(30) DEFAULT 'presencial' CHECK (tipo IN ('presencial', 'telemedicina')),
    
    -- Resumo (preenchido pelo médico ou IA)
    resumo TEXT,                                -- Resumo executivo da consulta
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Uma consulta por agendamento
    UNIQUE(agendamento_id)
);

-- Indexes
CREATE INDEX idx_consultas_clinica ON consultas(clinica_id);
CREATE INDEX idx_consultas_paciente ON consultas(paciente_id);
CREATE INDEX idx_consultas_medico ON consultas(medico_id);
CREATE INDEX idx_consultas_card ON consultas(card_id);
CREATE INDEX idx_consultas_data ON consultas(created_at);

-- Trigger updated_at
CREATE TRIGGER trigger_consultas_updated_at
    BEFORE UPDATE ON consultas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 2. TRANSCRICOES
-- ============================================================================
-- Transcrição do áudio da consulta (Whisper API)

CREATE TABLE transcricoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    
    -- Áudio original
    audio_storage_path TEXT,                    -- Caminho no Storage (opcional, pode não guardar)
    audio_duracao_segundos INTEGER,
    
    -- Transcrição
    transcricao_bruta TEXT,                     -- Texto fiel do Whisper
    transcricao_revisada TEXT,                  -- Se médico editou
    
    -- Status do processamento
    status VARCHAR(20) DEFAULT 'processando' CHECK (status IN (
        'processando',
        'concluida',
        'erro'
    )),
    erro_mensagem TEXT,
    
    -- Metadados
    modelo_whisper VARCHAR(50),                 -- 'whisper-1', etc
    idioma VARCHAR(10) DEFAULT 'pt',
    
    -- Timestamps
    iniciada_em TIMESTAMP WITH TIME ZONE,
    concluida_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_transcricoes_consulta ON transcricoes(consulta_id);


-- ============================================================================
-- 3. PRONTUARIOS_SOAP
-- ============================================================================
-- Prontuário estruturado no formato SOAP
-- S = Subjetivo, O = Objetivo, A = Avaliação, P = Plano

CREATE TABLE prontuarios_soap (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- SOAP
    subjetivo TEXT,                             -- Queixa do paciente, história
    objetivo TEXT,                              -- Exame físico, sinais vitais
    avaliacao TEXT,                             -- Diagnóstico, hipóteses
    plano TEXT,                                 -- Conduta, orientações
    
    -- Exame físico estruturado (além do texto)
    exame_fisico JSONB DEFAULT '{}'::jsonb,
    /*
    Exemplo:
    {
        "sinais_vitais": {
            "pa_sistolica": 140,
            "pa_diastolica": 90,
            "fc": 72,
            "fr": 16,
            "temperatura": 36.5,
            "saturacao": 97,
            "peso": 68,
            "altura": 165
        },
        "ausculta_cardiaca": "Bulhas rítmicas, normofonéticas, sem sopros",
        "ausculta_pulmonar": "Murmúrio vesicular presente, sem ruídos adventícios",
        "abdome": "Plano, indolor, sem visceromegalias",
        "extremidades": "Sem edema, pulsos presentes"
    }
    */
    
    -- CIDs (diagnósticos)
    cids JSONB DEFAULT '[]'::jsonb,
    /*
    Exemplo:
    [
        { "codigo": "I10", "descricao": "Hipertensão essencial", "tipo": "principal" },
        { "codigo": "E11", "descricao": "Diabetes tipo 2", "tipo": "secundario" }
    ]
    */
    
    -- Origem do conteúdo
    gerado_por_ia BOOLEAN DEFAULT false,        -- Se IA gerou baseado na transcrição
    revisado_por_medico BOOLEAN DEFAULT false,  -- Se médico revisou
    revisado_em TIMESTAMP WITH TIME ZONE,
    
    -- Assinatura digital (opcional, ICP-Brasil)
    assinado BOOLEAN DEFAULT false,
    assinatura_certificado TEXT,
    assinado_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Um SOAP por consulta
    UNIQUE(consulta_id)
);

-- Indexes
CREATE INDEX idx_soap_consulta ON prontuarios_soap(consulta_id);
CREATE INDEX idx_soap_paciente ON prontuarios_soap(paciente_id);
CREATE INDEX idx_soap_medico ON prontuarios_soap(medico_id);

-- Trigger updated_at
CREATE TRIGGER trigger_soap_updated_at
    BEFORE UPDATE ON prontuarios_soap
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 4. RECEITAS
-- ============================================================================
-- Prescrições médicas

CREATE TABLE receitas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Tipo de receita
    tipo VARCHAR(30) DEFAULT 'simples' CHECK (tipo IN (
        'simples',          -- Receita comum
        'especial',         -- Receita de controle especial (azul/amarela)
        'antimicrobiano'    -- Receita de antimicrobiano
    )),
    
    -- Medicamentos
    itens JSONB NOT NULL DEFAULT '[]'::jsonb,
    /*
    Exemplo:
    [
        {
            "medicamento": "Losartana",
            "concentracao": "50mg",
            "forma": "comprimido",
            "quantidade": 30,
            "posologia": "1 comprimido pela manhã",
            "duracao": "uso contínuo",
            "observacao": null
        },
        {
            "medicamento": "Atorvastatina",
            "concentracao": "20mg",
            "forma": "comprimido",
            "quantidade": 30,
            "posologia": "1 comprimido à noite",
            "duracao": "uso contínuo",
            "observacao": "Tomar após o jantar"
        }
    ]
    */
    
    -- Observações gerais
    observacoes TEXT,
    
    -- PDF gerado
    pdf_storage_path TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'emitida' CHECK (status IN (
        'rascunho',
        'emitida',
        'cancelada'
    )),
    
    -- Assinatura digital
    assinado BOOLEAN DEFAULT false,
    assinatura_certificado TEXT,
    assinado_em TIMESTAMP WITH TIME ZONE,
    
    -- Envio ao paciente
    enviada_paciente BOOLEAN DEFAULT false,
    enviada_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_receitas_consulta ON receitas(consulta_id);
CREATE INDEX idx_receitas_paciente ON receitas(paciente_id);
CREATE INDEX idx_receitas_medico ON receitas(medico_id);

-- Trigger updated_at
CREATE TRIGGER trigger_receitas_updated_at
    BEFORE UPDATE ON receitas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 5. ATESTADOS
-- ============================================================================
-- Atestados médicos (comparecimento, afastamento, aptidão)

CREATE TABLE atestados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Tipo
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN (
        'comparecimento',   -- Atesta que compareceu
        'afastamento',      -- Atesta dias de afastamento
        'aptidao',          -- Apto para atividade
        'acompanhante'      -- Para acompanhante de paciente
    )),
    
    -- Conteúdo
    texto TEXT NOT NULL,                        -- Texto do atestado
    
    -- Período (para afastamento)
    data_inicio DATE,
    data_fim DATE,
    dias_afastamento INTEGER,
    
    -- CID (opcional)
    cid_codigo VARCHAR(10),
    cid_descricao VARCHAR(255),
    incluir_cid BOOLEAN DEFAULT false,          -- Paciente autorizou incluir CID?
    
    -- PDF gerado
    pdf_storage_path TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'emitido' CHECK (status IN (
        'rascunho',
        'emitido',
        'cancelado'
    )),
    
    -- Assinatura digital
    assinado BOOLEAN DEFAULT false,
    assinatura_certificado TEXT,
    assinado_em TIMESTAMP WITH TIME ZONE,
    
    -- Envio ao paciente
    enviado_paciente BOOLEAN DEFAULT false,
    enviado_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_atestados_consulta ON atestados(consulta_id);
CREATE INDEX idx_atestados_paciente ON atestados(paciente_id);
CREATE INDEX idx_atestados_medico ON atestados(medico_id);

-- Trigger updated_at
CREATE TRIGGER trigger_atestados_updated_at
    BEFORE UPDATE ON atestados
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 6. EXAMES_SOLICITADOS
-- ============================================================================
-- Exames solicitados pelo médico (gera SADT para convênio)

CREATE TABLE exames_solicitados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Exame
    codigo_tuss VARCHAR(20),                    -- Código TUSS
    nome VARCHAR(255) NOT NULL,                 -- Nome do exame
    tipo VARCHAR(50),                           -- 'laboratorial', 'imagem', 'cardiologico', etc
    
    -- Indicação
    indicacao_clinica TEXT,                     -- Por que pediu
    cid_codigo VARCHAR(10),                     -- CID relacionado
    
    -- Urgência
    urgente BOOLEAN DEFAULT false,
    
    -- Para retorno (card derivado)
    para_retorno BOOLEAN DEFAULT false,         -- Este exame é necessário para o retorno?
    prazo_dias INTEGER,                         -- Prazo para realizar (ex: 30 dias)
    
    -- Status do exame
    status VARCHAR(30) DEFAULT 'solicitado' CHECK (status IN (
        'solicitado',       -- Médico pediu
        'guia_emitida',     -- SADT gerada
        'agendado',         -- Paciente agendou
        'realizado',        -- Paciente fez
        'resultado_anexado',-- Resultado chegou
        'cancelado'
    )),
    
    -- Match com documento recebido
    documento_id UUID,                          -- Referência a cards_documentos quando receber
    resultado_em TIMESTAMP WITH TIME ZONE,
    
    -- Guia SADT
    guia_storage_path TEXT,
    guia_numero VARCHAR(50),
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_exames_sol_consulta ON exames_solicitados(consulta_id);
CREATE INDEX idx_exames_sol_paciente ON exames_solicitados(paciente_id);
CREATE INDEX idx_exames_sol_status ON exames_solicitados(status);
CREATE INDEX idx_exames_sol_retorno ON exames_solicitados(para_retorno) WHERE para_retorno = true;

-- Trigger updated_at
CREATE TRIGGER trigger_exames_sol_updated_at
    BEFORE UPDATE ON exames_solicitados
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 7. ENCAMINHAMENTOS
-- ============================================================================
-- Encaminhamentos para outros especialistas

CREATE TABLE encaminhamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consulta_id UUID NOT NULL REFERENCES consultas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Especialidade destino
    especialidade VARCHAR(100) NOT NULL,        -- Ex: "Cardiologia", "Ortopedia"
    profissional_nome VARCHAR(255),             -- Se encaminhar para alguém específico
    
    -- Motivo
    motivo TEXT NOT NULL,
    cid_codigo VARCHAR(10),
    
    -- Urgência
    urgente BOOLEAN DEFAULT false,
    
    -- PDF
    pdf_storage_path TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'emitido' CHECK (status IN (
        'rascunho',
        'emitido',
        'cancelado'
    )),
    
    -- Envio
    enviado_paciente BOOLEAN DEFAULT false,
    enviado_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_encaminhamentos_consulta ON encaminhamentos(consulta_id);
CREATE INDEX idx_encaminhamentos_paciente ON encaminhamentos(paciente_id);


-- ============================================================================
-- 8. TRIGGER: CRIAR CONSULTA QUANDO MÉDICO INICIA ATENDIMENTO
-- ============================================================================

CREATE OR REPLACE FUNCTION on_agendamento_em_atendimento()
RETURNS TRIGGER AS $$
DECLARE
    v_card_id UUID;
BEGIN
    IF NEW.status = 'em_atendimento' AND OLD.status != 'em_atendimento' THEN
        -- Busca o card
        SELECT id INTO v_card_id FROM cards WHERE agendamento_id = NEW.id;
        
        -- Cria a consulta
        INSERT INTO consultas (
            clinica_id,
            agendamento_id,
            card_id,
            paciente_id,
            medico_id,
            iniciada_em,
            status
        ) VALUES (
            NEW.clinica_id,
            NEW.id,
            v_card_id,
            NEW.paciente_id,
            NEW.medico_id,
            NOW(),
            'em_andamento'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_criar_consulta
    AFTER UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION on_agendamento_em_atendimento();


-- ============================================================================
-- 9. TRIGGER: FINALIZAR CONSULTA E CALCULAR DURAÇÃO
-- ============================================================================

CREATE OR REPLACE FUNCTION on_agendamento_atendido()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'atendido' AND OLD.status != 'atendido' THEN
        -- Finaliza a consulta
        UPDATE consultas
        SET 
            finalizada_em = NOW(),
            duracao_minutos = EXTRACT(EPOCH FROM (NOW() - iniciada_em))::INTEGER / 60,
            status = 'finalizada'
        WHERE agendamento_id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_finalizar_consulta
    AFTER UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION on_agendamento_atendido();


-- ============================================================================
-- 10. TRIGGER: CRIAR CARD DERIVADO QUANDO SOLICITAR EXAMES PARA RETORNO
-- ============================================================================
-- Este trigger é chamado quando médico define retorno com exames

CREATE OR REPLACE FUNCTION criar_card_derivado(
    p_consulta_id UUID,
    p_dias_retorno INTEGER DEFAULT 60
)
RETURNS UUID AS $$
DECLARE
    v_consulta RECORD;
    v_card_origem RECORD;
    v_novo_agendamento_id UUID;
    v_novo_card_id UUID;
    v_exame RECORD;
BEGIN
    -- Busca dados da consulta
    SELECT * INTO v_consulta FROM consultas WHERE id = p_consulta_id;
    SELECT * INTO v_card_origem FROM cards WHERE id = v_consulta.card_id;
    
    -- Cria agendamento futuro (data aproximada, paciente reagenda depois)
    INSERT INTO agendamentos (
        clinica_id,
        paciente_id,
        medico_id,
        data,
        hora_inicio,
        hora_fim,
        forma_pagamento,
        status,
        agendamento_origem_id
    ) VALUES (
        v_consulta.clinica_id,
        v_consulta.paciente_id,
        v_consulta.medico_id,
        CURRENT_DATE + (p_dias_retorno || ' days')::INTERVAL,
        '00:00',  -- Hora fictícia, paciente escolhe depois
        '00:30',
        'particular',  -- Atualizado depois
        'agendado',
        (SELECT agendamento_id FROM cards WHERE id = v_card_origem.id)
    ) RETURNING id INTO v_novo_agendamento_id;
    
    -- Busca o card criado automaticamente pelo trigger
    SELECT id INTO v_novo_card_id FROM cards WHERE agendamento_id = v_novo_agendamento_id;
    
    -- Marca como derivado
    UPDATE cards
    SET 
        is_derivado = true,
        card_origem_id = v_card_origem.id
    WHERE id = v_novo_card_id;
    
    -- Atualiza card origem com referência ao derivado
    UPDATE cards
    SET card_derivado_id = v_novo_card_id
    WHERE id = v_card_origem.id;
    
    -- Cria checklist de exames no card derivado
    FOR v_exame IN 
        SELECT * FROM exames_solicitados 
        WHERE consulta_id = p_consulta_id AND para_retorno = true
    LOOP
        INSERT INTO cards_checklist (
            card_id,
            fase,
            tipo,
            descricao,
            obrigatorio,
            referencia_tipo,
            referencia_id
        ) VALUES (
            v_novo_card_id,
            1,  -- Fase 1 (pré-consulta)
            'exame_upload',
            'Enviar: ' || v_exame.nome,
            true,
            'exame_solicitado',
            v_exame.id
        );
    END LOOP;
    
    RETURN v_novo_card_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 11. FUNCTION: BUSCAR HISTÓRICO DO PACIENTE
-- ============================================================================

CREATE OR REPLACE FUNCTION get_historico_paciente(
    p_paciente_id UUID,
    p_medico_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    consulta_id UUID,
    data_consulta TIMESTAMP WITH TIME ZONE,
    medico_nome VARCHAR,
    medico_especialidade VARCHAR,
    resumo TEXT,
    cids JSONB,
    teve_receita BOOLEAN,
    teve_exames BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS consulta_id,
        c.iniciada_em AS data_consulta,
        u.nome AS medico_nome,
        u.especialidade AS medico_especialidade,
        c.resumo,
        COALESCE(ps.cids, '[]'::jsonb) AS cids,
        EXISTS(SELECT 1 FROM receitas r WHERE r.consulta_id = c.id) AS teve_receita,
        EXISTS(SELECT 1 FROM exames_solicitados e WHERE e.consulta_id = c.id) AS teve_exames
    FROM consultas c
    JOIN users u ON u.id = c.medico_id
    LEFT JOIN prontuarios_soap ps ON ps.consulta_id = c.id
    WHERE c.paciente_id = p_paciente_id
      AND c.status = 'finalizada'
      AND (p_medico_id IS NULL OR c.medico_id = p_medico_id)
    ORDER BY c.iniciada_em DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 12. FUNCTION: BUSCAR ÚLTIMA CONSULTA DO PACIENTE
-- ============================================================================

CREATE OR REPLACE FUNCTION get_ultima_consulta(p_paciente_id UUID, p_medico_id UUID)
RETURNS TABLE (
    consulta_id UUID,
    data_consulta TIMESTAMP WITH TIME ZONE,
    resumo TEXT,
    subjetivo TEXT,
    avaliacao TEXT,
    plano TEXT,
    cids JSONB,
    medicamentos JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS consulta_id,
        c.iniciada_em AS data_consulta,
        c.resumo,
        ps.subjetivo,
        ps.avaliacao,
        ps.plano,
        COALESCE(ps.cids, '[]'::jsonb) AS cids,
        COALESCE(
            (SELECT jsonb_agg(r.itens) FROM receitas r WHERE r.consulta_id = c.id),
            '[]'::jsonb
        ) AS medicamentos
    FROM consultas c
    LEFT JOIN prontuarios_soap ps ON ps.consulta_id = c.id
    WHERE c.paciente_id = p_paciente_id
      AND c.medico_id = p_medico_id
      AND c.status = 'finalizada'
    ORDER BY c.iniciada_em DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 13. ROW LEVEL SECURITY (RLS) - NÍVEL CRÍTICO
-- ============================================================================
-- Prontuário: APENAS médico que atendeu pode ver
-- Exceção: Admin não pode ver prontuário (sigilo médico)

ALTER TABLE consultas ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcricoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE prontuarios_soap ENABLE ROW LEVEL SECURITY;
ALTER TABLE receitas ENABLE ROW LEVEL SECURITY;
ALTER TABLE atestados ENABLE ROW LEVEL SECURITY;
ALTER TABLE exames_solicitados ENABLE ROW LEVEL SECURITY;
ALTER TABLE encaminhamentos ENABLE ROW LEVEL SECURITY;

-- Policy: Apenas médico do atendimento ou médico da clínica com flag is_medico
CREATE POLICY "consultas_medico" ON consultas
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()) 
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );

CREATE POLICY "transcricoes_medico" ON transcricoes
    FOR ALL USING (
        consulta_id IN (
            SELECT id FROM consultas 
            WHERE medico_id = auth.uid()
            OR (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()) 
                AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
        )
    );

CREATE POLICY "soap_medico" ON prontuarios_soap
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (consulta_id IN (SELECT id FROM consultas WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );

CREATE POLICY "receitas_medico" ON receitas
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (consulta_id IN (SELECT id FROM consultas WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );

CREATE POLICY "atestados_medico" ON atestados
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (consulta_id IN (SELECT id FROM consultas WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );

CREATE POLICY "exames_sol_medico" ON exames_solicitados
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (consulta_id IN (SELECT id FROM consultas WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );

CREATE POLICY "encaminhamentos_medico" ON encaminhamentos
    FOR ALL USING (
        medico_id = auth.uid() 
        OR 
        (consulta_id IN (SELECT id FROM consultas WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
         AND EXISTS (SELECT 1 FROM users u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = auth.uid() AND p.is_medico = true))
    );


-- ============================================================================
-- FIM DA FASE 4
-- ============================================================================
