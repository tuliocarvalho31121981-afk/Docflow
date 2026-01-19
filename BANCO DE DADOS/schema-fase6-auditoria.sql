-- ============================================================================
-- FASE 6: AUDITORIA E LOGS
-- ============================================================================
-- Conformidade LGPD, CFM, ANS. Registro imutável de todas as ações.
-- Depende de: clinicas, users, pacientes (Fase 1)
-- ============================================================================


-- ============================================================================
-- 1. AUDIT_LOGS
-- ============================================================================
-- Registro de TODAS as ações no sistema. Imutável (sem UPDATE/DELETE).
-- Retenção: 20 anos para prontuário (CFM), 10 anos para financeiro (ANS)

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL,                   -- Não usa FK para performance
    
    -- Quem fez
    user_id UUID,                               -- Se foi usuário logado
    user_nome VARCHAR(255),                     -- Snapshot do nome (caso usuário seja excluído)
    user_perfil VARCHAR(100),                   -- Snapshot do perfil
    paciente_id UUID,                           -- Se foi ação do paciente
    ip_address INET,
    user_agent TEXT,
    
    -- O que fez
    acao VARCHAR(50) NOT NULL,                  -- 'create', 'read', 'update', 'delete', 'login', 'export', etc
    modulo VARCHAR(50) NOT NULL,                -- 'prontuario', 'agenda', 'financeiro', etc
    
    -- Onde (entidade afetada)
    entidade VARCHAR(50) NOT NULL,              -- Nome da tabela
    entidade_id UUID,                           -- ID do registro
    
    -- Detalhes da mudança
    dados_anteriores JSONB,                     -- Estado antes (para update/delete)
    dados_novos JSONB,                          -- Estado depois (para create/update)
    campos_alterados TEXT[],                    -- Lista de campos que mudaram
    
    -- Contexto
    descricao TEXT,                             -- Descrição legível da ação
    motivo TEXT,                                -- Se exigiu justificativa
    
    -- Classificação
    sensibilidade VARCHAR(20) DEFAULT 'normal' CHECK (sensibilidade IN (
        'baixa',        -- Ações comuns (listar, visualizar)
        'normal',       -- Alterações padrão
        'alta',         -- Dados sensíveis (prontuário)
        'critica'       -- Ações críticas (exclusão, export em massa)
    )),
    
    -- Quando
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Retenção
    retencao_ate DATE                           -- Até quando manter (calculado por trigger)
);

-- Indexes para busca
CREATE INDEX idx_audit_clinica ON audit_logs(clinica_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_paciente ON audit_logs(paciente_id);
CREATE INDEX idx_audit_entidade ON audit_logs(entidade, entidade_id);
CREATE INDEX idx_audit_acao ON audit_logs(acao);
CREATE INDEX idx_audit_modulo ON audit_logs(modulo);
CREATE INDEX idx_audit_data ON audit_logs(created_at);
CREATE INDEX idx_audit_sensibilidade ON audit_logs(sensibilidade);

-- Index para busca por período
CREATE INDEX idx_audit_clinica_data ON audit_logs(clinica_id, created_at DESC);

-- Impede alteração/exclusão de logs
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Logs de auditoria são imutáveis e não podem ser alterados ou excluídos';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_no_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER trigger_audit_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();


-- ============================================================================
-- 2. AUDIT_LOGS_ALERTAS
-- ============================================================================
-- Alertas gerados por ações suspeitas (notifica admin)

CREATE TABLE audit_logs_alertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    audit_log_id UUID NOT NULL REFERENCES audit_logs(id),
    
    -- Tipo de alerta
    tipo VARCHAR(50) NOT NULL,                  -- 'acesso_negado', 'tentativas_login', 'export_massa', etc
    severidade VARCHAR(20) DEFAULT 'media' CHECK (severidade IN ('baixa', 'media', 'alta', 'critica')),
    
    -- Descrição
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'visto', 'resolvido', 'ignorado')),
    
    -- Resolução
    resolvido_por UUID REFERENCES users(id),
    resolvido_em TIMESTAMP WITH TIME ZONE,
    resolucao_comentario TEXT,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_alertas_clinica ON audit_logs_alertas(clinica_id);
CREATE INDEX idx_alertas_status ON audit_logs_alertas(status);


-- ============================================================================
-- 3. CONSENTIMENTOS
-- ============================================================================
-- Registro de consentimentos do paciente (LGPD Art. 8)

CREATE TABLE consentimentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    -- Tipo de consentimento
    tipo VARCHAR(50) NOT NULL,                  -- Ver comentário abaixo
    
    -- Status
    aceito BOOLEAN NOT NULL,
    
    -- Detalhes
    versao_termo VARCHAR(20),                   -- Versão do termo aceito
    texto_termo TEXT,                           -- Snapshot do termo
    
    -- Como foi dado
    meio VARCHAR(30) NOT NULL,                  -- 'whatsapp', 'presencial', 'app', 'email'
    
    -- Evidência
    evidencia_tipo VARCHAR(30),                 -- 'mensagem', 'assinatura', 'checkbox'
    evidencia_storage_path TEXT,                -- Caminho para evidência (se houver)
    
    -- IP (se online)
    ip_address INET,
    
    -- Validade
    valido_ate DATE,                            -- Se tiver prazo
    revogado BOOLEAN DEFAULT false,
    revogado_em TIMESTAMP WITH TIME ZONE,
    revogado_motivo TEXT,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_consentimentos_paciente ON consentimentos(paciente_id);
CREATE INDEX idx_consentimentos_tipo ON consentimentos(tipo);
CREATE INDEX idx_consentimentos_ativo ON consentimentos(paciente_id, tipo, revogado) WHERE NOT revogado;

-- Comentário sobre tipos
COMMENT ON COLUMN consentimentos.tipo IS '
Tipos de consentimento (LGPD):

OBRIGATÓRIOS:
- tratamento_dados: Tratamento de dados pessoais para cadastro e prontuário
- comunicacao_whatsapp: Comunicação via WhatsApp (lembretes, confirmações)
- compartilhar_convenio: Compartilhar dados com convênio (TISS)

OPCIONAIS:
- marketing: Receber campanhas e promoções
- pesquisa: Uso de dados anonimizados para pesquisa
- compartilhar_terceiros: Compartilhar com parceiros

ESPECÍFICOS:
- procedimento_[nome]: Consentimento para procedimento específico
- tratamento_[especialidade]: Consentimento para tratamento específico
';


-- ============================================================================
-- 4. NOTIFICACOES
-- ============================================================================
-- Notificações para usuários do sistema (alertas, lembretes, etc)

CREATE TABLE notificacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Destinatário
    user_id UUID REFERENCES users(id),          -- Se para usuário específico
    perfil_destino VARCHAR(100),                -- Se para todos de um perfil
    
    -- Conteúdo
    titulo VARCHAR(255) NOT NULL,
    mensagem TEXT NOT NULL,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN (
        'info',         -- Informação geral
        'alerta',       -- Atenção necessária
        'erro',         -- Algo deu errado
        'sucesso',      -- Ação completada
        'tarefa'        -- Ação requerida
    )),
    
    -- Prioridade
    prioridade VARCHAR(20) DEFAULT 'normal' CHECK (prioridade IN ('baixa', 'normal', 'alta', 'urgente')),
    
    -- Link (para onde direciona ao clicar)
    link_tipo VARCHAR(50),                      -- 'agendamento', 'conta_pagar', 'paciente', etc
    link_id UUID,
    
    -- Status
    lida BOOLEAN DEFAULT false,
    lida_em TIMESTAMP WITH TIME ZONE,
    
    -- Expiração
    expira_em TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notificacoes_user ON notificacoes(user_id);
CREATE INDEX idx_notificacoes_nao_lidas ON notificacoes(user_id, lida) WHERE NOT lida;
CREATE INDEX idx_notificacoes_clinica ON notificacoes(clinica_id);


-- ============================================================================
-- 5. SESSOES
-- ============================================================================
-- Registro de sessões de usuário (complementa Supabase Auth)

CREATE TABLE sessoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    clinica_id UUID NOT NULL REFERENCES clinicas(id),
    
    -- Sessão
    token_hash VARCHAR(255),                    -- Hash do token (não guarda token real)
    
    -- Dispositivo
    ip_address INET,
    user_agent TEXT,
    dispositivo VARCHAR(100),                   -- 'Chrome/Windows', 'Safari/iOS', etc
    
    -- Localização (aproximada)
    cidade VARCHAR(100),
    pais VARCHAR(100),
    
    -- Status
    ativa BOOLEAN DEFAULT true,
    
    -- Timestamps
    iniciada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultimo_acesso TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    encerrada_em TIMESTAMP WITH TIME ZONE,
    
    -- Motivo do encerramento
    encerrada_por VARCHAR(30)                   -- 'logout', 'expiracao', 'admin', 'seguranca'
);

-- Indexes
CREATE INDEX idx_sessoes_user ON sessoes(user_id);
CREATE INDEX idx_sessoes_ativas ON sessoes(user_id, ativa) WHERE ativa = true;


-- ============================================================================
-- 6. TENTATIVAS_LOGIN
-- ============================================================================
-- Registro de tentativas de login (segurança)

CREATE TABLE tentativas_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação
    email VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id),          -- Se usuário existe
    
    -- Resultado
    sucesso BOOLEAN NOT NULL,
    motivo_falha VARCHAR(50),                   -- 'senha_incorreta', 'usuario_inexistente', 'bloqueado', '2fa_falhou'
    
    -- Dispositivo
    ip_address INET,
    user_agent TEXT,
    
    -- Quando
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tentativas_email ON tentativas_login(email);
CREATE INDEX idx_tentativas_ip ON tentativas_login(ip_address);
CREATE INDEX idx_tentativas_data ON tentativas_login(created_at);

-- Index para contar tentativas recentes (bloqueio)
CREATE INDEX idx_tentativas_recentes ON tentativas_login(email, created_at DESC);


-- ============================================================================
-- 7. FUNCTION: REGISTRAR LOG DE AUDITORIA
-- ============================================================================
-- Function genérica para registrar logs (chamada por outras triggers)

CREATE OR REPLACE FUNCTION registrar_audit_log(
    p_clinica_id UUID,
    p_user_id UUID,
    p_acao VARCHAR(50),
    p_modulo VARCHAR(50),
    p_entidade VARCHAR(50),
    p_entidade_id UUID,
    p_dados_anteriores JSONB DEFAULT NULL,
    p_dados_novos JSONB DEFAULT NULL,
    p_descricao TEXT DEFAULT NULL,
    p_sensibilidade VARCHAR(20) DEFAULT 'normal'
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
    v_user_nome VARCHAR(255);
    v_user_perfil VARCHAR(100);
    v_campos_alterados TEXT[];
    v_retencao_anos INTEGER;
BEGIN
    -- Busca dados do usuário
    IF p_user_id IS NOT NULL THEN
        SELECT u.nome, p.nome INTO v_user_nome, v_user_perfil
        FROM users u
        JOIN perfis p ON p.id = u.perfil_id
        WHERE u.id = p_user_id;
    END IF;
    
    -- Calcula campos alterados
    IF p_dados_anteriores IS NOT NULL AND p_dados_novos IS NOT NULL THEN
        SELECT ARRAY_AGG(key) INTO v_campos_alterados
        FROM jsonb_each(p_dados_novos) AS novo
        WHERE NOT EXISTS (
            SELECT 1 FROM jsonb_each(p_dados_anteriores) AS antigo
            WHERE antigo.key = novo.key AND antigo.value = novo.value
        );
    END IF;
    
    -- Define retenção baseado no módulo
    v_retencao_anos := CASE p_modulo
        WHEN 'prontuario' THEN 20   -- CFM
        WHEN 'receita' THEN 20
        WHEN 'atestado' THEN 20
        WHEN 'financeiro' THEN 10   -- ANS
        WHEN 'convenio' THEN 10
        ELSE 5                       -- Padrão
    END;
    
    -- Insere o log
    INSERT INTO audit_logs (
        clinica_id,
        user_id,
        user_nome,
        user_perfil,
        acao,
        modulo,
        entidade,
        entidade_id,
        dados_anteriores,
        dados_novos,
        campos_alterados,
        descricao,
        sensibilidade,
        retencao_ate
    ) VALUES (
        p_clinica_id,
        p_user_id,
        v_user_nome,
        v_user_perfil,
        p_acao,
        p_modulo,
        p_entidade,
        p_entidade_id,
        p_dados_anteriores,
        p_dados_novos,
        v_campos_alterados,
        p_descricao,
        p_sensibilidade,
        CURRENT_DATE + (v_retencao_anos || ' years')::INTERVAL
    ) RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 8. FUNCTION: VERIFICAR TENTATIVAS DE LOGIN
-- ============================================================================
-- Retorna se usuário está bloqueado por excesso de tentativas

CREATE OR REPLACE FUNCTION verificar_bloqueio_login(p_email VARCHAR)
RETURNS TABLE (
    bloqueado BOOLEAN,
    tentativas INTEGER,
    tempo_restante_minutos INTEGER
) AS $$
DECLARE
    v_tentativas INTEGER;
    v_ultima_tentativa TIMESTAMP WITH TIME ZONE;
    v_minutos_desde_ultima INTEGER;
BEGIN
    -- Conta tentativas falhas nos últimos 30 minutos
    SELECT COUNT(*), MAX(created_at) 
    INTO v_tentativas, v_ultima_tentativa
    FROM tentativas_login
    WHERE email = p_email
      AND sucesso = false
      AND created_at > NOW() - INTERVAL '30 minutes';
    
    -- Calcula minutos desde última tentativa
    IF v_ultima_tentativa IS NOT NULL THEN
        v_minutos_desde_ultima := EXTRACT(EPOCH FROM (NOW() - v_ultima_tentativa))::INTEGER / 60;
    ELSE
        v_minutos_desde_ultima := 30;
    END IF;
    
    -- Retorna resultado
    RETURN QUERY SELECT 
        v_tentativas >= 5 AS bloqueado,
        v_tentativas AS tentativas,
        GREATEST(0, 30 - v_minutos_desde_ultima) AS tempo_restante_minutos;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 9. FUNCTION: GERAR ALERTA DE SEGURANÇA
-- ============================================================================

CREATE OR REPLACE FUNCTION gerar_alerta_seguranca(
    p_clinica_id UUID,
    p_audit_log_id UUID,
    p_tipo VARCHAR(50),
    p_titulo VARCHAR(255),
    p_descricao TEXT,
    p_severidade VARCHAR(20) DEFAULT 'media'
)
RETURNS UUID AS $$
DECLARE
    v_alerta_id UUID;
BEGIN
    INSERT INTO audit_logs_alertas (
        clinica_id,
        audit_log_id,
        tipo,
        titulo,
        descricao,
        severidade
    ) VALUES (
        p_clinica_id,
        p_audit_log_id,
        p_tipo,
        p_titulo,
        p_descricao,
        p_severidade
    ) RETURNING id INTO v_alerta_id;
    
    -- Cria notificação para admins
    INSERT INTO notificacoes (
        clinica_id,
        perfil_destino,
        titulo,
        mensagem,
        tipo,
        prioridade,
        link_tipo,
        link_id
    ) VALUES (
        p_clinica_id,
        'Administrador',
        '🚨 ' || p_titulo,
        p_descricao,
        'alerta',
        CASE p_severidade WHEN 'critica' THEN 'urgente' WHEN 'alta' THEN 'alta' ELSE 'normal' END,
        'alerta_seguranca',
        v_alerta_id
    );
    
    RETURN v_alerta_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 10. TRIGGER: AUDITORIA AUTOMÁTICA DE PRONTUÁRIO
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_prontuario()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM registrar_audit_log(
            NEW.clinica_id,
            NEW.medico_id,
            'create',
            'prontuario',
            TG_TABLE_NAME,
            NEW.id,
            NULL,
            to_jsonb(NEW),
            'Criação de registro de prontuário',
            'alta'
        );
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM registrar_audit_log(
            NEW.clinica_id,
            NEW.medico_id,
            'update',
            'prontuario',
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW),
            'Alteração de registro de prontuário',
            'alta'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplica em tabelas de prontuário
CREATE TRIGGER trigger_audit_consultas
    AFTER INSERT OR UPDATE ON consultas
    FOR EACH ROW
    EXECUTE FUNCTION audit_prontuario();

CREATE TRIGGER trigger_audit_soap
    AFTER INSERT OR UPDATE ON prontuarios_soap
    FOR EACH ROW
    EXECUTE FUNCTION audit_prontuario();

CREATE TRIGGER trigger_audit_receitas
    AFTER INSERT OR UPDATE ON receitas
    FOR EACH ROW
    EXECUTE FUNCTION audit_prontuario();

CREATE TRIGGER trigger_audit_atestados
    AFTER INSERT OR UPDATE ON atestados
    FOR EACH ROW
    EXECUTE FUNCTION audit_prontuario();


-- ============================================================================
-- 11. TRIGGER: DETECTAR ACESSO SUSPEITO
-- ============================================================================

CREATE OR REPLACE FUNCTION detectar_acesso_suspeito()
RETURNS TRIGGER AS $$
DECLARE
    v_alerta_id UUID;
BEGIN
    -- Acesso fora do horário (22h - 6h)
    IF EXTRACT(HOUR FROM NOW()) >= 22 OR EXTRACT(HOUR FROM NOW()) < 6 THEN
        IF NEW.modulo = 'prontuario' THEN
            PERFORM gerar_alerta_seguranca(
                NEW.clinica_id,
                NEW.id,
                'acesso_fora_horario',
                'Acesso a prontuário fora do horário',
                'Usuário ' || COALESCE(NEW.user_nome, 'desconhecido') || ' acessou prontuário às ' || TO_CHAR(NOW(), 'HH24:MI'),
                'alta'
            );
        END IF;
    END IF;
    
    -- Export em massa (mais de 50 registros)
    IF NEW.acao = 'export' AND (NEW.dados_novos->>'quantidade')::INTEGER > 50 THEN
        PERFORM gerar_alerta_seguranca(
            NEW.clinica_id,
            NEW.id,
            'export_massa',
            'Exportação em massa de dados',
            'Usuário ' || COALESCE(NEW.user_nome, 'desconhecido') || ' exportou ' || (NEW.dados_novos->>'quantidade') || ' registros',
            'critica'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_detectar_acesso_suspeito
    AFTER INSERT ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION detectar_acesso_suspeito();


-- ============================================================================
-- 12. TRIGGER: BLOQUEAR APÓS TENTATIVAS DE LOGIN
-- ============================================================================

CREATE OR REPLACE FUNCTION verificar_tentativas_login()
RETURNS TRIGGER AS $$
DECLARE
    v_tentativas INTEGER;
BEGIN
    IF NOT NEW.sucesso THEN
        -- Conta tentativas falhas recentes
        SELECT COUNT(*) INTO v_tentativas
        FROM tentativas_login
        WHERE email = NEW.email
          AND sucesso = false
          AND created_at > NOW() - INTERVAL '30 minutes';
        
        -- Se atingiu 5 tentativas, gera alerta
        IF v_tentativas >= 5 THEN
            -- Busca clinica do usuário (se existir)
            PERFORM gerar_alerta_seguranca(
                (SELECT clinica_id FROM users WHERE email = NEW.email LIMIT 1),
                NULL,
                'tentativas_login',
                'Múltiplas tentativas de login falhas',
                'Email ' || NEW.email || ' teve ' || v_tentativas || ' tentativas de login falhas',
                'alta'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_verificar_tentativas
    AFTER INSERT ON tentativas_login
    FOR EACH ROW
    EXECUTE FUNCTION verificar_tentativas_login();


-- ============================================================================
-- 13. FUNCTION: RELATÓRIO DE AUDITORIA
-- ============================================================================

CREATE OR REPLACE FUNCTION get_audit_report(
    p_clinica_id UUID,
    p_data_inicio DATE,
    p_data_fim DATE,
    p_modulo VARCHAR DEFAULT NULL,
    p_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    data DATE,
    total_acoes INTEGER,
    creates INTEGER,
    reads INTEGER,
    updates INTEGER,
    deletes INTEGER,
    exports INTEGER,
    usuarios_unicos INTEGER,
    acoes_criticas INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        created_at::DATE AS data,
        COUNT(*)::INTEGER AS total_acoes,
        COUNT(*) FILTER (WHERE acao = 'create')::INTEGER AS creates,
        COUNT(*) FILTER (WHERE acao = 'read')::INTEGER AS reads,
        COUNT(*) FILTER (WHERE acao = 'update')::INTEGER AS updates,
        COUNT(*) FILTER (WHERE acao = 'delete')::INTEGER AS deletes,
        COUNT(*) FILTER (WHERE acao = 'export')::INTEGER AS exports,
        COUNT(DISTINCT user_id)::INTEGER AS usuarios_unicos,
        COUNT(*) FILTER (WHERE sensibilidade = 'critica')::INTEGER AS acoes_criticas
    FROM audit_logs
    WHERE clinica_id = p_clinica_id
      AND created_at::DATE BETWEEN p_data_inicio AND p_data_fim
      AND (p_modulo IS NULL OR modulo = p_modulo)
      AND (p_user_id IS NULL OR user_id = p_user_id)
    GROUP BY created_at::DATE
    ORDER BY created_at::DATE;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 14. FUNCTION: VERIFICAR CONSENTIMENTO
-- ============================================================================

CREATE OR REPLACE FUNCTION verificar_consentimento(
    p_paciente_id UUID,
    p_tipo VARCHAR
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM consentimentos
        WHERE paciente_id = p_paciente_id
          AND tipo = p_tipo
          AND aceito = true
          AND revogado = false
          AND (valido_ate IS NULL OR valido_ate >= CURRENT_DATE)
    );
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 15. ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs_alertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE consentimentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tentativas_login ENABLE ROW LEVEL SECURITY;

-- Audit logs: apenas admin vê
CREATE POLICY "audit_admin" ON audit_logs
    FOR SELECT USING (
        clinica_id IN (
            SELECT u.clinica_id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
    );

-- Alertas: apenas admin
CREATE POLICY "alertas_admin" ON audit_logs_alertas
    FOR ALL USING (
        clinica_id IN (
            SELECT u.clinica_id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
    );

-- Consentimentos: médico e admin
CREATE POLICY "consentimentos_clinica" ON consentimentos
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );

-- Notificações: usuário vê as suas ou do seu perfil
CREATE POLICY "notificacoes_usuario" ON notificacoes
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        AND (
            user_id = auth.uid()
            OR perfil_destino IN (
                SELECT p.nome FROM users u
                JOIN perfis p ON p.id = u.perfil_id
                WHERE u.id = auth.uid()
            )
        )
    );

-- Sessões: usuário vê as suas, admin vê todas
CREATE POLICY "sessoes_usuario" ON sessoes
    FOR SELECT USING (
        user_id = auth.uid()
        OR clinica_id IN (
            SELECT u.clinica_id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
    );

-- Tentativas de login: apenas admin
CREATE POLICY "tentativas_admin" ON tentativas_login
    FOR SELECT USING (
        user_id IN (
            SELECT u.id FROM users u
            JOIN perfis p ON p.id = u.perfil_id
            WHERE u.id = auth.uid() AND p.is_admin = true
        )
        OR email IN (SELECT email FROM users WHERE id = auth.uid())
    );


-- ============================================================================
-- FIM DA FASE 6
-- ============================================================================
