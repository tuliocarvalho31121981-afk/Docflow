-- ============================================================================
-- FASE 7: EVIDÊNCIAS
-- ============================================================================
-- Provas documentais de ações no sistema.
-- Complementa audit_logs (que registra AÇÕES) com PROVAS das ações.
-- Baseado em melhores práticas HIPAA, LGPD e padrões de auditoria.
-- ============================================================================


-- ============================================================================
-- 1. EVIDENCIAS
-- ============================================================================
-- Armazena metadados e referências às provas documentais.
-- Arquivos físicos ficam no Supabase Storage.

CREATE TABLE evidencias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Vínculo com entidade (polimórfico)
    entidade VARCHAR(50) NOT NULL,              -- Nome da tabela: 'contas_pagar', 'agendamentos', etc
    entidade_id UUID NOT NULL,                  -- ID do registro na tabela
    
    -- Tipo de evidência
    tipo VARCHAR(50) NOT NULL,                  -- Ver comentário abaixo
    categoria VARCHAR(30) NOT NULL CHECK (categoria IN (
        'documento',        -- Arquivo (PDF, imagem)
        'api_response',     -- Resposta de API externa
        'assinatura',       -- Assinatura digital
        'comprovante',      -- Comprovante de pagamento
        'log_sistema',      -- Log estruturado do sistema
        'mensagem',         -- Mensagem WhatsApp/email
        'formulario'        -- Dados preenchidos (anamnese, etc)
    )),
    
    -- Descrição
    descricao VARCHAR(255),
    
    -- Arquivo (se categoria = documento, comprovante, assinatura)
    arquivo_nome VARCHAR(255),                  -- Nome original do arquivo
    arquivo_path TEXT,                          -- Caminho no Supabase Storage
    arquivo_mime_type VARCHAR(100),
    arquivo_tamanho_bytes INTEGER,
    arquivo_hash VARCHAR(64),                   -- SHA-256 para integridade
    
    -- Dados estruturados (se categoria = api_response, log_sistema, formulario)
    dados JSONB,
    
    -- Origem
    origem VARCHAR(50) NOT NULL CHECK (origem IN (
        'usuario',          -- Usuário fez upload
        'paciente',         -- Paciente enviou
        'sistema',          -- Sistema gerou automaticamente
        'api_externa',      -- Resposta de API externa
        'ia'                -- IA processou/gerou
    )),
    
    -- Validação
    validado BOOLEAN DEFAULT false,             -- Foi validado/verificado?
    validado_por UUID REFERENCES users(id),
    validado_em TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN (
        'ativo',
        'substituido',      -- Foi substituído por versão mais recente
        'invalido'          -- Marcado como inválido
    )),
    substituido_por UUID REFERENCES evidencias(id),
    
    -- Vínculo com audit_log (qual ação gerou esta evidência)
    audit_log_id UUID REFERENCES audit_logs(id),
    
    -- Retenção
    retencao_ate DATE,                          -- Até quando manter
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id),
    created_by_paciente BOOLEAN DEFAULT false,
    created_by_sistema BOOLEAN DEFAULT false
);

-- Indexes
CREATE INDEX idx_evidencias_clinica ON evidencias(clinica_id);
CREATE INDEX idx_evidencias_entidade ON evidencias(entidade, entidade_id);
CREATE INDEX idx_evidencias_tipo ON evidencias(tipo);
CREATE INDEX idx_evidencias_categoria ON evidencias(categoria);
CREATE INDEX idx_evidencias_status ON evidencias(status);

-- Index para buscar evidências ativas de uma entidade
CREATE INDEX idx_evidencias_entidade_ativa ON evidencias(entidade, entidade_id, status) 
    WHERE status = 'ativo';

-- Comentário sobre tipos
COMMENT ON COLUMN evidencias.tipo IS '
Tipos de evidência por entidade:

AGENDAMENTOS:
- elegibilidade_convenio: Resposta da API do convênio confirmando elegibilidade
- confirmacao_paciente: Registro da confirmação via WhatsApp

CONTAS_PAGAR:
- nota_fiscal: NF (PDF/XML)
- boleto: Boleto bancário (PDF)
- recibo: Recibo de pagamento
- comprovante_pagamento: Comprovante de transferência/PIX
- aprovacao: Log da aprovação

CONTAS_RECEBER:
- comprovante_pagamento: Comprovante recebido do paciente
- guia_convenio: Guia TISS enviada

CONSULTAS:
- transcricao_audio: Arquivo de áudio original
- transcricao_texto: Texto transcrito

RECEITAS:
- pdf_assinado: PDF da receita assinada
- assinatura_digital: Certificado ICP-Brasil

ATESTADOS:
- pdf_assinado: PDF do atestado assinado

EXAMES_SOLICITADOS:
- guia_sadt: Guia SADT gerada
- resultado: Resultado do exame recebido

ANAMNESES:
- formulario_preenchido: Dados da anamnese

CONSENTIMENTOS:
- termo_aceito: Registro do aceite
- assinatura: Assinatura do paciente (se presencial)
';


-- ============================================================================
-- 2. EVIDENCIAS_OBRIGATORIAS
-- ============================================================================
-- Define quais ações exigem quais evidências.
-- Usado pelo backend para validar antes de permitir ação.

CREATE TABLE evidencias_obrigatorias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Regra
    entidade VARCHAR(50) NOT NULL,              -- Tabela: 'contas_pagar', 'receitas', etc
    acao VARCHAR(50) NOT NULL,                  -- Ação: 'criar', 'pagar', 'emitir', 'aprovar'
    
    -- Evidências necessárias
    tipos_evidencia TEXT[] NOT NULL,            -- Array de tipos: ['nota_fiscal', 'boleto']
    quantidade_minima INTEGER DEFAULT 1,        -- Quantas evidências desse grupo são necessárias
    logica VARCHAR(10) DEFAULT 'OR' CHECK (logica IN ('AND', 'OR')),
    -- AND = precisa de TODAS as evidências listadas
    -- OR = precisa de PELO MENOS UMA das evidências listadas
    
    -- Exceções
    excecao_perfis TEXT[],                      -- Perfis que não precisam dessa evidência
    excecao_valor_ate DECIMAL(10,2),            -- Se valor <= X, não exige
    
    -- Mensagem de erro
    mensagem_erro VARCHAR(255) NOT NULL,
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_evid_obrig_entidade_acao ON evidencias_obrigatorias(entidade, acao);

-- Inserir regras padrão
INSERT INTO evidencias_obrigatorias (entidade, acao, tipos_evidencia, logica, mensagem_erro) VALUES
-- Contas a Pagar
('contas_pagar', 'criar', ARRAY['nota_fiscal', 'boleto', 'recibo'], 'OR', 
 'É necessário anexar NF, boleto ou recibo para criar conta a pagar'),
('contas_pagar', 'pagar', ARRAY['comprovante_pagamento'], 'AND', 
 'É necessário anexar comprovante de pagamento'),
('contas_pagar', 'aprovar', ARRAY['aprovacao'], 'AND', 
 'Log de aprovação é obrigatório'),

-- Contas a Receber (particular)
('contas_receber', 'receber', ARRAY['comprovante_pagamento'], 'AND', 
 'É necessário anexar comprovante de pagamento'),

-- Agendamentos (convênio)
('agendamentos', 'confirmar_convenio', ARRAY['elegibilidade_convenio'], 'AND', 
 'É necessário verificar elegibilidade do convênio'),

-- Receitas
('receitas', 'emitir', ARRAY['pdf_assinado'], 'AND', 
 'É necessário gerar o PDF da receita'),

-- Atestados
('atestados', 'emitir', ARRAY['pdf_assinado'], 'AND', 
 'É necessário gerar o PDF do atestado'),

-- Consentimentos
('consentimentos', 'registrar', ARRAY['termo_aceito', 'assinatura', 'mensagem_whatsapp'], 'OR', 
 'É necessário registrar evidência do consentimento');


-- ============================================================================
-- 3. FUNCTION: VERIFICAR EVIDÊNCIAS
-- ============================================================================
-- Verifica se uma entidade tem as evidências obrigatórias para uma ação

CREATE OR REPLACE FUNCTION verificar_evidencias(
    p_entidade VARCHAR,
    p_entidade_id UUID,
    p_acao VARCHAR,
    p_valor DECIMAL DEFAULT NULL,
    p_perfil VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    pode_executar BOOLEAN,
    evidencias_faltando TEXT[],
    mensagem TEXT
) AS $$
DECLARE
    v_regra RECORD;
    v_evidencias_existentes TEXT[];
    v_faltando TEXT[];
    v_pode BOOLEAN := true;
    v_mensagem TEXT := 'OK';
BEGIN
    -- Busca regras para esta entidade/ação
    FOR v_regra IN 
        SELECT * FROM evidencias_obrigatorias 
        WHERE entidade = p_entidade 
          AND acao = p_acao 
          AND ativo = true
    LOOP
        -- Verifica exceções
        IF p_perfil IS NOT NULL AND v_regra.excecao_perfis IS NOT NULL THEN
            IF p_perfil = ANY(v_regra.excecao_perfis) THEN
                CONTINUE; -- Pula esta regra
            END IF;
        END IF;
        
        IF p_valor IS NOT NULL AND v_regra.excecao_valor_ate IS NOT NULL THEN
            IF p_valor <= v_regra.excecao_valor_ate THEN
                CONTINUE; -- Pula esta regra
            END IF;
        END IF;
        
        -- Busca evidências existentes para esta entidade
        SELECT ARRAY_AGG(DISTINCT tipo) INTO v_evidencias_existentes
        FROM evidencias
        WHERE entidade = p_entidade
          AND entidade_id = p_entidade_id
          AND status = 'ativo'
          AND tipo = ANY(v_regra.tipos_evidencia);
        
        -- Verifica lógica
        IF v_regra.logica = 'AND' THEN
            -- Precisa de TODAS
            SELECT ARRAY_AGG(t) INTO v_faltando
            FROM UNNEST(v_regra.tipos_evidencia) AS t
            WHERE t != ALL(COALESCE(v_evidencias_existentes, ARRAY[]::TEXT[]));
            
            IF ARRAY_LENGTH(v_faltando, 1) > 0 THEN
                v_pode := false;
                v_mensagem := v_regra.mensagem_erro;
            END IF;
        ELSE
            -- Precisa de PELO MENOS UMA
            IF v_evidencias_existentes IS NULL OR ARRAY_LENGTH(v_evidencias_existentes, 1) = 0 THEN
                v_pode := false;
                v_faltando := v_regra.tipos_evidencia;
                v_mensagem := v_regra.mensagem_erro;
            END IF;
        END IF;
    END LOOP;
    
    RETURN QUERY SELECT v_pode, v_faltando, v_mensagem;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 4. FUNCTION: REGISTRAR EVIDÊNCIA
-- ============================================================================
-- Function para registrar evidência com validações

CREATE OR REPLACE FUNCTION registrar_evidencia(
    p_clinica_id UUID,
    p_entidade VARCHAR,
    p_entidade_id UUID,
    p_tipo VARCHAR,
    p_categoria VARCHAR,
    p_descricao VARCHAR DEFAULT NULL,
    p_arquivo_nome VARCHAR DEFAULT NULL,
    p_arquivo_path TEXT DEFAULT NULL,
    p_arquivo_mime_type VARCHAR DEFAULT NULL,
    p_arquivo_tamanho INTEGER DEFAULT NULL,
    p_arquivo_hash VARCHAR DEFAULT NULL,
    p_dados JSONB DEFAULT NULL,
    p_origem VARCHAR DEFAULT 'sistema',
    p_user_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_evidencia_id UUID;
    v_retencao_anos INTEGER;
BEGIN
    -- Define retenção baseado na entidade
    v_retencao_anos := CASE p_entidade
        WHEN 'consultas' THEN 20
        WHEN 'receitas' THEN 20
        WHEN 'atestados' THEN 20
        WHEN 'prontuarios_soap' THEN 20
        WHEN 'contas_pagar' THEN 10
        WHEN 'contas_receber' THEN 10
        WHEN 'consentimentos' THEN 10
        ELSE 6
    END;
    
    INSERT INTO evidencias (
        clinica_id,
        entidade,
        entidade_id,
        tipo,
        categoria,
        descricao,
        arquivo_nome,
        arquivo_path,
        arquivo_mime_type,
        arquivo_tamanho_bytes,
        arquivo_hash,
        dados,
        origem,
        created_by_user,
        created_by_sistema,
        retencao_ate
    ) VALUES (
        p_clinica_id,
        p_entidade,
        p_entidade_id,
        p_tipo,
        p_categoria,
        p_descricao,
        p_arquivo_nome,
        p_arquivo_path,
        p_arquivo_mime_type,
        p_arquivo_tamanho,
        p_arquivo_hash,
        p_dados,
        p_origem,
        p_user_id,
        p_origem = 'sistema',
        CURRENT_DATE + (v_retencao_anos || ' years')::INTERVAL
    ) RETURNING id INTO v_evidencia_id;
    
    RETURN v_evidencia_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 5. FUNCTION: BUSCAR EVIDÊNCIAS DE ENTIDADE
-- ============================================================================

CREATE OR REPLACE FUNCTION get_evidencias(
    p_entidade VARCHAR,
    p_entidade_id UUID
)
RETURNS TABLE (
    evidencia_id UUID,
    tipo VARCHAR,
    categoria VARCHAR,
    descricao VARCHAR,
    arquivo_nome VARCHAR,
    arquivo_path TEXT,
    dados JSONB,
    origem VARCHAR,
    validado BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS evidencia_id,
        e.tipo,
        e.categoria,
        e.descricao,
        e.arquivo_nome,
        e.arquivo_path,
        e.dados,
        e.origem,
        e.validado,
        e.created_at
    FROM evidencias e
    WHERE e.entidade = p_entidade
      AND e.entidade_id = p_entidade_id
      AND e.status = 'ativo'
    ORDER BY e.created_at DESC;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 6. TRIGGERS: REGISTRAR EVIDÊNCIAS AUTOMÁTICAS
-- ============================================================================

-- Trigger para registrar evidência quando receita é emitida
CREATE OR REPLACE FUNCTION on_receita_emitida()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'emitida' AND OLD.status != 'emitida' AND NEW.pdf_storage_path IS NOT NULL THEN
        PERFORM registrar_evidencia(
            (SELECT clinica_id FROM consultas WHERE id = NEW.consulta_id),
            'receitas',
            NEW.id,
            'pdf_assinado',
            'documento',
            'PDF da receita emitida',
            'receita_' || NEW.id || '.pdf',
            NEW.pdf_storage_path,
            'application/pdf',
            NULL,
            NULL,
            NULL,
            'sistema',
            NEW.medico_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_receita_evidencia
    AFTER UPDATE ON receitas
    FOR EACH ROW
    EXECUTE FUNCTION on_receita_emitida();


-- Trigger para registrar evidência quando atestado é emitido
CREATE OR REPLACE FUNCTION on_atestado_emitido()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'emitido' AND OLD.status != 'emitido' AND NEW.pdf_storage_path IS NOT NULL THEN
        PERFORM registrar_evidencia(
            (SELECT clinica_id FROM consultas WHERE id = NEW.consulta_id),
            'atestados',
            NEW.id,
            'pdf_assinado',
            'documento',
            'PDF do atestado emitido',
            'atestado_' || NEW.id || '.pdf',
            NEW.pdf_storage_path,
            'application/pdf',
            NULL,
            NULL,
            NULL,
            'sistema',
            NEW.medico_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atestado_evidencia
    AFTER UPDATE ON atestados
    FOR EACH ROW
    EXECUTE FUNCTION on_atestado_emitido();


-- Trigger para registrar evidência de aprovação de conta a pagar
CREATE OR REPLACE FUNCTION on_conta_pagar_aprovada()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'aprovado' AND OLD.status != 'aprovado' THEN
        PERFORM registrar_evidencia(
            NEW.clinica_id,
            'contas_pagar',
            NEW.id,
            'aprovacao',
            'log_sistema',
            'Aprovação de pagamento',
            NULL,
            NULL,
            NULL,
            NULL,
            NULL,
            jsonb_build_object(
                'aprovado_por', NEW.aprovado_por,
                'aprovado_em', NEW.aprovado_em,
                'valor', NEW.valor
            ),
            'sistema',
            NEW.aprovado_por
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_conta_pagar_aprovacao_evidencia
    AFTER UPDATE ON contas_pagar
    FOR EACH ROW
    EXECUTE FUNCTION on_conta_pagar_aprovada();


-- Trigger para registrar evidência de pagamento de conta a pagar
CREATE OR REPLACE FUNCTION on_conta_pagar_paga()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'pago' AND OLD.status != 'pago' AND NEW.comprovante_storage_path IS NOT NULL THEN
        PERFORM registrar_evidencia(
            NEW.clinica_id,
            'contas_pagar',
            NEW.id,
            'comprovante_pagamento',
            'comprovante',
            'Comprovante de pagamento',
            'comprovante_' || NEW.id || '.pdf',
            NEW.comprovante_storage_path,
            'application/pdf',
            NULL,
            NULL,
            NULL,
            'usuario',
            NULL
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_conta_pagar_pagamento_evidencia
    AFTER UPDATE ON contas_pagar
    FOR EACH ROW
    EXECUTE FUNCTION on_conta_pagar_paga();


-- ============================================================================
-- 7. STORAGE BUCKETS (documentação)
-- ============================================================================
-- Buckets a serem criados no Supabase Storage:
--
-- evidencias/
--   ├── documentos/          -- NFs, boletos, recibos
--   ├── comprovantes/        -- Comprovantes de pagamento
--   ├── receitas/            -- PDFs de receitas
--   ├── atestados/           -- PDFs de atestados
--   ├── guias/               -- Guias SADT, TISS
--   ├── exames/              -- Resultados de exames
--   ├── assinaturas/         -- Assinaturas digitais
--   └── api_responses/       -- XMLs/JSONs de APIs externas
--
-- Políticas de acesso:
-- - Todos os arquivos criptografados (AES-256)
-- - Acesso via RLS (mesmo padrão das tabelas)
-- - Sem acesso público
-- - Retenção conforme tabela evidencias.retencao_ate


-- ============================================================================
-- 8. VIEW: RESUMO DE EVIDÊNCIAS POR ENTIDADE
-- ============================================================================

CREATE OR REPLACE VIEW vw_evidencias_resumo AS
SELECT 
    e.clinica_id,
    e.entidade,
    e.entidade_id,
    COUNT(*) AS total_evidencias,
    COUNT(*) FILTER (WHERE e.categoria = 'documento') AS documentos,
    COUNT(*) FILTER (WHERE e.categoria = 'comprovante') AS comprovantes,
    COUNT(*) FILTER (WHERE e.categoria = 'api_response') AS api_responses,
    COUNT(*) FILTER (WHERE e.validado = true) AS validadas,
    ARRAY_AGG(DISTINCT e.tipo) AS tipos_presentes,
    MIN(e.created_at) AS primeira_evidencia,
    MAX(e.created_at) AS ultima_evidencia
FROM evidencias e
WHERE e.status = 'ativo'
GROUP BY e.clinica_id, e.entidade, e.entidade_id;


-- ============================================================================
-- 9. FUNCTION: VERIFICAR INTEGRIDADE DE ARQUIVO
-- ============================================================================
-- Compara hash armazenado com hash calculado (chamada do backend)

CREATE OR REPLACE FUNCTION verificar_integridade_evidencia(p_evidencia_id UUID)
RETURNS TABLE (
    integro BOOLEAN,
    hash_armazenado VARCHAR,
    arquivo_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.arquivo_hash IS NOT NULL AS integro,  -- Backend calcula e compara
        e.arquivo_hash AS hash_armazenado,
        e.arquivo_path
    FROM evidencias e
    WHERE e.id = p_evidencia_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 10. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE evidencias ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidencias_obrigatorias ENABLE ROW LEVEL SECURITY;

-- Evidências: usuário vê da sua clínica
CREATE POLICY "evidencias_clinica" ON evidencias
    FOR ALL USING (clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()));

-- Regras obrigatórias: todos podem ler (são globais)
CREATE POLICY "evidencias_obrig_leitura" ON evidencias_obrigatorias
    FOR SELECT USING (true);

-- Apenas admin pode alterar regras
CREATE POLICY "evidencias_obrig_admin" ON evidencias_obrigatorias
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
    );


-- ============================================================================
-- 11. COMENTÁRIO: FLUXO DE USO
-- ============================================================================
/*
FLUXO DE USO DAS EVIDÊNCIAS:

1. UPLOAD DE EVIDÊNCIA (usuário ou sistema):
   - Backend recebe arquivo
   - Calcula hash SHA-256
   - Salva no Storage (bucket apropriado)
   - Chama registrar_evidencia() com metadados

2. VALIDAÇÃO ANTES DE AÇÃO:
   - Antes de executar ação (ex: pagar conta)
   - Backend chama verificar_evidencias(entidade, id, acao)
   - Se pode_executar = false, retorna erro com mensagem
   - Se pode_executar = true, permite ação

3. AUDITORIA:
   - Quando ação é executada, audit_log é criado
   - Evidências vinculadas via entidade + entidade_id
   - Auditores podem listar todas evidências de uma ação

4. VERIFICAÇÃO DE INTEGRIDADE:
   - Periodicamente, backend verifica hash dos arquivos
   - Se hash não bate, marca evidência como 'invalido'
   - Gera alerta de segurança

5. RETENÇÃO:
   - Cron job verifica evidencias.retencao_ate
   - Arquivos expirados são arquivados/deletados
   - Metadados mantidos (registro de que existiu)
*/


-- ============================================================================
-- FIM DA FASE 7
-- ============================================================================
