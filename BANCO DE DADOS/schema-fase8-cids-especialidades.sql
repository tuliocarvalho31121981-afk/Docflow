-- ============================================================================
-- FASE 8: CIDs E ESPECIALIDADES
-- ============================================================================
-- Tabela de CID-10 configurável por especialidade médica.
-- Permite múltiplas especialidades e filtro automático na consulta.
-- Depende de: clinicas (Fase 1)
-- ============================================================================


-- ============================================================================
-- 1. ESPECIALIDADES MÉDICAS
-- ============================================================================
-- Cadastro de especialidades disponíveis no sistema

CREATE TABLE especialidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    codigo VARCHAR(20) NOT NULL UNIQUE,         -- 'cardiologia', 'ortopedia', etc
    nome VARCHAR(100) NOT NULL,                 -- 'Cardiologia', 'Ortopedia'
    descricao TEXT,                             -- Descrição da especialidade

    -- Configuração
    ativa BOOLEAN DEFAULT true,                 -- Se está disponível no sistema
    cor VARCHAR(7),                             -- Cor para UI (hex: #FF5733)
    icone VARCHAR(50),                          -- Nome do ícone (lucide: 'heart', 'bone')

    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger updated_at
CREATE TRIGGER trigger_especialidades_updated_at
    BEFORE UPDATE ON especialidades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_especialidades_codigo ON especialidades(codigo);
CREATE INDEX idx_especialidades_ativa ON especialidades(ativa) WHERE ativa = true;


-- ============================================================================
-- 2. TABELA CID-10
-- ============================================================================
-- Classificação Internacional de Doenças

CREATE TABLE cids (
    codigo VARCHAR(10) PRIMARY KEY,             -- Código CID (ex: I10, E11.9)

    -- Descrição
    descricao VARCHAR(500) NOT NULL,            -- Descrição completa
    descricao_abreviada VARCHAR(100),           -- Versão curta para UI

    -- Categorização
    capitulo VARCHAR(5),                        -- Capítulo CID (I, II, III...)
    grupo VARCHAR(10),                          -- Grupo (I00-I99, E00-E90...)
    categoria VARCHAR(10),                      -- Categoria (I10, I11, I12...)

    -- Configuração
    ativo BOOLEAN DEFAULT true,                 -- Se está disponível para uso

    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cids_capitulo ON cids(capitulo);
CREATE INDEX idx_cids_grupo ON cids(grupo);
CREATE INDEX idx_cids_descricao ON cids USING gin(to_tsvector('portuguese', descricao));
CREATE INDEX idx_cids_ativo ON cids(ativo) WHERE ativo = true;


-- ============================================================================
-- 3. RELACIONAMENTO CIDs x ESPECIALIDADES
-- ============================================================================
-- Quais CIDs são relevantes para cada especialidade

CREATE TABLE cids_especialidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    especialidade_id UUID NOT NULL REFERENCES especialidades(id) ON DELETE CASCADE,
    cid_codigo VARCHAR(10) NOT NULL REFERENCES cids(codigo) ON DELETE CASCADE,

    -- Relevância
    frequencia_uso INTEGER DEFAULT 0,           -- Quantas vezes foi usado (para ordenar)
    favorito BOOLEAN DEFAULT false,             -- Se é um CID "favorito" da especialidade

    -- Controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique
    UNIQUE(especialidade_id, cid_codigo)
);

-- Indexes
CREATE INDEX idx_cids_esp_especialidade ON cids_especialidades(especialidade_id);
CREATE INDEX idx_cids_esp_cid ON cids_especialidades(cid_codigo);
CREATE INDEX idx_cids_esp_frequencia ON cids_especialidades(especialidade_id, frequencia_uso DESC);
CREATE INDEX idx_cids_esp_favorito ON cids_especialidades(especialidade_id, favorito) WHERE favorito = true;


-- ============================================================================
-- 4. ADICIONAR ESPECIALIDADE AO MÉDICO
-- ============================================================================
-- Vincula médico a uma ou mais especialidades

ALTER TABLE users
ADD COLUMN IF NOT EXISTS especialidade_principal_id UUID REFERENCES especialidades(id);

-- Tabela para múltiplas especialidades por médico (opcional)
CREATE TABLE IF NOT EXISTS users_especialidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    especialidade_id UUID NOT NULL REFERENCES especialidades(id) ON DELETE CASCADE,
    principal BOOLEAN DEFAULT false,            -- É a especialidade principal?
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, especialidade_id)
);

CREATE INDEX idx_users_esp_user ON users_especialidades(user_id);
CREATE INDEX idx_users_esp_especialidade ON users_especialidades(especialidade_id);


-- ============================================================================
-- 5. ADICIONAR ESPECIALIDADE AO TIPO DE CONSULTA
-- ============================================================================
-- Vincula tipo de consulta a uma especialidade

ALTER TABLE tipos_consulta
ADD COLUMN IF NOT EXISTS especialidade_id UUID REFERENCES especialidades(id);


-- ============================================================================
-- 6. FUNCTION: BUSCAR CIDs POR ESPECIALIDADE
-- ============================================================================
-- Retorna CIDs filtrados por especialidade, ordenados por frequência

CREATE OR REPLACE FUNCTION get_cids_por_especialidade(
    p_especialidade_id UUID,
    p_search TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    codigo VARCHAR(10),
    descricao VARCHAR(500),
    descricao_abreviada VARCHAR(100),
    frequencia_uso INTEGER,
    favorito BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.codigo,
        c.descricao,
        c.descricao_abreviada,
        COALESCE(ce.frequencia_uso, 0) AS frequencia_uso,
        COALESCE(ce.favorito, false) AS favorito
    FROM cids c
    LEFT JOIN cids_especialidades ce ON ce.cid_codigo = c.codigo AND ce.especialidade_id = p_especialidade_id
    WHERE c.ativo = true
      AND (
          p_search IS NULL
          OR c.codigo ILIKE '%' || p_search || '%'
          OR c.descricao ILIKE '%' || p_search || '%'
      )
      AND (
          -- Se especialidade informada, filtra apenas CIDs vinculados
          p_especialidade_id IS NULL
          OR ce.especialidade_id IS NOT NULL
      )
    ORDER BY
        ce.favorito DESC NULLS LAST,
        ce.frequencia_uso DESC NULLS LAST,
        c.codigo ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. FUNCTION: INCREMENTAR FREQUÊNCIA DE USO DO CID
-- ============================================================================
-- Chamada quando médico usa um CID, aumenta a relevância

CREATE OR REPLACE FUNCTION incrementar_uso_cid(
    p_especialidade_id UUID,
    p_cid_codigo VARCHAR(10)
)
RETURNS VOID AS $$
BEGIN
    -- Tenta atualizar
    UPDATE cids_especialidades
    SET frequencia_uso = frequencia_uso + 1
    WHERE especialidade_id = p_especialidade_id AND cid_codigo = p_cid_codigo;

    -- Se não existia, insere
    IF NOT FOUND THEN
        INSERT INTO cids_especialidades (especialidade_id, cid_codigo, frequencia_uso)
        VALUES (p_especialidade_id, p_cid_codigo, 1)
        ON CONFLICT (especialidade_id, cid_codigo) DO UPDATE
        SET frequencia_uso = cids_especialidades.frequencia_uso + 1;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 8. DADOS INICIAIS: ESPECIALIDADES
-- ============================================================================

INSERT INTO especialidades (codigo, nome, descricao, cor, icone) VALUES
('cardiologia', 'Cardiologia', 'Especialidade médica que trata do coração e sistema cardiovascular', '#EF4444', 'heart'),
('ortopedia', 'Ortopedia', 'Especialidade médica que trata do sistema musculoesquelético', '#3B82F6', 'bone'),
('dermatologia', 'Dermatologia', 'Especialidade médica que trata da pele, cabelos e unhas', '#EC4899', 'scan'),
('gastroenterologia', 'Gastroenterologia', 'Especialidade médica que trata do sistema digestivo', '#F59E0B', 'utensils'),
('neurologia', 'Neurologia', 'Especialidade médica que trata do sistema nervoso', '#8B5CF6', 'brain'),
('pneumologia', 'Pneumologia', 'Especialidade médica que trata do sistema respiratório', '#06B6D4', 'wind'),
('endocrinologia', 'Endocrinologia', 'Especialidade médica que trata do sistema endócrino', '#10B981', 'pill'),
('clinica_geral', 'Clínica Geral', 'Medicina geral e familiar', '#6B7280', 'stethoscope'),
('pediatria', 'Pediatria', 'Especialidade médica que trata de crianças e adolescentes', '#F472B6', 'baby'),
('ginecologia', 'Ginecologia', 'Especialidade médica que trata da saúde da mulher', '#A855F7', 'heart-pulse')
ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- 9. DADOS INICIAIS: CIDs DE CARDIOLOGIA
-- ============================================================================

-- Inserir CIDs (apenas cardiologia para começar)
INSERT INTO cids (codigo, descricao, descricao_abreviada, capitulo, grupo, categoria) VALUES
-- Hipertensão
('I10', 'Hipertensão essencial (primária)', 'HAS essencial', 'IX', 'I10-I15', 'I10'),
('I11', 'Doença cardíaca hipertensiva', 'Cardiopatia hipertensiva', 'IX', 'I10-I15', 'I11'),
('I11.0', 'Doença cardíaca hipertensiva com insuficiência cardíaca', 'Cardiopatia hipertensiva c/ IC', 'IX', 'I10-I15', 'I11'),
('I11.9', 'Doença cardíaca hipertensiva sem insuficiência cardíaca', 'Cardiopatia hipertensiva s/ IC', 'IX', 'I10-I15', 'I11'),
('I13', 'Doença cardíaca e renal hipertensiva', 'Cardiopatia e nefropatia hipertensiva', 'IX', 'I10-I15', 'I13'),
('I15', 'Hipertensão secundária', 'HAS secundária', 'IX', 'I10-I15', 'I15'),

-- Doença Isquêmica do Coração
('I20', 'Angina pectoris', 'Angina', 'IX', 'I20-I25', 'I20'),
('I20.0', 'Angina instável', 'Angina instável', 'IX', 'I20-I25', 'I20'),
('I20.1', 'Angina pectoris com espasmo documentado', 'Angina vasoespástica', 'IX', 'I20-I25', 'I20'),
('I20.8', 'Outras formas de angina pectoris', 'Angina outras formas', 'IX', 'I20-I25', 'I20'),
('I20.9', 'Angina pectoris não especificada', 'Angina NE', 'IX', 'I20-I25', 'I20'),
('I21', 'Infarto agudo do miocárdio', 'IAM', 'IX', 'I20-I25', 'I21'),
('I21.0', 'Infarto agudo transmural da parede anterior do miocárdio', 'IAM anterior', 'IX', 'I20-I25', 'I21'),
('I21.1', 'Infarto agudo transmural da parede inferior do miocárdio', 'IAM inferior', 'IX', 'I20-I25', 'I21'),
('I21.4', 'Infarto agudo subendocárdico do miocárdio', 'IAM subendocárdico', 'IX', 'I20-I25', 'I21'),
('I21.9', 'Infarto agudo do miocárdio não especificado', 'IAM NE', 'IX', 'I20-I25', 'I21'),
('I25', 'Doença isquêmica crônica do coração', 'Cardiopatia isquêmica crônica', 'IX', 'I20-I25', 'I25'),
('I25.1', 'Doença aterosclerótica do coração', 'DAC', 'IX', 'I20-I25', 'I25'),
('I25.2', 'Infarto antigo do miocárdio', 'IAM antigo', 'IX', 'I20-I25', 'I25'),
('I25.5', 'Cardiomiopatia isquêmica', 'Cardiomiopatia isquêmica', 'IX', 'I20-I25', 'I25'),
('I25.9', 'Doença isquêmica crônica do coração não especificada', 'Cardiopatia isquêmica NE', 'IX', 'I20-I25', 'I25'),

-- Doenças da Circulação Pulmonar
('I26', 'Embolia pulmonar', 'TEP', 'IX', 'I26-I28', 'I26'),
('I26.0', 'Embolia pulmonar com menção de cor pulmonale agudo', 'TEP c/ cor pulmonale', 'IX', 'I26-I28', 'I26'),
('I26.9', 'Embolia pulmonar sem menção de cor pulmonale agudo', 'TEP s/ cor pulmonale', 'IX', 'I26-I28', 'I26'),
('I27', 'Outras formas de doença cardíaca pulmonar', 'Hipertensão pulmonar', 'IX', 'I26-I28', 'I27'),
('I27.0', 'Hipertensão pulmonar primária', 'HAP primária', 'IX', 'I26-I28', 'I27'),
('I27.2', 'Outra hipertensão pulmonar secundária', 'HAP secundária', 'IX', 'I26-I28', 'I27'),

-- Outras Formas de Doença do Coração
('I30', 'Pericardite aguda', 'Pericardite aguda', 'IX', 'I30-I52', 'I30'),
('I31', 'Outras doenças do pericárdio', 'Doença pericárdica', 'IX', 'I30-I52', 'I31'),
('I31.3', 'Derrame pericárdico (não-inflamatório)', 'Derrame pericárdico', 'IX', 'I30-I52', 'I31'),
('I33', 'Endocardite aguda e subaguda', 'Endocardite', 'IX', 'I30-I52', 'I33'),
('I34', 'Transtornos não-reumáticos da valva mitral', 'Valvopatia mitral', 'IX', 'I30-I52', 'I34'),
('I34.0', 'Insuficiência (da valva) mitral', 'IM', 'IX', 'I30-I52', 'I34'),
('I34.1', 'Prolapso (da valva) mitral', 'PVM', 'IX', 'I30-I52', 'I34'),
('I35', 'Transtornos não-reumáticos da valva aórtica', 'Valvopatia aórtica', 'IX', 'I30-I52', 'I35'),
('I35.0', 'Estenose (da valva) aórtica', 'EAo', 'IX', 'I30-I52', 'I35'),
('I35.1', 'Insuficiência (da valva) aórtica', 'IAo', 'IX', 'I30-I52', 'I35'),
('I35.2', 'Estenose (da valva) aórtica com insuficiência', 'Dupla lesão aórtica', 'IX', 'I30-I52', 'I35'),
('I38', 'Endocardite de valva não especificada', 'Endocardite NE', 'IX', 'I30-I52', 'I38'),

-- Cardiomiopatias
('I42', 'Cardiomiopatia', 'Cardiomiopatia', 'IX', 'I30-I52', 'I42'),
('I42.0', 'Cardiomiopatia dilatada', 'CMD', 'IX', 'I30-I52', 'I42'),
('I42.1', 'Cardiomiopatia obstrutiva hipertrófica', 'CMH obstrutiva', 'IX', 'I30-I52', 'I42'),
('I42.2', 'Outra cardiomiopatia hipertrófica', 'CMH', 'IX', 'I30-I52', 'I42'),
('I42.5', 'Outra cardiomiopatia restritiva', 'CMR', 'IX', 'I30-I52', 'I42'),
('I42.9', 'Cardiomiopatia não especificada', 'Cardiomiopatia NE', 'IX', 'I30-I52', 'I42'),

-- Arritmias
('I44', 'Bloqueio atrioventricular e do ramo esquerdo', 'Bloqueio AV/BRE', 'IX', 'I30-I52', 'I44'),
('I44.0', 'Bloqueio atrioventricular de primeiro grau', 'BAV 1º grau', 'IX', 'I30-I52', 'I44'),
('I44.1', 'Bloqueio atrioventricular de segundo grau', 'BAV 2º grau', 'IX', 'I30-I52', 'I44'),
('I44.2', 'Bloqueio atrioventricular total', 'BAVT', 'IX', 'I30-I52', 'I44'),
('I44.7', 'Bloqueio de ramo esquerdo não especificado', 'BRE', 'IX', 'I30-I52', 'I44'),
('I45', 'Outros transtornos de condução', 'Distúrbio de condução', 'IX', 'I30-I52', 'I45'),
('I45.0', 'Bloqueio fascicular anterior direito', 'BDAS', 'IX', 'I30-I52', 'I45'),
('I45.1', 'Outro bloqueio de ramo direito e os não especificados', 'BRD', 'IX', 'I30-I52', 'I45'),
('I45.5', 'Outra forma de bloqueio cardíaco especificado', 'Bloqueio cardíaco', 'IX', 'I30-I52', 'I45'),
('I45.6', 'Síndrome de pré-excitação', 'WPW', 'IX', 'I30-I52', 'I45'),
('I47', 'Taquicardia paroxística', 'Taquicardia paroxística', 'IX', 'I30-I52', 'I47'),
('I47.0', 'Arritmia ventricular por reentrada', 'TV reentrada', 'IX', 'I30-I52', 'I47'),
('I47.1', 'Taquicardia supraventricular', 'TSV', 'IX', 'I30-I52', 'I47'),
('I47.2', 'Taquicardia ventricular', 'TV', 'IX', 'I30-I52', 'I47'),
('I48', 'Flutter e fibrilação atrial', 'FA/Flutter', 'IX', 'I30-I52', 'I48'),
('I48.0', 'Fibrilação atrial paroxística', 'FA paroxística', 'IX', 'I30-I52', 'I48'),
('I48.1', 'Fibrilação atrial persistente', 'FA persistente', 'IX', 'I30-I52', 'I48'),
('I48.2', 'Fibrilação atrial crônica', 'FA crônica', 'IX', 'I30-I52', 'I48'),
('I48.3', 'Flutter atrial típico', 'Flutter típico', 'IX', 'I30-I52', 'I48'),
('I48.4', 'Flutter atrial atípico', 'Flutter atípico', 'IX', 'I30-I52', 'I48'),
('I48.9', 'Fibrilação e flutter atrial não especificados', 'FA/Flutter NE', 'IX', 'I30-I52', 'I48'),
('I49', 'Outras arritmias cardíacas', 'Arritmias outras', 'IX', 'I30-I52', 'I49'),
('I49.0', 'Fibrilação e flutter ventricular', 'FV', 'IX', 'I30-I52', 'I49'),
('I49.1', 'Despolarização atrial prematura', 'ESSV', 'IX', 'I30-I52', 'I49'),
('I49.3', 'Despolarização ventricular prematura', 'ESV', 'IX', 'I30-I52', 'I49'),
('I49.4', 'Outra despolarização prematura e as não especificadas', 'Extrassístoles', 'IX', 'I30-I52', 'I49'),
('I49.5', 'Síndrome do nó sinusal', 'DNS', 'IX', 'I30-I52', 'I49'),
('I49.8', 'Outras arritmias cardíacas especificadas', 'Arritmia especificada', 'IX', 'I30-I52', 'I49'),
('I49.9', 'Arritmia cardíaca não especificada', 'Arritmia NE', 'IX', 'I30-I52', 'I49'),

-- Insuficiência Cardíaca
('I50', 'Insuficiência cardíaca', 'IC', 'IX', 'I30-I52', 'I50'),
('I50.0', 'Insuficiência cardíaca congestiva', 'ICC', 'IX', 'I30-I52', 'I50'),
('I50.1', 'Insuficiência ventricular esquerda', 'IVE', 'IX', 'I30-I52', 'I50'),
('I50.9', 'Insuficiência cardíaca não especificada', 'IC NE', 'IX', 'I30-I52', 'I50'),

-- Outras
('I51.7', 'Cardiomegalia', 'Cardiomegalia', 'IX', 'I30-I52', 'I51'),

-- Doenças Cerebrovasculares (relacionadas)
('I63', 'Infarto cerebral', 'AVC isquêmico', 'IX', 'I60-I69', 'I63'),
('I64', 'Acidente vascular cerebral não especificado', 'AVC NE', 'IX', 'I60-I69', 'I64'),

-- Doenças Vasculares Periféricas
('I70', 'Aterosclerose', 'Aterosclerose', 'IX', 'I70-I79', 'I70'),
('I70.0', 'Aterosclerose da aorta', 'Aterosclerose aorta', 'IX', 'I70-I79', 'I70'),
('I70.2', 'Aterosclerose das artérias das extremidades', 'DAOP', 'IX', 'I70-I79', 'I70'),
('I71', 'Aneurisma e dissecção da aorta', 'Aneurisma/Dissecção aorta', 'IX', 'I70-I79', 'I71'),
('I71.0', 'Dissecção da aorta', 'Dissecção aorta', 'IX', 'I70-I79', 'I71'),
('I71.4', 'Aneurisma da aorta abdominal, sem menção de ruptura', 'AAA', 'IX', 'I70-I79', 'I71'),
('I73', 'Outras doenças vasculares periféricas', 'Doença vascular periférica', 'IX', 'I70-I79', 'I73'),
('I74', 'Embolia e trombose arteriais', 'Tromboembolismo arterial', 'IX', 'I70-I79', 'I74'),

-- Hipotensão
('I95', 'Hipotensão', 'Hipotensão', 'IX', 'I95-I99', 'I95'),
('I95.0', 'Hipotensão idiopática', 'Hipotensão idiopática', 'IX', 'I95-I99', 'I95'),
('I95.1', 'Hipotensão ortostática', 'Hipotensão ortostática', 'IX', 'I95-I99', 'I95'),

-- Dislipidemia (Capítulo IV mas muito usado em cardio)
('E78', 'Distúrbios do metabolismo de lipoproteínas e outras lipidemias', 'Dislipidemia', 'IV', 'E70-E90', 'E78'),
('E78.0', 'Hipercolesterolemia pura', 'Hipercolesterolemia', 'IV', 'E70-E90', 'E78'),
('E78.1', 'Hipertrigliceridemia pura', 'Hipertrigliceridemia', 'IV', 'E70-E90', 'E78'),
('E78.2', 'Hiperlipidemia mista', 'Dislipidemia mista', 'IV', 'E70-E90', 'E78'),
('E78.5', 'Hiperlipidemia não especificada', 'Dislipidemia NE', 'IV', 'E70-E90', 'E78'),

-- Diabetes (muito usado em cardio)
('E10', 'Diabetes mellitus insulino-dependente', 'DM tipo 1', 'IV', 'E10-E14', 'E10'),
('E11', 'Diabetes mellitus não-insulino-dependente', 'DM tipo 2', 'IV', 'E10-E14', 'E11'),
('E11.9', 'Diabetes mellitus não-insulino-dependente sem complicações', 'DM tipo 2 s/ complicações', 'IV', 'E10-E14', 'E11'),

-- Obesidade
('E66', 'Obesidade', 'Obesidade', 'IV', 'E65-E68', 'E66'),
('E66.0', 'Obesidade devida a excesso de calorias', 'Obesidade', 'IV', 'E65-E68', 'E66'),
('E66.9', 'Obesidade não especificada', 'Obesidade NE', 'IV', 'E65-E68', 'E66'),

-- Sintomas Cardiovasculares
('R00', 'Anormalidades do batimento cardíaco', 'Anormalidades cardíacas', 'XVIII', 'R00-R09', 'R00'),
('R00.0', 'Taquicardia não especificada', 'Taquicardia', 'XVIII', 'R00-R09', 'R00'),
('R00.1', 'Bradicardia não especificada', 'Bradicardia', 'XVIII', 'R00-R09', 'R00'),
('R00.2', 'Palpitações', 'Palpitações', 'XVIII', 'R00-R09', 'R00'),
('R01', 'Sopros e outros sons cardíacos', 'Sopro cardíaco', 'XVIII', 'R00-R09', 'R01'),
('R06.0', 'Dispneia', 'Dispneia', 'XVIII', 'R00-R09', 'R06'),
('R07', 'Dor de garganta e no peito', 'Dor torácica', 'XVIII', 'R00-R09', 'R07'),
('R07.2', 'Dor precordial', 'Dor precordial', 'XVIII', 'R00-R09', 'R07'),
('R07.3', 'Outras dores torácicas', 'Dor torácica outras', 'XVIII', 'R00-R09', 'R07'),
('R07.4', 'Dor torácica não especificada', 'Dor torácica NE', 'XVIII', 'R00-R09', 'R07'),
('R42', 'Tontura e instabilidade', 'Tontura', 'XVIII', 'R40-R46', 'R42'),
('R55', 'Síncope e colapso', 'Síncope', 'XVIII', 'R55-R59', 'R55'),
('R60', 'Edema não classificado em outra parte', 'Edema', 'XVIII', 'R60-R69', 'R60'),
('R60.0', 'Edema localizado', 'Edema localizado', 'XVIII', 'R60-R69', 'R60'),
('R60.9', 'Edema não especificado', 'Edema NE', 'XVIII', 'R60-R69', 'R60')

ON CONFLICT (codigo) DO UPDATE SET
    descricao = EXCLUDED.descricao,
    descricao_abreviada = EXCLUDED.descricao_abreviada,
    capitulo = EXCLUDED.capitulo,
    grupo = EXCLUDED.grupo,
    categoria = EXCLUDED.categoria;


-- ============================================================================
-- 10. VINCULAR CIDs À ESPECIALIDADE CARDIOLOGIA
-- ============================================================================

INSERT INTO cids_especialidades (especialidade_id, cid_codigo, favorito)
SELECT
    e.id,
    c.codigo,
    CASE
        -- Marcar como favoritos os mais comuns
        WHEN c.codigo IN ('I10', 'I11.9', 'I20.9', 'I21.9', 'I25.1', 'I48', 'I50.0', 'E78.5', 'R00.2', 'R06.0') THEN true
        ELSE false
    END
FROM especialidades e
CROSS JOIN cids c
WHERE e.codigo = 'cardiologia'
  AND c.codigo LIKE 'I%' OR c.codigo LIKE 'E78%' OR c.codigo LIKE 'E11%' OR c.codigo LIKE 'E66%' OR c.codigo LIKE 'R0%' OR c.codigo IN ('R42', 'R55', 'R60', 'R60.0', 'R60.9')
ON CONFLICT (especialidade_id, cid_codigo) DO NOTHING;


-- ============================================================================
-- 11. ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE especialidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE cids ENABLE ROW LEVEL SECURITY;
ALTER TABLE cids_especialidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE users_especialidades ENABLE ROW LEVEL SECURITY;

-- Especialidades: todos podem ler
CREATE POLICY "especialidades_read" ON especialidades
    FOR SELECT USING (true);

-- CIDs: todos podem ler
CREATE POLICY "cids_read" ON cids
    FOR SELECT USING (true);

-- CIDs x Especialidades: todos podem ler
CREATE POLICY "cids_esp_read" ON cids_especialidades
    FOR SELECT USING (true);

-- Users x Especialidades: mesmo tenant
CREATE POLICY "users_esp_tenant" ON users_especialidades
    FOR ALL USING (
        user_id IN (SELECT id FROM users WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid()))
    );


-- ============================================================================
-- FIM DA FASE 8
-- ============================================================================
