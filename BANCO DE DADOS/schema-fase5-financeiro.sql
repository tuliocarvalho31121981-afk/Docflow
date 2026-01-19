-- ============================================================================
-- FASE 5: FINANCEIRO
-- ============================================================================
-- Contas a pagar, contas a receber, fluxo de caixa, conciliação
-- Depende de: clinicas, users, pacientes, consultas, convenios (Fases 1-4)
-- ============================================================================


-- ============================================================================
-- 1. CATEGORIAS FINANCEIRAS
-- ============================================================================
-- Categorias para classificação de receitas e despesas

CREATE TABLE categorias_financeiras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    
    -- Hierarquia (categoria pai)
    categoria_pai_id UUID REFERENCES categorias_financeiras(id),
    
    -- DRE
    grupo_dre VARCHAR(50),                      -- 'receita_operacional', 'custo_fixo', 'custo_variavel', etc
    
    -- Controle
    cor VARCHAR(7) DEFAULT '#6B7280',
    icone VARCHAR(50),
    ativo BOOLEAN DEFAULT true,
    is_sistema BOOLEAN DEFAULT false,           -- Categorias padrão não editáveis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_categorias_clinica ON categorias_financeiras(clinica_id);
CREATE INDEX idx_categorias_tipo ON categorias_financeiras(tipo);


-- ============================================================================
-- 2. FORNECEDORES
-- ============================================================================
-- Cadastro de fornecedores para contas a pagar

CREATE TABLE fornecedores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255),
    tipo_pessoa VARCHAR(2) DEFAULT 'PJ' CHECK (tipo_pessoa IN ('PF', 'PJ')),
    cpf_cnpj VARCHAR(14),                       -- Sem pontuação
    
    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Endereço
    logradouro VARCHAR(255),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(8),
    
    -- Dados bancários (para pagamento)
    banco VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    tipo_conta VARCHAR(20),                     -- 'corrente', 'poupanca'
    pix VARCHAR(100),                           -- Chave PIX
    
    -- Categoria padrão
    categoria_padrao_id UUID REFERENCES categorias_financeiras(id),
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fornecedores_clinica ON fornecedores(clinica_id);
CREATE INDEX idx_fornecedores_cpf_cnpj ON fornecedores(cpf_cnpj);

-- Trigger updated_at
CREATE TRIGGER trigger_fornecedores_updated_at
    BEFORE UPDATE ON fornecedores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 3. CONTAS A PAGAR
-- ============================================================================
-- Despesas da clínica

CREATE TABLE contas_pagar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    descricao VARCHAR(255) NOT NULL,
    fornecedor_id UUID REFERENCES fornecedores(id),
    categoria_id UUID REFERENCES categorias_financeiras(id),
    
    -- Valores
    valor DECIMAL(10,2) NOT NULL,
    valor_pago DECIMAL(10,2),                   -- Se pago parcial
    
    -- Datas
    data_emissao DATE DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    
    -- Recorrência
    recorrente BOOLEAN DEFAULT false,
    recorrencia_tipo VARCHAR(20),               -- 'mensal', 'anual', 'semanal'
    recorrencia_fim DATE,                       -- Até quando repetir
    conta_origem_id UUID REFERENCES contas_pagar(id), -- Se veio de recorrência
    
    -- Documento (scan)
    documento_tipo VARCHAR(30),                 -- 'boleto', 'nf', 'recibo', 'guia', etc
    documento_storage_path TEXT,
    codigo_barras VARCHAR(100),
    
    -- Dados extraídos por IA (do scan)
    dados_ia JSONB,                             -- Campos extraídos pelo OCR
    ia_confianca DECIMAL(3,2),                  -- Score de confiança 0-1
    
    -- Status
    status VARCHAR(30) DEFAULT 'pendente' CHECK (status IN (
        'rascunho',         -- Criado mas não confirmado
        'pendente',         -- Aguardando aprovação ou pagamento
        'aprovado',         -- Aprovado, aguardando pagamento
        'pago',             -- Pago
        'atrasado',         -- Venceu e não pagou
        'cancelado'
    )),
    
    -- Aprovação
    requer_aprovacao BOOLEAN DEFAULT false,
    aprovado_por UUID REFERENCES users(id),
    aprovado_em TIMESTAMP WITH TIME ZONE,
    motivo_reprovacao TEXT,
    
    -- Pagamento
    forma_pagamento VARCHAR(30),                -- 'boleto', 'pix', 'transferencia', 'dinheiro'
    comprovante_storage_path TEXT,
    
    -- Conciliação
    conciliado BOOLEAN DEFAULT false,
    conciliacao_id UUID,                        -- Referência à conciliação (preenchido depois)
    
    -- Controle
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_contas_pagar_clinica ON contas_pagar(clinica_id);
CREATE INDEX idx_contas_pagar_fornecedor ON contas_pagar(fornecedor_id);
CREATE INDEX idx_contas_pagar_categoria ON contas_pagar(categoria_id);
CREATE INDEX idx_contas_pagar_vencimento ON contas_pagar(data_vencimento);
CREATE INDEX idx_contas_pagar_status ON contas_pagar(status);

-- Index para buscar contas vencidas
CREATE INDEX idx_contas_pagar_atrasadas ON contas_pagar(data_vencimento, status) 
    WHERE status IN ('pendente', 'aprovado');

-- Trigger updated_at
CREATE TRIGGER trigger_contas_pagar_updated_at
    BEFORE UPDATE ON contas_pagar
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 4. CONTAS A RECEBER
-- ============================================================================
-- Receitas da clínica (consultas, convênios, etc)

CREATE TABLE contas_receber (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Origem
    origem VARCHAR(30) NOT NULL CHECK (origem IN (
        'consulta',         -- Consulta particular
        'convenio',         -- Faturamento de convênio
        'procedimento',     -- Procedimento avulso
        'outro'
    )),
    
    -- Vínculos (dependendo da origem)
    consulta_id UUID REFERENCES consultas(id),
    paciente_id UUID REFERENCES pacientes(id),
    convenio_id UUID REFERENCES convenios(id),
    
    -- Identificação
    descricao VARCHAR(255) NOT NULL,
    categoria_id UUID REFERENCES categorias_financeiras(id),
    
    -- Valores
    valor DECIMAL(10,2) NOT NULL,
    valor_recebido DECIMAL(10,2),               -- Se recebeu parcial
    desconto DECIMAL(10,2) DEFAULT 0,
    
    -- Datas
    data_emissao DATE DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_recebimento DATE,
    
    -- Convênio (se origem = convenio)
    guia_numero VARCHAR(50),
    lote_id UUID,                               -- Referência ao lote TISS (se houver)
    
    -- Status
    status VARCHAR(30) DEFAULT 'pendente' CHECK (status IN (
        'pendente',         -- Aguardando pagamento
        'parcial',          -- Pago parcialmente
        'pago',             -- Pago integralmente
        'atrasado',         -- Venceu e não pagou
        'glosado',          -- Convênio glosou
        'cancelado'
    )),
    
    -- Pagamento
    forma_pagamento VARCHAR(30),                -- 'pix', 'cartao_credito', 'cartao_debito', 'dinheiro', 'convenio'
    
    -- Cobrança (régua de cobrança)
    cobranca_enviada BOOLEAN DEFAULT false,
    cobranca_ultimo_envio TIMESTAMP WITH TIME ZONE,
    cobranca_quantidade INTEGER DEFAULT 0,      -- Quantas cobranças enviou
    
    -- Conciliação
    conciliado BOOLEAN DEFAULT false,
    conciliacao_id UUID,
    
    -- Controle
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_contas_receber_clinica ON contas_receber(clinica_id);
CREATE INDEX idx_contas_receber_paciente ON contas_receber(paciente_id);
CREATE INDEX idx_contas_receber_convenio ON contas_receber(convenio_id);
CREATE INDEX idx_contas_receber_consulta ON contas_receber(consulta_id);
CREATE INDEX idx_contas_receber_status ON contas_receber(status);
CREATE INDEX idx_contas_receber_vencimento ON contas_receber(data_vencimento);

-- Index para régua de cobrança
CREATE INDEX idx_contas_receber_cobranca ON contas_receber(status, data_vencimento) 
    WHERE status IN ('pendente', 'atrasado');

-- Trigger updated_at
CREATE TRIGGER trigger_contas_receber_updated_at
    BEFORE UPDATE ON contas_receber
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 5. CONTAS_PAGAR_APROVACOES
-- ============================================================================
-- Histórico de aprovações de contas a pagar

CREATE TABLE contas_pagar_aprovacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conta_pagar_id UUID NOT NULL REFERENCES contas_pagar(id) ON DELETE CASCADE,
    
    -- Ação
    acao VARCHAR(20) NOT NULL CHECK (acao IN ('aprovado', 'reprovado', 'solicitado')),
    
    -- Quem
    usuario_id UUID REFERENCES users(id),
    
    -- Detalhes
    comentario TEXT,
    
    -- Quando
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_aprovacoes_conta ON contas_pagar_aprovacoes(conta_pagar_id);


-- ============================================================================
-- 6. CONTAS BANCARIAS
-- ============================================================================
-- Contas bancárias da clínica para conciliação

CREATE TABLE contas_bancarias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Banco
    banco_codigo VARCHAR(10),                   -- Código do banco (001, 341, etc)
    banco_nome VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    tipo VARCHAR(20) DEFAULT 'corrente' CHECK (tipo IN ('corrente', 'poupanca')),
    
    -- Identificação
    apelido VARCHAR(100),                       -- Ex: "Conta Principal", "Conta Reserva"
    
    -- Saldo
    saldo_atual DECIMAL(12,2) DEFAULT 0,
    saldo_atualizado_em TIMESTAMP WITH TIME ZONE,
    
    -- Integração
    integracao_ativa BOOLEAN DEFAULT false,     -- Se importa OFX automaticamente
    
    -- Controle
    principal BOOLEAN DEFAULT false,            -- Conta principal da clínica
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_contas_bancarias_clinica ON contas_bancarias(clinica_id);

-- Trigger updated_at
CREATE TRIGGER trigger_contas_bancarias_updated_at
    BEFORE UPDATE ON contas_bancarias
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 7. EXTRATO_BANCARIO
-- ============================================================================
-- Lançamentos importados do banco (OFX ou manual)

CREATE TABLE extrato_bancario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conta_bancaria_id UUID NOT NULL REFERENCES contas_bancarias(id) ON DELETE CASCADE,
    
    -- Transação
    data DATE NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('credito', 'debito')),
    valor DECIMAL(10,2) NOT NULL,
    
    -- Identificação (do banco)
    id_transacao_banco VARCHAR(100),            -- ID único do banco
    
    -- Conciliação
    conciliado BOOLEAN DEFAULT false,
    conciliacao_id UUID,
    conta_pagar_id UUID REFERENCES contas_pagar(id),
    conta_receber_id UUID REFERENCES contas_receber(id),
    
    -- Se não conciliado, categoria sugerida
    categoria_sugerida_id UUID REFERENCES categorias_financeiras(id),
    
    -- Controle
    importado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    arquivo_origem VARCHAR(255)                 -- Nome do arquivo OFX importado
);

-- Indexes
CREATE INDEX idx_extrato_conta ON extrato_bancario(conta_bancaria_id);
CREATE INDEX idx_extrato_data ON extrato_bancario(data);
CREATE INDEX idx_extrato_conciliado ON extrato_bancario(conciliado);

-- Index para evitar duplicatas
CREATE UNIQUE INDEX idx_extrato_unico ON extrato_bancario(conta_bancaria_id, id_transacao_banco) 
    WHERE id_transacao_banco IS NOT NULL;


-- ============================================================================
-- 8. CONCILIACOES
-- ============================================================================
-- Registro de conciliações realizadas

CREATE TABLE conciliacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Extrato
    extrato_id UUID NOT NULL REFERENCES extrato_bancario(id),
    
    -- Vinculado a
    conta_pagar_id UUID REFERENCES contas_pagar(id),
    conta_receber_id UUID REFERENCES contas_receber(id),
    
    -- Tipo
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN (
        'automatica',       -- Sistema identificou
        'manual',           -- Usuário vinculou
        'tarifa',           -- Tarifa bancária (cria despesa automática)
        'transferencia'     -- Transferência entre contas
    )),
    
    -- Quem conciliou
    conciliado_por UUID REFERENCES users(id),
    conciliado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Observações
    observacao TEXT
);

-- Index
CREATE INDEX idx_conciliacoes_clinica ON conciliacoes(clinica_id);
CREATE INDEX idx_conciliacoes_extrato ON conciliacoes(extrato_id);


-- ============================================================================
-- 9. TRIGGER: CRIAR CONTA A RECEBER APÓS CHECKOUT
-- ============================================================================

CREATE OR REPLACE FUNCTION on_consulta_finalizada_criar_conta()
RETURNS TRIGGER AS $$
DECLARE
    v_agendamento RECORD;
    v_valor DECIMAL(10,2);
BEGIN
    IF NEW.status = 'finalizada' AND OLD.status != 'finalizada' THEN
        -- Busca dados do agendamento
        SELECT * INTO v_agendamento FROM agendamentos WHERE id = NEW.agendamento_id;
        
        -- Define valor
        v_valor := COALESCE(v_agendamento.valor_previsto, 0);
        
        -- Se particular, cria conta a receber
        IF v_agendamento.forma_pagamento = 'particular' AND v_valor > 0 THEN
            INSERT INTO contas_receber (
                clinica_id,
                origem,
                consulta_id,
                paciente_id,
                descricao,
                valor,
                data_vencimento,
                status
            ) VALUES (
                NEW.clinica_id,
                'consulta',
                NEW.id,
                NEW.paciente_id,
                'Consulta - ' || (SELECT nome FROM pacientes WHERE id = NEW.paciente_id),
                v_valor,
                CURRENT_DATE,  -- Vence hoje (pagar na saída)
                'pendente'
            );
        END IF;
        
        -- Se convênio, cria conta a receber com vencimento futuro
        IF v_agendamento.forma_pagamento = 'convenio' AND v_valor > 0 THEN
            INSERT INTO contas_receber (
                clinica_id,
                origem,
                consulta_id,
                paciente_id,
                convenio_id,
                descricao,
                valor,
                data_vencimento,
                status
            ) VALUES (
                NEW.clinica_id,
                'convenio',
                NEW.id,
                NEW.paciente_id,
                v_agendamento.convenio_id,
                'Consulta convênio - ' || (SELECT nome FROM convenios WHERE id = v_agendamento.convenio_id),
                v_valor,
                CURRENT_DATE + INTERVAL '30 days',  -- Prazo padrão convênio
                'pendente'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consulta_criar_conta_receber
    AFTER UPDATE ON consultas
    FOR EACH ROW
    EXECUTE FUNCTION on_consulta_finalizada_criar_conta();


-- ============================================================================
-- 10. TRIGGER: ATUALIZAR STATUS PARA ATRASADO
-- ============================================================================
-- Executar via CRON diariamente

CREATE OR REPLACE FUNCTION atualizar_contas_atrasadas()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
BEGIN
    -- Contas a pagar
    WITH updated AS (
        UPDATE contas_pagar
        SET status = 'atrasado'
        WHERE status IN ('pendente', 'aprovado')
          AND data_vencimento < CURRENT_DATE
        RETURNING id
    )
    SELECT COUNT(*) INTO v_count FROM updated;
    
    -- Contas a receber
    WITH updated AS (
        UPDATE contas_receber
        SET status = 'atrasado'
        WHERE status = 'pendente'
          AND data_vencimento < CURRENT_DATE
        RETURNING id
    )
    SELECT v_count + COUNT(*) INTO v_count FROM updated;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 11. TRIGGER: VERIFICAR APROVAÇÃO NECESSÁRIA
-- ============================================================================

CREATE OR REPLACE FUNCTION verificar_aprovacao_conta_pagar()
RETURNS TRIGGER AS $$
BEGIN
    -- Regras de aprovação por valor
    IF NEW.valor <= 500 THEN
        NEW.requer_aprovacao := false;
        NEW.status := 'aprovado';
    ELSIF NEW.valor <= 2000 THEN
        NEW.requer_aprovacao := true;
        -- Precisa aprovação de gestor
    ELSE
        NEW.requer_aprovacao := true;
        -- Precisa aprovação dupla
    END IF;
    
    -- Exceções: sempre requer aprovação
    IF NEW.fornecedor_id IS NULL THEN
        NEW.requer_aprovacao := true;  -- Fornecedor novo
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_verificar_aprovacao
    BEFORE INSERT ON contas_pagar
    FOR EACH ROW
    EXECUTE FUNCTION verificar_aprovacao_conta_pagar();


-- ============================================================================
-- 12. FUNCTION: FLUXO DE CAIXA PROJETADO
-- ============================================================================

CREATE OR REPLACE FUNCTION get_fluxo_caixa(
    p_clinica_id UUID,
    p_data_inicio DATE DEFAULT CURRENT_DATE,
    p_data_fim DATE DEFAULT CURRENT_DATE + INTERVAL '30 days'
)
RETURNS TABLE (
    data DATE,
    entradas DECIMAL(12,2),
    saidas DECIMAL(12,2),
    saldo_dia DECIMAL(12,2),
    saldo_acumulado DECIMAL(12,2)
) AS $$
DECLARE
    v_saldo_inicial DECIMAL(12,2);
BEGIN
    -- Busca saldo inicial (soma das contas bancárias)
    SELECT COALESCE(SUM(saldo_atual), 0) INTO v_saldo_inicial
    FROM contas_bancarias
    WHERE clinica_id = p_clinica_id AND ativo = true;
    
    RETURN QUERY
    WITH datas AS (
        SELECT generate_series(p_data_inicio, p_data_fim, '1 day'::INTERVAL)::DATE AS dia
    ),
    movimentos AS (
        SELECT 
            d.dia,
            COALESCE(SUM(cr.valor) FILTER (WHERE cr.data_vencimento = d.dia), 0) AS entradas,
            COALESCE(SUM(cp.valor) FILTER (WHERE cp.data_vencimento = d.dia), 0) AS saidas
        FROM datas d
        LEFT JOIN contas_receber cr ON cr.clinica_id = p_clinica_id 
            AND cr.status IN ('pendente', 'parcial')
            AND cr.data_vencimento = d.dia
        LEFT JOIN contas_pagar cp ON cp.clinica_id = p_clinica_id 
            AND cp.status IN ('pendente', 'aprovado')
            AND cp.data_vencimento = d.dia
        GROUP BY d.dia
    )
    SELECT 
        m.dia AS data,
        m.entradas,
        m.saidas,
        (m.entradas - m.saidas) AS saldo_dia,
        v_saldo_inicial + SUM(m.entradas - m.saidas) OVER (ORDER BY m.dia) AS saldo_acumulado
    FROM movimentos m
    ORDER BY m.dia;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 13. FUNCTION: DRE SIMPLIFICADO
-- ============================================================================

CREATE OR REPLACE FUNCTION get_dre_simplificado(
    p_clinica_id UUID,
    p_mes INTEGER,
    p_ano INTEGER
)
RETURNS TABLE (
    descricao VARCHAR,
    valor DECIMAL(12,2),
    percentual DECIMAL(5,2)
) AS $$
DECLARE
    v_receita_bruta DECIMAL(12,2);
    v_receita_liquida DECIMAL(12,2);
BEGIN
    -- Calcula receita bruta
    SELECT COALESCE(SUM(valor_recebido), 0) INTO v_receita_bruta
    FROM contas_receber
    WHERE clinica_id = p_clinica_id
      AND EXTRACT(MONTH FROM data_recebimento) = p_mes
      AND EXTRACT(YEAR FROM data_recebimento) = p_ano
      AND status = 'pago';
    
    RETURN QUERY
    WITH receitas AS (
        SELECT 
            cf.nome AS categoria,
            COALESCE(SUM(cr.valor_recebido), 0) AS total
        FROM contas_receber cr
        LEFT JOIN categorias_financeiras cf ON cf.id = cr.categoria_id
        WHERE cr.clinica_id = p_clinica_id
          AND EXTRACT(MONTH FROM cr.data_recebimento) = p_mes
          AND EXTRACT(YEAR FROM cr.data_recebimento) = p_ano
          AND cr.status = 'pago'
        GROUP BY cf.nome
    ),
    despesas AS (
        SELECT 
            cf.nome AS categoria,
            COALESCE(SUM(cp.valor_pago), 0) AS total
        FROM contas_pagar cp
        LEFT JOIN categorias_financeiras cf ON cf.id = cp.categoria_id
        WHERE cp.clinica_id = p_clinica_id
          AND EXTRACT(MONTH FROM cp.data_pagamento) = p_mes
          AND EXTRACT(YEAR FROM cp.data_pagamento) = p_ano
          AND cp.status = 'pago'
        GROUP BY cf.nome
    )
    -- Receitas
    SELECT '(+) ' || COALESCE(r.categoria, 'Outras receitas'), r.total, 
           CASE WHEN v_receita_bruta > 0 THEN ROUND(r.total / v_receita_bruta * 100, 1) ELSE 0 END
    FROM receitas r
    UNION ALL
    SELECT '= RECEITA BRUTA', v_receita_bruta, 100.0
    UNION ALL
    -- Despesas
    SELECT '(-) ' || COALESCE(d.categoria, 'Outras despesas'), d.total,
           CASE WHEN v_receita_bruta > 0 THEN ROUND(d.total / v_receita_bruta * 100, 1) ELSE 0 END
    FROM despesas d
    UNION ALL
    SELECT '= LUCRO OPERACIONAL', 
           v_receita_bruta - COALESCE((SELECT SUM(total) FROM despesas), 0),
           CASE WHEN v_receita_bruta > 0 
                THEN ROUND((v_receita_bruta - COALESCE((SELECT SUM(total) FROM despesas), 0)) / v_receita_bruta * 100, 1) 
                ELSE 0 END;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 14. FUNCTION: RESUMO FINANCEIRO (DASHBOARD)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_resumo_financeiro(p_clinica_id UUID)
RETURNS TABLE (
    saldo_atual DECIMAL(12,2),
    a_receber_hoje DECIMAL(12,2),
    a_pagar_hoje DECIMAL(12,2),
    a_receber_atrasado DECIMAL(12,2),
    a_pagar_atrasado DECIMAL(12,2),
    receita_mes DECIMAL(12,2),
    despesa_mes DECIMAL(12,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        -- Saldo atual
        COALESCE((SELECT SUM(saldo_atual) FROM contas_bancarias WHERE clinica_id = p_clinica_id AND ativo = true), 0),
        
        -- A receber hoje
        COALESCE((SELECT SUM(valor - COALESCE(valor_recebido, 0)) FROM contas_receber 
                  WHERE clinica_id = p_clinica_id AND data_vencimento = CURRENT_DATE AND status = 'pendente'), 0),
        
        -- A pagar hoje
        COALESCE((SELECT SUM(valor - COALESCE(valor_pago, 0)) FROM contas_pagar 
                  WHERE clinica_id = p_clinica_id AND data_vencimento = CURRENT_DATE AND status IN ('pendente', 'aprovado')), 0),
        
        -- A receber atrasado
        COALESCE((SELECT SUM(valor - COALESCE(valor_recebido, 0)) FROM contas_receber 
                  WHERE clinica_id = p_clinica_id AND status = 'atrasado'), 0),
        
        -- A pagar atrasado
        COALESCE((SELECT SUM(valor - COALESCE(valor_pago, 0)) FROM contas_pagar 
                  WHERE clinica_id = p_clinica_id AND status = 'atrasado'), 0),
        
        -- Receita do mês
        COALESCE((SELECT SUM(valor_recebido) FROM contas_receber 
                  WHERE clinica_id = p_clinica_id 
                    AND EXTRACT(MONTH FROM data_recebimento) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM data_recebimento) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND status = 'pago'), 0),
        
        -- Despesa do mês
        COALESCE((SELECT SUM(valor_pago) FROM contas_pagar 
                  WHERE clinica_id = p_clinica_id 
                    AND EXTRACT(MONTH FROM data_pagamento) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM data_pagamento) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND status = 'pago'), 0);
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 15. CATEGORIAS PADRÃO (SEED)
-- ============================================================================

CREATE OR REPLACE FUNCTION criar_categorias_padrao(p_clinica_id UUID)
RETURNS void AS $$
BEGIN
    -- RECEITAS
    INSERT INTO categorias_financeiras (clinica_id, nome, tipo, grupo_dre, is_sistema) VALUES
    (p_clinica_id, 'Consultas Particulares', 'receita', 'receita_operacional', true),
    (p_clinica_id, 'Consultas Convênio', 'receita', 'receita_operacional', true),
    (p_clinica_id, 'Procedimentos', 'receita', 'receita_operacional', true),
    (p_clinica_id, 'Outras Receitas', 'receita', 'outras_receitas', true);
    
    -- DESPESAS
    INSERT INTO categorias_financeiras (clinica_id, nome, tipo, grupo_dre, is_sistema) VALUES
    (p_clinica_id, 'Aluguel', 'despesa', 'custo_fixo', true),
    (p_clinica_id, 'Condomínio', 'despesa', 'custo_fixo', true),
    (p_clinica_id, 'Energia', 'despesa', 'custo_fixo', true),
    (p_clinica_id, 'Água', 'despesa', 'custo_fixo', true),
    (p_clinica_id, 'Internet/Telefone', 'despesa', 'custo_fixo', true),
    (p_clinica_id, 'Salários', 'despesa', 'pessoal', true),
    (p_clinica_id, 'Encargos (FGTS/INSS)', 'despesa', 'pessoal', true),
    (p_clinica_id, 'Vale Transporte', 'despesa', 'pessoal', true),
    (p_clinica_id, 'Vale Refeição', 'despesa', 'pessoal', true),
    (p_clinica_id, 'Material Médico', 'despesa', 'custo_variavel', true),
    (p_clinica_id, 'Material Escritório', 'despesa', 'custo_variavel', true),
    (p_clinica_id, 'Limpeza', 'despesa', 'custo_variavel', true),
    (p_clinica_id, 'Impostos (DAS)', 'despesa', 'impostos', true),
    (p_clinica_id, 'Impostos (ISS)', 'despesa', 'impostos', true),
    (p_clinica_id, 'Manutenção', 'despesa', 'operacional', true),
    (p_clinica_id, 'Marketing', 'despesa', 'operacional', true),
    (p_clinica_id, 'Software/Sistemas', 'despesa', 'operacional', true),
    (p_clinica_id, 'Tarifas Bancárias', 'despesa', 'financeiro', true),
    (p_clinica_id, 'Outras Despesas', 'despesa', 'outras_despesas', true);
END;
$$ LANGUAGE plpgsql;

-- Adiciona ao trigger de criação de clínica
CREATE OR REPLACE FUNCTION on_clinica_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM criar_perfis_padrao(NEW.id);
    PERFORM criar_tipos_consulta_padrao(NEW.id);
    PERFORM criar_categorias_padrao(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 16. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE categorias_financeiras ENABLE ROW LEVEL SECURITY;
ALTER TABLE fornecedores ENABLE ROW LEVEL SECURITY;
ALTER TABLE contas_pagar ENABLE ROW LEVEL SECURITY;
ALTER TABLE contas_receber ENABLE ROW LEVEL SECURITY;
ALTER TABLE contas_pagar_aprovacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE contas_bancarias ENABLE ROW LEVEL SECURITY;
ALTER TABLE extrato_bancario ENABLE ROW LEVEL SECURITY;
ALTER TABLE conciliacoes ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "categorias_clinica" ON categorias_financeiras
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "fornecedores_clinica" ON fornecedores
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "contas_pagar_clinica" ON contas_pagar
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "contas_receber_clinica" ON contas_receber
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "aprovacoes_clinica" ON contas_pagar_aprovacoes
    FOR ALL USING (
        conta_pagar_id IN (SELECT id FROM contas_pagar WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
    );

CREATE POLICY "contas_bancarias_clinica" ON contas_bancarias
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

CREATE POLICY "extrato_clinica" ON extrato_bancario
    FOR ALL USING (
        conta_bancaria_id IN (SELECT id FROM contas_bancarias WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
    );

CREATE POLICY "conciliacoes_clinica" ON conciliacoes
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));


-- ============================================================================
-- FIM DA FASE 5
-- ============================================================================
