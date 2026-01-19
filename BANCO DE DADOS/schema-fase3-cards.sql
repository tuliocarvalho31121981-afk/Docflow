-- ============================================================================
-- FASE 3: CARDS (JORNADA KANBAN)
-- ============================================================================
-- Sistema de cards que acompanha o paciente pela jornada
-- Depende de: clinicas, users, pacientes, agendamentos (Fases 1-2)
-- ============================================================================


-- ============================================================================
-- 1. CARDS
-- ============================================================================
-- Objeto central do Kanban. Cada agendamento gera um card.
-- Card acompanha o paciente desde o agendamento até pós-consulta.

CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Vínculos
    agendamento_id UUID NOT NULL REFERENCES agendamentos(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    medico_id UUID NOT NULL REFERENCES users(id),
    
    -- Posição no Kanban
    fase INTEGER NOT NULL DEFAULT 0 CHECK (fase BETWEEN 0 AND 3),
    -- 0 = Agendado (futuro)
    -- 1 = Pré-Consulta (D-3 até D-1)
    -- 2 = Dia da Consulta
    -- 3 = Pós-Consulta
    
    coluna VARCHAR(50) NOT NULL DEFAULT 'agendado',
    -- Colunas por fase:
    -- Fase 0: agendado
    -- Fase 1: pendente_anamnese, pendente_confirmacao, pronto
    -- Fase 2: aguardando_checkin, em_espera, em_atendimento, finalizado
    -- Fase 3: pendente_documentos, pendente_pagamento, concluido
    
    posicao INTEGER DEFAULT 0,                  -- Ordem dentro da coluna
    
    -- Status geral do card
    status VARCHAR(30) DEFAULT 'ativo' CHECK (status IN (
        'ativo',        -- Em andamento
        'concluido',    -- Jornada completa
        'cancelado',    -- Cancelado
        'no_show'       -- Paciente faltou
    )),
    
    -- Indicadores visuais (cor do card)
    prioridade VARCHAR(20) DEFAULT 'normal' CHECK (prioridade IN ('baixa', 'normal', 'alta', 'urgente')),
    cor_alerta VARCHAR(20),                     -- 'amarelo', 'vermelho' (tempo de espera)
    
    -- Timestamps da jornada
    fase0_em TIMESTAMP WITH TIME ZONE,          -- Quando entrou na fase 0
    fase1_em TIMESTAMP WITH TIME ZONE,          -- Quando entrou na fase 1
    fase2_em TIMESTAMP WITH TIME ZONE,          -- Quando entrou na fase 2
    fase3_em TIMESTAMP WITH TIME ZONE,          -- Quando entrou na fase 3
    concluido_em TIMESTAMP WITH TIME ZONE,      -- Quando finalizou tudo
    
    -- Card derivado (retorno com exames)
    is_derivado BOOLEAN DEFAULT false,          -- Este card veio de outro?
    card_origem_id UUID REFERENCES cards(id),   -- Card que originou este
    card_derivado_id UUID,                      -- Card filho gerado (atualizado depois)
    
    -- Dados copiados para performance (evita joins)
    paciente_nome VARCHAR(255),
    paciente_telefone VARCHAR(20),
    data_agendamento DATE,
    hora_agendamento TIME,
    tipo_consulta VARCHAR(100),
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cards_clinica ON cards(clinica_id);
CREATE INDEX idx_cards_agendamento ON cards(agendamento_id);
CREATE INDEX idx_cards_paciente ON cards(paciente_id);
CREATE INDEX idx_cards_medico ON cards(medico_id);
CREATE INDEX idx_cards_fase ON cards(fase);
CREATE INDEX idx_cards_coluna ON cards(coluna);
CREATE INDEX idx_cards_status ON cards(status);
CREATE INDEX idx_cards_data ON cards(data_agendamento);

-- Index composto para buscar cards ativos de um médico em uma data
CREATE INDEX idx_cards_medico_data_status ON cards(medico_id, data_agendamento, status);

-- Index para buscar cards derivados
CREATE INDEX idx_cards_origem ON cards(card_origem_id);

-- Trigger updated_at
CREATE TRIGGER trigger_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 2. CARDS_CHECKLIST
-- ============================================================================
-- Itens que precisam ser completados em cada fase.
-- Sistema marca automaticamente, mas pode ter intervenção manual.

CREATE TABLE cards_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    
    -- Item
    fase INTEGER NOT NULL CHECK (fase BETWEEN 0 AND 3),
    tipo VARCHAR(50) NOT NULL,                  -- Tipo do item (ver comentário)
    descricao VARCHAR(255) NOT NULL,            -- Texto exibido
    
    -- Status
    obrigatorio BOOLEAN DEFAULT true,           -- Bloqueia avanço se não concluído?
    concluido BOOLEAN DEFAULT false,
    concluido_em TIMESTAMP WITH TIME ZONE,
    
    -- Quem concluiu
    concluido_por_user UUID REFERENCES users(id),
    concluido_por_paciente BOOLEAN DEFAULT false,
    concluido_por_sistema BOOLEAN DEFAULT false,
    
    -- Referência ao objeto relacionado (se aplicável)
    referencia_tipo VARCHAR(50),                -- 'anamnese', 'documento', 'pagamento'
    referencia_id UUID,                         -- ID do objeto
    
    -- Ordem de exibição
    posicao INTEGER DEFAULT 0,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_checklist_card ON cards_checklist(card_id);
CREATE INDEX idx_checklist_fase ON cards_checklist(card_id, fase);
CREATE INDEX idx_checklist_pendentes ON cards_checklist(card_id, concluido) WHERE NOT concluido;

-- Comentário sobre tipos
COMMENT ON COLUMN cards_checklist.tipo IS '
Tipos por fase:

FASE 0 (Agendado):
- confirmacao: Aguardando confirmação do paciente

FASE 1 (Pré-Consulta):
- anamnese: Preencher anamnese
- exame_upload: Upload de exame específico (pode ter vários)
- documento: Enviar documento solicitado

FASE 2 (Dia da Consulta):
- checkin: Fazer check-in na clínica
- pagamento_previo: Pagar antes (se particular)

FASE 3 (Pós-Consulta):
- documento_envio: Enviar documento ao paciente
- pagamento: Pagamento pendente
- guia_convenio: Enviar guia ao convênio
- retorno: Agendar retorno
- exame_cobranca: Cobrar exame para retorno
';


-- ============================================================================
-- 3. CARDS_DOCUMENTOS
-- ============================================================================
-- Arquivos anexados ao card (exames enviados pelo paciente, docs gerados)

CREATE TABLE cards_documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    
    -- Documento
    tipo VARCHAR(50) NOT NULL,                  -- 'exame', 'laudo', 'receita', 'atestado', 'guia', 'outro'
    nome VARCHAR(255) NOT NULL,                 -- Nome do arquivo
    descricao TEXT,
    
    -- Storage
    storage_path TEXT NOT NULL,                 -- Caminho no Supabase Storage
    mime_type VARCHAR(100),
    tamanho_bytes INTEGER,
    
    -- Metadados extraídos (se exame)
    exame_tipo VARCHAR(100),                    -- Tipo do exame (ECG, Hemograma, etc)
    exame_data DATE,                            -- Data do exame
    exame_laboratorio VARCHAR(255),             -- Onde foi feito
    
    -- Match com exame solicitado
    exame_solicitado_id UUID,                   -- Referência ao exame pedido (preenchido depois)
    match_status VARCHAR(20) DEFAULT 'pendente' CHECK (match_status IN (
        'pendente',     -- Ainda não verificado
        'matched',      -- Corresponde a um exame solicitado
        'extra'         -- Não foi solicitado, paciente enviou por conta
    )),
    
    -- Quem enviou
    uploaded_by_user UUID REFERENCES users(id),
    uploaded_by_paciente BOOLEAN DEFAULT false,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_card_docs_card ON cards_documentos(card_id);
CREATE INDEX idx_card_docs_tipo ON cards_documentos(tipo);


-- ============================================================================
-- 4. CARDS_MENSAGENS
-- ============================================================================
-- Histórico de mensagens enviadas/recebidas do paciente via WhatsApp

CREATE TABLE cards_mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    
    -- Mensagem
    direcao VARCHAR(10) NOT NULL CHECK (direcao IN ('enviada', 'recebida')),
    tipo VARCHAR(30) NOT NULL,                  -- 'confirmacao', 'lembrete', 'cobranca', 'documento', 'manual'
    conteudo TEXT,                              -- Texto da mensagem
    
    -- Template (se foi mensagem de template)
    template_nome VARCHAR(100),
    
    -- Status de entrega (WhatsApp)
    status_entrega VARCHAR(20) DEFAULT 'enviada' CHECK (status_entrega IN (
        'enviada',      -- Enviada ao WhatsApp
        'entregue',     -- Entregue ao telefone
        'lida',         -- Lida pelo paciente
        'falhou'        -- Falha no envio
    )),
    
    -- Resposta do paciente (se recebida)
    resposta_esperada VARCHAR(50),              -- 'confirmacao', 'livre'
    resposta_processada BOOLEAN DEFAULT false,
    
    -- Controle
    enviada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    entregue_em TIMESTAMP WITH TIME ZONE,
    lida_em TIMESTAMP WITH TIME ZONE,
    
    -- Quem enviou (se manual)
    enviada_por_user UUID REFERENCES users(id),
    enviada_por_sistema BOOLEAN DEFAULT true
);

-- Indexes
CREATE INDEX idx_card_msgs_card ON cards_mensagens(card_id);
CREATE INDEX idx_card_msgs_tipo ON cards_mensagens(tipo);


-- ============================================================================
-- 5. CARDS_HISTORICO
-- ============================================================================
-- Log de movimentações do card no Kanban

CREATE TABLE cards_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    
    -- Mudança
    acao VARCHAR(50) NOT NULL,                  -- 'criado', 'movido', 'status_alterado', 'checklist_item', etc
    
    -- Detalhes da mudança
    fase_anterior INTEGER,
    fase_nova INTEGER,
    coluna_anterior VARCHAR(50),
    coluna_nova VARCHAR(50),
    status_anterior VARCHAR(30),
    status_novo VARCHAR(30),
    
    -- Contexto adicional
    detalhes JSONB,                             -- Dados extras da ação
    
    -- Quem fez
    created_by_user UUID REFERENCES users(id),
    created_by_paciente BOOLEAN DEFAULT false,
    created_by_sistema BOOLEAN DEFAULT false,
    
    -- Quando
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_card_hist_card ON cards_historico(card_id);
CREATE INDEX idx_card_hist_acao ON cards_historico(acao);


-- ============================================================================
-- 6. ANAMNESES
-- ============================================================================
-- Respostas do questionário de pré-consulta

CREATE TABLE anamneses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id),
    
    -- Queixa principal
    queixa_principal TEXT NOT NULL,
    duracao_sintomas VARCHAR(100),              -- "2 dias", "1 semana", etc
    
    -- Histórico médico
    doencas_cronicas TEXT[],                    -- Array de doenças
    cirurgias_previas TEXT,
    internacoes_previas TEXT,
    
    -- Histórico familiar
    historico_familiar JSONB,                   -- { "diabetes": true, "hipertensao": true, ... }
    
    -- Hábitos
    fumante VARCHAR(20),                        -- 'nunca', 'ex', 'atual'
    etilista VARCHAR(20),                       -- 'nunca', 'social', 'frequente'
    atividade_fisica VARCHAR(50),               -- 'sedentario', 'leve', 'moderado', 'intenso'
    
    -- Medicamentos (além dos de uso contínuo)
    medicamentos_atuais TEXT,                   -- Texto livre
    
    -- Outras informações
    observacoes TEXT,
    
    -- Status
    completa BOOLEAN DEFAULT false,
    
    -- Quem preencheu
    preenchida_por_paciente BOOLEAN DEFAULT true,
    preenchida_por_user UUID REFERENCES users(id),
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_anamneses_card ON anamneses(card_id);
CREATE INDEX idx_anamneses_paciente ON anamneses(paciente_id);

-- Trigger updated_at
CREATE TRIGGER trigger_anamneses_updated_at
    BEFORE UPDATE ON anamneses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 7. TRIGGER: CRIAR CARD AO CRIAR AGENDAMENTO
-- ============================================================================

CREATE OR REPLACE FUNCTION on_agendamento_created()
RETURNS TRIGGER AS $$
DECLARE
    v_paciente RECORD;
    v_tipo_consulta RECORD;
BEGIN
    -- Busca dados do paciente
    SELECT nome, telefone INTO v_paciente 
    FROM pacientes WHERE id = NEW.paciente_id;
    
    -- Busca tipo de consulta
    SELECT nome INTO v_tipo_consulta 
    FROM tipos_consulta WHERE id = NEW.tipo_consulta_id;
    
    -- Cria o card
    INSERT INTO cards (
        clinica_id,
        agendamento_id,
        paciente_id,
        medico_id,
        fase,
        coluna,
        fase0_em,
        paciente_nome,
        paciente_telefone,
        data_agendamento,
        hora_agendamento,
        tipo_consulta
    ) VALUES (
        NEW.clinica_id,
        NEW.id,
        NEW.paciente_id,
        NEW.medico_id,
        0,
        'agendado',
        NOW(),
        v_paciente.nome,
        v_paciente.telefone,
        NEW.data,
        NEW.hora_inicio,
        v_tipo_consulta.nome
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agendamento_criar_card
    AFTER INSERT ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION on_agendamento_created();


-- ============================================================================
-- 8. TRIGGER: CRIAR CHECKLIST PADRÃO AO CRIAR CARD
-- ============================================================================

CREATE OR REPLACE FUNCTION on_card_created()
RETURNS TRIGGER AS $$
BEGIN
    -- Fase 0: Confirmação
    INSERT INTO cards_checklist (card_id, fase, tipo, descricao, posicao)
    VALUES (NEW.id, 0, 'confirmacao', 'Aguardando confirmação do paciente', 1);
    
    -- Fase 1: Pré-consulta
    INSERT INTO cards_checklist (card_id, fase, tipo, descricao, posicao)
    VALUES 
        (NEW.id, 1, 'anamnese', 'Preencher anamnese', 1);
    
    -- Fase 2: Dia da consulta
    INSERT INTO cards_checklist (card_id, fase, tipo, descricao, posicao)
    VALUES (NEW.id, 2, 'checkin', 'Fazer check-in na clínica', 1);
    
    -- Fase 3: Pós-consulta (criados dinamicamente após consulta)
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_card_criar_checklist
    AFTER INSERT ON cards
    FOR EACH ROW
    EXECUTE FUNCTION on_card_created();


-- ============================================================================
-- 9. TRIGGER: ATUALIZAR CARD QUANDO AGENDAMENTO MUDA STATUS
-- ============================================================================

CREATE OR REPLACE FUNCTION on_agendamento_status_change_update_card()
RETURNS TRIGGER AS $$
BEGIN
    -- Confirmado → Marca checklist
    IF NEW.status = 'confirmado' AND OLD.status != 'confirmado' THEN
        UPDATE cards_checklist 
        SET concluido = true, 
            concluido_em = NOW(), 
            concluido_por_paciente = true
        WHERE card_id = (SELECT id FROM cards WHERE agendamento_id = NEW.id)
          AND tipo = 'confirmacao';
    END IF;
    
    -- Check-in (aguardando) → Move card para fase 2
    IF NEW.status = 'aguardando' AND OLD.status != 'aguardando' THEN
        UPDATE cards 
        SET fase = 2, 
            coluna = 'em_espera',
            fase2_em = NOW()
        WHERE agendamento_id = NEW.id;
        
        UPDATE cards_checklist 
        SET concluido = true, 
            concluido_em = NOW(), 
            concluido_por_paciente = true
        WHERE card_id = (SELECT id FROM cards WHERE agendamento_id = NEW.id)
          AND tipo = 'checkin';
    END IF;
    
    -- Em atendimento → Atualiza coluna
    IF NEW.status = 'em_atendimento' AND OLD.status != 'em_atendimento' THEN
        UPDATE cards 
        SET coluna = 'em_atendimento'
        WHERE agendamento_id = NEW.id;
    END IF;
    
    -- Atendido → Move para fase 3
    IF NEW.status = 'atendido' AND OLD.status != 'atendido' THEN
        UPDATE cards 
        SET fase = 3, 
            coluna = 'pendente_documentos',
            fase3_em = NOW()
        WHERE agendamento_id = NEW.id;
    END IF;
    
    -- Cancelado → Atualiza card
    IF NEW.status = 'cancelado' THEN
        UPDATE cards 
        SET status = 'cancelado'
        WHERE agendamento_id = NEW.id;
    END IF;
    
    -- Faltou → Atualiza card
    IF NEW.status = 'faltou' THEN
        UPDATE cards 
        SET status = 'no_show'
        WHERE agendamento_id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agendamento_atualiza_card
    AFTER UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION on_agendamento_status_change_update_card();


-- ============================================================================
-- 10. FUNCTION: MOVER CARDS PARA FASE 1 (CRON DIÁRIO)
-- ============================================================================
-- Executar via pg_cron ou Edge Function diariamente

CREATE OR REPLACE FUNCTION mover_cards_para_pre_consulta()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Move cards que estão a 3 dias ou menos da consulta para fase 1
    WITH cards_para_mover AS (
        UPDATE cards
        SET fase = 1,
            coluna = 'pendente_anamnese',
            fase1_em = NOW()
        WHERE fase = 0
          AND status = 'ativo'
          AND data_agendamento <= CURRENT_DATE + INTERVAL '3 days'
          AND data_agendamento >= CURRENT_DATE
        RETURNING id
    )
    SELECT COUNT(*) INTO v_count FROM cards_para_mover;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 11. FUNCTION: MOVER CARDS PARA DIA DA CONSULTA (CRON DIÁRIO)
-- ============================================================================

CREATE OR REPLACE FUNCTION mover_cards_para_dia_consulta()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Move cards do dia para fase 2
    WITH cards_para_mover AS (
        UPDATE cards
        SET fase = 2,
            coluna = 'aguardando_checkin',
            fase2_em = NOW()
        WHERE fase IN (0, 1)
          AND status = 'ativo'
          AND data_agendamento = CURRENT_DATE
        RETURNING id
    )
    SELECT COUNT(*) INTO v_count FROM cards_para_mover;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 12. FUNCTION: BUSCAR CARDS DO KANBAN
-- ============================================================================

CREATE OR REPLACE FUNCTION get_cards_kanban(
    p_clinica_id UUID,
    p_medico_id UUID DEFAULT NULL,
    p_data DATE DEFAULT NULL,
    p_fase INTEGER DEFAULT NULL
)
RETURNS TABLE (
    card_id UUID,
    fase INTEGER,
    coluna VARCHAR,
    status VARCHAR,
    prioridade VARCHAR,
    cor_alerta VARCHAR,
    paciente_nome VARCHAR,
    paciente_telefone VARCHAR,
    data_agendamento DATE,
    hora_agendamento TIME,
    tipo_consulta VARCHAR,
    medico_id UUID,
    checklist_total INTEGER,
    checklist_concluido INTEGER,
    tempo_espera_minutos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS card_id,
        c.fase,
        c.coluna,
        c.status,
        c.prioridade,
        c.cor_alerta,
        c.paciente_nome,
        c.paciente_telefone,
        c.data_agendamento,
        c.hora_agendamento,
        c.tipo_consulta,
        c.medico_id,
        (SELECT COUNT(*)::INTEGER FROM cards_checklist WHERE card_id = c.id AND fase = c.fase) AS checklist_total,
        (SELECT COUNT(*)::INTEGER FROM cards_checklist WHERE card_id = c.id AND fase = c.fase AND concluido) AS checklist_concluido,
        CASE 
            WHEN c.coluna = 'em_espera' THEN
                EXTRACT(EPOCH FROM (NOW() - (SELECT checkin_em FROM agendamentos WHERE id = c.agendamento_id)))::INTEGER / 60
            ELSE NULL
        END AS tempo_espera_minutos
    FROM cards c
    WHERE c.clinica_id = p_clinica_id
      AND c.status = 'ativo'
      AND (p_medico_id IS NULL OR c.medico_id = p_medico_id)
      AND (p_data IS NULL OR c.data_agendamento = p_data)
      AND (p_fase IS NULL OR c.fase = p_fase)
    ORDER BY c.fase, c.posicao, c.hora_agendamento;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 13. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards_checklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards_documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards_mensagens ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE anamneses ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "cards_clinica" ON cards
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "cards_checklist_clinica" ON cards_checklist
    FOR ALL USING (card_id IN (SELECT id FROM cards WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())));

CREATE POLICY "cards_documentos_clinica" ON cards_documentos
    FOR ALL USING (card_id IN (SELECT id FROM cards WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())));

CREATE POLICY "cards_mensagens_clinica" ON cards_mensagens
    FOR ALL USING (card_id IN (SELECT id FROM cards WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())));

CREATE POLICY "cards_historico_clinica" ON cards_historico
    FOR ALL USING (card_id IN (SELECT id FROM cards WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())));

CREATE POLICY "anamneses_clinica" ON anamneses
    FOR ALL USING (card_id IN (SELECT id FROM cards WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())));


-- ============================================================================
-- FIM DA FASE 3
-- ============================================================================
